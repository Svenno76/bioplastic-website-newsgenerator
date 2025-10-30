#!/usr/bin/env python3
"""
Bioplastic News Fetcher Rev2
Fetches general bioplastic news and matches companies with fuzzy matching
"""

import sys
import os
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
import pandas as pd
from fuzzywuzzy import fuzz

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bioplastic_news_errors.log'),
        logging.StreamHandler()
    ]
)

def get_iso_week(date_str):
    """Convert date string to ISO week format (e.g., '2025-W43')"""
    try:
        date_obj = pd.to_datetime(date_str)
        iso_year, iso_week, _ = date_obj.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    except Exception as e:
        logging.error(f"Error converting date {date_str} to ISO week: {e}")
        return None

def fuzzy_match_company(company_name, known_companies, threshold=85):
    """
    Fuzzy match a company name against a list of known companies
    Returns (matched_name, score) or (None, 0) if no match above threshold
    """
    best_match = None
    best_score = 0

    for known_company in known_companies:
        score = fuzz.ratio(company_name.lower(), known_company.lower())
        if score > best_score:
            best_score = score
            best_match = known_company

    if best_score >= threshold:
        return best_match, best_score
    return None, best_score

def fetch_bioplastic_news(days=7, max_items=10, exclude_urls=None):
    """
    Fetch general bioplastic news from the last N days from company websites
    Returns JSON array with: Company, Publishing Date, Headline, Description, Category, Source URL
    """
    try:
        Config.validate()

        # Calculate date range
        today = datetime.now()
        start_date = today - timedelta(days=days)

        print(f"\n🔍 Fetching bioplastic news from {start_date.strftime('%B %d')} to {today.strftime('%B %d, %Y')}...")

        # Build URL exclusion text
        url_exclusion_text = ""
        if exclude_urls and len(exclude_urls) > 0:
            print(f"  ℹ️  Excluding {len(exclude_urls)} URLs from this week's existing news")
            url_list = "\n        ".join([f"- {url}" for url in exclude_urls])
            url_exclusion_text = f"""
        EXCLUDE news from these URLs (already covered this week):
        {url_list}
        """

        # Construct the query
        query = f"""
        Find the most recent bioplastic and biopolymer industry news from ACTUAL COMPANIES
        published between {start_date.strftime('%B %d, %Y')} and {today.strftime('%B %d, %Y')}.
        {url_exclusion_text}

        CRITICAL REQUIREMENTS:
        - ONLY search company websites, press release pages, and official company announcements
        - PRIORITIZE news directly from company websites (not third-party news sites)
        - Publication date MUST be within the specified date range
        - ONLY include actual companies (producers, converters, compounders, equipment manufacturers)
        - EXCLUDE: market reports, industry associations, news publications, analyst firms, research companies

        Search for these types of news ONLY:
        1. Plant Announcement - plant openings, closures, revamps, maintenance, capacity changes
        2. People Moves - key decision makers joining or leaving
        3. M&A - mergers and acquisitions
        4. Litigation - court cases, arbitration, lawsuits
        5. Product Launch - new materials, grades, formulations, innovations
        6. Partnerships - collaborations, joint ventures, R&D agreements
        7. Financial Results - earnings, revenue reports, financial performance
        8. Supply Agreements - offtake agreements, contracts, customer wins
        9. Investment & Funding - capital raises, grants, government funding
        10. Certifications - regulatory approvals, certifications, compliance

        Return EXACTLY {max_items} news items in valid JSON format as an array with these fields:
        - Company: The ACTUAL COMPANY name (not "Market", not "Industry", not news sites)
        - PublishingDate: The exact date in YYYY-MM-DD format (must be within date range)
        - Headline: A concise headline (max 100 characters)
        - Description: A 50-word summary of the news
        - Category: ONE of the 10 categories listed above (exact category name)
        - SourceURL: The URL from the company website or press release

        Example format:
        [
          {{
            "Company": "NatureWorks",
            "PublishingDate": "2025-10-25",
            "Headline": "NatureWorks expands Ingeo PLA production capacity",
            "Description": "NatureWorks announced a significant expansion of its Ingeo PLA biopolymer production capacity at its Blair facility, adding 50,000 tons annual capacity to meet growing demand for sustainable packaging materials.",
            "Category": "Plant Announcement",
            "SourceURL": "https://www.natureworksllc.com/news/press-releases/..."
          }}
        ]

        IMPORTANT: Return ONLY the JSON array with no markdown formatting, no explanatory text.
        """

        # Make API call
        headers = {
            "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": Config.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a bioplastic industry news aggregator. Return only valid JSON arrays without any markdown formatting or additional text."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": Config.MAX_TOKENS,
            "temperature": 0.2,
            "return_citations": True,
            "stream": False
        }

        print(f"📡 Calling Perplexity API...")
        response = requests.post(
            Config.PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']

            print(f"✓ API call successful")
            print(f"\n📄 Raw response:\n{content}\n")

            # Try to parse JSON from the response
            # Remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            try:
                news_items = json.loads(content)
                print(f"✓ Successfully parsed {len(news_items)} news items")
                return news_items
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                logging.error(f"Content: {content}")
                return []
        else:
            error_msg = response.text
            logging.error(f"API Error {response.status_code}: {error_msg}")
            return []

    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []

def validate_news_item(item, start_date, end_date):
    """
    Validate a news item for quality and date range
    Returns: (is_valid, reason)
    """
    # List of invalid company patterns (non-companies)
    invalid_patterns = [
        'market', 'industry', 'report', 'insights', 'analysis', 'news',
        'publication', 'association', 'plastics industry', 'biopolymers market',
        'research', 'study', 'survey', 'forecast', 'outlook'
    ]

    company_name = item.get('Company', '').lower()

    # Check if it's a non-company entity
    for pattern in invalid_patterns:
        if pattern in company_name:
            return False, f"Not a company (contains '{pattern}')"

    # Validate date
    try:
        pub_date = pd.to_datetime(item.get('PublishingDate', ''))
        if pub_date < start_date or pub_date > end_date:
            return False, f"Date {pub_date.date()} outside range"
    except:
        return False, "Invalid date format"

    # Validate required fields
    required_fields = ['Company', 'PublishingDate', 'Headline', 'Description', 'Category', 'SourceURL']
    for field in required_fields:
        if not item.get(field):
            return False, f"Missing required field: {field}"

    # Validate category
    valid_categories = [
        'Plant Announcement', 'People Moves', 'M&A', 'Litigation',
        'Product Launch', 'Partnerships', 'Financial Results',
        'Supply Agreements', 'Investment & Funding', 'Certifications'
    ]
    if item.get('Category') not in valid_categories:
        return False, f"Invalid category: {item.get('Category')}"

    return True, "Valid"

def process_news_items(news_items, companies_df, start_date, end_date):
    """
    Process news items: validate, fuzzy match companies, add new companies if needed
    Returns: processed_items (list of dicts), updated_companies_df
    """
    processed_items = []
    known_companies = companies_df['Company'].tolist()
    new_companies = []

    print(f"\n🔍 Processing {len(news_items)} news items...")

    for item in news_items:
        # Validate news item
        is_valid, reason = validate_news_item(item, start_date, end_date)
        if not is_valid:
            print(f"  ⚠️  Skipping '{item.get('Company', 'Unknown')}': {reason}")
            continue
        company_name = item.get('Company', '')

        # Fuzzy match against known companies
        matched_company, score = fuzzy_match_company(company_name, known_companies)

        if matched_company:
            print(f"  ✓ Matched '{company_name}' to '{matched_company}' (score: {score})")
        else:
            print(f"  🆕 New company found: '{company_name}' (best score: {score})")
            if company_name not in new_companies:
                new_companies.append(company_name)
                # Add to known companies list for subsequent fuzzy matching
                known_companies.append(company_name)

        # Categorize URLs
        source_url = item.get('SourceURL', '')
        company_url = ''
        other_url = ''

        if matched_company:
            # Check if URL matches company webpage
            company_webpage = companies_df[companies_df['Company'] == matched_company]['Webpage'].values
            if len(company_webpage) > 0 and pd.notna(company_webpage[0]) and company_webpage[0]:
                webpage_domain = str(company_webpage[0]).replace('www.', '').lower()
                if webpage_domain in source_url.lower():
                    company_url = source_url
                else:
                    other_url = source_url
            else:
                other_url = source_url
        else:
            other_url = source_url

        # Calculate ISO week
        publishing_date = item.get('PublishingDate', '')
        iso_week = get_iso_week(publishing_date)

        processed_item = {
            'Company': company_name,
            'Company matched': matched_company if matched_company else '',
            'Publishing Date': publishing_date,
            'Headline': item.get('Headline', ''),
            'Description': item.get('Description', ''),
            'Category': item.get('Category', ''),
            'Source URL (company)': company_url,
            'Source URL (other)': other_url,
            'Week': iso_week
        }

        processed_items.append(processed_item)

    # Add new companies to companies DataFrame
    if new_companies:
        print(f"\n🆕 Adding {len(new_companies)} new companies to companies.xlsx:")
        for company in new_companies:
            print(f"  - {company}")
            new_row = pd.DataFrame({
                'Company': [company],
                'Type': [''],
                'Webpage': [''],
                'Description': ['']
            })
            companies_df = pd.concat([companies_df, new_row], ignore_index=True)

    return processed_items, companies_df

def save_results(processed_items, companies_df, output_file='companies_news.xlsx', companies_file='companies.xlsx'):
    """
    Save processed news items to companies_news.xlsx and updated companies to companies.xlsx
    """
    print(f"\n💾 Saving results...")

    # Save companies (including any new ones)
    companies_df.to_excel(companies_file, index=False)
    print(f"  ✓ Updated {companies_file}")

    # Create new DataFrame with the new structure
    news_df = pd.DataFrame(processed_items)

    # Append to existing companies_news.xlsx if it exists
    if os.path.exists(output_file):
        try:
            existing_df = pd.read_excel(output_file)

            # Deduplicate by URL before appending
            existing_urls = set()
            existing_urls.update(existing_df['Source URL (company)'].dropna().tolist())
            existing_urls.update(existing_df['Source URL (other)'].dropna().tolist())

            # Filter out duplicates from new items
            original_count = len(news_df)
            news_df_filtered = news_df[
                ~(news_df['Source URL (company)'].isin(existing_urls) |
                  news_df['Source URL (other)'].isin(existing_urls))
            ]
            duplicates_removed = original_count - len(news_df_filtered)

            if duplicates_removed > 0:
                print(f"  ℹ️  Removed {duplicates_removed} duplicate(s) by URL")

            # Combine existing and deduplicated new data
            combined_df = pd.concat([existing_df, news_df_filtered], ignore_index=True)
            combined_df.to_excel(output_file, index=False)
            print(f"  ✓ Appended {len(news_df_filtered)} news items to {output_file} (total: {len(combined_df)})")
        except Exception as e:
            logging.error(f"Error appending to existing file: {e}")
            news_df.to_excel(output_file, index=False)
            print(f"  ✓ Saved {len(processed_items)} news items to {output_file} (new file)")
    else:
        news_df.to_excel(output_file, index=False)
        print(f"  ✓ Saved {len(processed_items)} news items to {output_file} (new file)")

    return True

def main():
    """Main execution function"""
    try:
        print("=" * 70)
        print("🌱 BIOPLASTIC NEWS FETCHER REV2")
        print("=" * 70)

        # Determine paths (works from both project root and skill directory)
        if os.path.exists('companies.xlsx'):
            companies_file = 'companies.xlsx'
            news_file = 'companies_news.xlsx'
        else:
            # Running from skill directory, go up to project root
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            companies_file = project_root / 'companies.xlsx'
            news_file = project_root / 'companies_news.xlsx'

        # Load companies
        print("\n📂 Loading companies file...")
        companies_df = pd.read_excel(companies_file)
        print(f"  ✓ Loaded {len(companies_df)} companies")

        # Define date range for validation
        days = 7
        today = datetime.now()
        start_date = today - timedelta(days=days)
        current_iso_week = get_iso_week(today.strftime('%Y-%m-%d'))

        # Load existing news and get URLs from current week
        exclude_urls = []
        if os.path.exists(news_file):
            try:
                existing_news_df = pd.read_excel(news_file)
                # Filter for current week
                current_week_news = existing_news_df[existing_news_df['Week'] == current_iso_week]
                # Collect all URLs from both URL columns
                urls_company = current_week_news['Source URL (company)'].dropna().tolist()
                urls_other = current_week_news['Source URL (other)'].dropna().tolist()
                exclude_urls = list(set(urls_company + urls_other))  # Remove duplicates
                print(f"📋 Found {len(current_week_news)} existing news items for week {current_iso_week}")
            except Exception as e:
                logging.warning(f"Could not load existing news for URL exclusion: {e}")

        # Fetch news
        news_items = fetch_bioplastic_news(days=days, max_items=10, exclude_urls=exclude_urls)

        if not news_items:
            print("\n⚠️  No news items found or API error occurred")
            return

        # Process news items with date validation
        processed_items, updated_companies_df = process_news_items(
            news_items, companies_df, start_date, today
        )

        # Save results
        save_results(processed_items, updated_companies_df,
                    output_file=str(news_file), companies_file=str(companies_file))

        # Summary with category breakdown
        print("\n" + "=" * 70)
        print("✅ REV2 PROCESSING COMPLETE!")
        print("=" * 70)
        print(f"  Valid news items: {len(processed_items)}")
        print(f"  New companies discovered: {len(updated_companies_df) - len(companies_df)}")
        print(f"  Total companies in database: {len(updated_companies_df)}")

        if processed_items:
            print("\n📊 Category breakdown:")
            categories = {}
            for item in processed_items:
                cat = item.get('Category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            for cat, count in sorted(categories.items()):
                print(f"     {cat}: {count}")

        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        logging.info("Process interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
