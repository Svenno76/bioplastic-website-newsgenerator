#!/usr/bin/env python3
"""
Bioplastic News Fetcher
Fetches news from company websites using Perplexity API and tracks in Excel
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd

# Setup paths
PROJECT_ROOT = Path('/home/sven/bioplastic-website-newsgenerator')

# Add project root to Python path to import config
sys.path.insert(0, str(PROJECT_ROOT))
from config import Config
INPUT_FILE = PROJECT_ROOT / 'companies.xlsx'
OUTPUT_FILE = PROJECT_ROOT / 'companies_news.xlsx'
LOG_FILE = PROJECT_ROOT / 'bioplastic_news_errors.log'

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_iso_week(date=None):
    """Get ISO week string (e.g., '2025-W42')"""
    if date is None:
        date = datetime.now()
    iso_calendar = date.isocalendar()
    return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"


def get_week_date_range(iso_week):
    """Get start and end dates for an ISO week"""
    year, week = iso_week.split('-W')
    year = int(year)
    week = int(week)

    # Get first day of the week (Monday)
    jan_4 = datetime(year, 1, 4)
    week_start = jan_4 - timedelta(days=jan_4.weekday()) + timedelta(weeks=week-1)
    week_end = week_start + timedelta(days=6)

    return week_start, week_end


def previous_week(iso_week):
    """Get the previous ISO week"""
    week_start, _ = get_week_date_range(iso_week)
    prev_week_date = week_start - timedelta(days=7)
    return get_iso_week(prev_week_date)


def read_companies(file_path):
    """Read companies from Excel file"""
    try:
        df = pd.read_excel(file_path)
        # Rename columns to standard names
        df.columns = ['Company', 'Type', 'Webpage']
        return df
    except FileNotFoundError:
        logging.error(f"Input file not found: {file_path}")
        print(f"❌ Error: Input file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading companies file: {e}")
        print(f"❌ Error reading companies file: {e}")
        sys.exit(1)


def read_existing_news(file_path):
    """Read existing news from Excel file"""
    if not file_path.exists():
        # Create empty DataFrame with correct columns
        return pd.DataFrame(columns=['Company', 'Week', 'News Detected', 'Description', 'URL', 'Publishing Date'])

    try:
        df = pd.read_excel(file_path)
        # Add Publishing Date column if it doesn't exist (for backwards compatibility)
        if 'Publishing Date' not in df.columns:
            df['Publishing Date'] = ""
        return df
    except Exception as e:
        logging.error(f"Error reading existing news file: {e}")
        print(f"⚠️  Warning: Could not read existing news file, starting fresh")
        return pd.DataFrame(columns=['Company', 'Week', 'News Detected', 'Description', 'URL', 'Publishing Date'])


def determine_target_week(companies_df, news_df):
    """Determine which week to process based on existing data"""
    current_week = get_iso_week()
    week_to_check = current_week

    print(f"\n📅 Current week: {current_week}")

    while True:
        # Get news for this week
        week_news = news_df[news_df['Week'] == week_to_check].copy()
        all_companies = set(companies_df['Company'].unique())

        # Companies with valid results (YES or NO, not NaN or ERROR)
        valid_results = week_news[week_news['News Detected'].isin(['YES', 'NO'])]
        companies_with_valid_results = set(valid_results['Company'].unique())

        # Check if all companies have valid results
        missing_or_invalid = all_companies - companies_with_valid_results

        if len(missing_or_invalid) > 0:
            print(f"✓ Week {week_to_check}: {len(missing_or_invalid)} companies need processing")
            return week_to_check

        # All companies have valid results (YES or NO)
        # Move to previous week since all companies have been queried
        print(f"✓ Week {week_to_check}: All companies processed, going back...")
        week_to_check = previous_week(week_to_check)
        continue


def query_perplexity(company_name, company_type, webpage, target_week):
    """Query Perplexity API for company news"""
    try:
        Config.validate()

        week_start, week_end = get_week_date_range(target_week)

        # Construct query with site operator
        query = f"""
        Search site:{webpage} ONLY for bioplastic-related news, press releases, or announcements
        published between {week_start.strftime('%B %d, %Y')} and {week_end.strftime('%B %d, %Y')}.

        Company: {company_name}
        Type: {company_type}

        CRITICAL REQUIREMENTS:
        - ONLY include news if you can CONFIRM the publication date is within the specified date range
        - If the publication date is OUTSIDE this range or UNCERTAIN, respond with "NO NEWS FOUND"
        - The publication date must be explicitly stated on the source webpage

        If news IS found within the exact date range:
        1. STATE THE EXACT PUBLICATION DATE (format: YYYY-MM-DD or Month DD, YYYY)
        2. Provide a 50-word summary of the news
        3. Include the exact URL of the news article/press release

        If no news is published in this specific week, state "NO NEWS FOUND".
        """

        headers = {
            "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": Config.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a bioplastics industry news researcher. Search only the specified company website. Provide factual information with exact URLs and dates. If no news is found, clearly state it."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": Config.MAX_TOKENS,
            "temperature": Config.TEMPERATURE,
            "return_citations": True,
            "stream": False
        }

        response = requests.post(
            Config.PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']

                # Parse the response
                return parse_perplexity_response(content, week_start, week_end)
            else:
                logging.error(f"Unexpected response structure for {company_name}")
                return None, None, None, None

        elif response.status_code == 401:
            logging.error("Authentication failed - check API key")
            print("❌ Authentication failed. Please check your API key.")
            sys.exit(1)

        elif response.status_code == 429:
            logging.warning("Rate limit hit, waiting 30 seconds...")
            print("⚠️  Rate limit hit, waiting 30 seconds...")
            time.sleep(30)
            return query_perplexity(company_name, company_type, webpage, target_week)

        else:
            logging.error(f"API Error {response.status_code} for {company_name}: {response.text}")
            return None, None, None, None

    except Exception as e:
        logging.error(f"Error querying {company_name}: {e}")
        return None, None, None, None


def parse_perplexity_response(content, week_start, week_end):
    """Parse Perplexity response to extract news info and validate date"""
    import re
    from dateutil import parser as date_parser

    content_upper = content.upper()

    # Check if no news found
    if "NO NEWS FOUND" in content_upper or "NO RELEVANT" in content_upper:
        return "NO", "", "", ""

    # Try to extract URL
    url = ""
    lines = content.split('\n')
    for line in lines:
        if 'http' in line.lower():
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
            if urls:
                url = urls[0]
                break

    # Try to extract publication date
    pub_date = ""
    date_found = False

    # Look for common date patterns
    date_patterns = [
        r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
        r'\b([A-Z][a-z]+ \d{1,2},? \d{4})\b',  # Month DD, YYYY or Month DD YYYY
        r'\b(\d{1,2} [A-Z][a-z]+ \d{4})\b',  # DD Month YYYY
        r'\b([A-Z][a-z]+ \d{1,2}th?,? \d{4})\b',  # Month DDth, YYYY
    ]

    for line in lines[:10]:  # Check first 10 lines for dates
        for pattern in date_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                try:
                    # Try to parse the date
                    parsed_date = date_parser.parse(matches[0], fuzzy=False)

                    # Validate the date is within the week range
                    if week_start <= parsed_date.replace(tzinfo=None) <= week_end:
                        pub_date = parsed_date.strftime('%Y-%m-%d')
                        date_found = True
                        break
                    else:
                        # Date is outside the range - reject this news
                        logging.warning(f"Date {parsed_date.strftime('%Y-%m-%d')} outside range {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
                        return "NO", "", "", ""
                except (ValueError, TypeError):
                    continue
        if date_found:
            break

    # If we have a URL but no valid date, reject it
    if url and not date_found:
        logging.warning(f"URL found but no valid date within range: {url}")
        return "NO", "", "", ""

    # Generate 50-word summary from the content
    summary_lines = [line for line in lines if 'http' not in line.lower() and line.strip()]
    summary = ' '.join(summary_lines).strip()

    # Truncate to approximately 50 words
    words = summary.split()
    if len(words) > 50:
        summary = ' '.join(words[:50]) + "..."

    news_detected = "YES" if (url and date_found) else "NO"

    return news_detected, summary, url, pub_date


def save_results(news_df, output_file):
    """Save results to Excel file"""
    try:
        news_df.to_excel(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        logging.error(f"Error saving results: {e}")
        print(f"❌ Error saving results: {e}")


def main():
    """Main execution function"""
    print("=" * 70)
    print("🌱 BIOPLASTIC NEWS FETCHER")
    print("=" * 70)

    # Read companies
    print("\n📂 Reading companies file...")
    companies_df = read_companies(INPUT_FILE)
    print(f"✓ Found {len(companies_df)} companies")

    # Read existing news
    print("\n📂 Reading existing news file...")
    news_df = read_existing_news(OUTPUT_FILE)
    print(f"✓ Found {len(news_df)} existing news entries")

    # Determine target week
    target_week = determine_target_week(companies_df, news_df)
    print(f"\n🎯 Target week for processing: {target_week}")

    week_start, week_end = get_week_date_range(target_week)
    print(f"   Date range: {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}")

    # Get companies that need processing for this week
    # Include companies with no entry OR with NaN/ERROR in "News Detected"
    week_news = news_df[news_df['Week'] == target_week].copy()

    # Companies with valid results (YES or NO)
    valid_results = week_news[week_news['News Detected'].isin(['YES', 'NO'])]['Company'].unique()

    # Companies that need processing: not in valid_results
    companies_to_process = companies_df[~companies_df['Company'].isin(valid_results)]

    if len(companies_to_process) == 0:
        print("\n✓ All companies already processed for this week!")
        return

    print(f"\n📋 Companies to process: {len(companies_to_process)}")

    # Ask user how many to process
    while True:
        try:
            max_count = input(f"\n🔢 How many companies to process? (max {len(companies_to_process)}): ")
            max_count = int(max_count)
            if 1 <= max_count <= len(companies_to_process):
                break
            print(f"⚠️  Please enter a number between 1 and {len(companies_to_process)}")
        except ValueError:
            print("⚠️  Please enter a valid number")

    companies_to_process = companies_to_process.head(max_count)

    print(f"\n🔍 Processing {len(companies_to_process)} companies...")
    print("=" * 70)

    # Process each company
    results = []
    for idx, row in companies_to_process.iterrows():
        company = row['Company']
        company_type = row['Type']
        webpage = row['Webpage']

        print(f"\n[{idx+1}/{len(companies_to_process)}] 🏭 {company} ({company_type})")
        print(f"    Website: {webpage}")

        # Query Perplexity
        news_detected, description, url, pub_date = query_perplexity(company, company_type, webpage, target_week)

        if news_detected is None:
            print("    ❌ Error querying API (logged)")
            news_detected = "ERROR"
            description = ""
            url = ""
            pub_date = ""
        elif news_detected == "YES":
            print(f"    ✓ News found!")
            print(f"    📅 Published: {pub_date}")
            print(f"    📰 {description[:60]}...")
        else:
            print("    ○ No news found")

        # Add to results
        results.append({
            'Company': company,
            'Week': target_week,
            'News Detected': news_detected,
            'Description': description,
            'URL': url,
            'Publishing Date': pub_date
        })

        # Save after each company (in case of interruption)
        results_df = pd.DataFrame(results)
        updated_news_df = pd.concat([news_df, results_df], ignore_index=True)
        save_results(updated_news_df, OUTPUT_FILE)

        # Rate limiting delay
        if idx < len(companies_to_process) - 1:  # Don't wait after last one
            print("    ⏳ Waiting 5 seconds...")
            time.sleep(5)

    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   Companies processed: {len(results)}")
    print(f"   News found: {sum(1 for r in results if r['News Detected'] == 'YES')}")
    print(f"   No news: {sum(1 for r in results if r['News Detected'] == 'NO')}")
    print(f"   Errors: {sum(1 for r in results if r['News Detected'] == 'ERROR')}")
    print(f"\n💾 Output file: {OUTPUT_FILE}")
    print(f"📋 Log file: {LOG_FILE}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
