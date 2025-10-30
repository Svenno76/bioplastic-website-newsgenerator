#!/usr/bin/env python3
"""
Bioplastic News Fetcher
Fetches news from company websites using Perplexity API and tracks in Excel
"""

import os
import sys
import time
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlparse
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
        # Check if we have 3 or 4 columns (with or without Date Added)
        if len(df.columns) == 3:
            df.columns = ['Company', 'Type', 'Webpage']
            df['Date Added'] = ""  # Add empty column for backward compatibility
        elif len(df.columns) == 4:
            df.columns = ['Company', 'Type', 'Webpage', 'Date Added']
        else:
            # Assume at least first 3 columns are what we need
            df = df.iloc[:, :4] if len(df.columns) >= 4 else df.iloc[:, :3]
            if len(df.columns) == 3:
                df.columns = ['Company', 'Type', 'Webpage']
                df['Date Added'] = ""
            else:
                df.columns = ['Company', 'Type', 'Webpage', 'Date Added']
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
        return pd.DataFrame(columns=['Company', 'Week', 'News Detected', 'Category', 'Description', 'Company URL', 'Other URLs', 'Publishing Date'])

    try:
        df = pd.read_excel(file_path)
        # Add Publishing Date column if it doesn't exist (for backwards compatibility)
        if 'Publishing Date' not in df.columns:
            df['Publishing Date'] = ""
        # Add Category column if it doesn't exist (for backwards compatibility)
        if 'Category' not in df.columns:
            df['Category'] = ""
        # Migrate old URL column to new structure
        if 'URL' in df.columns and 'Company URL' not in df.columns:
            df['Company URL'] = ""
            df['Other URLs'] = df['URL']
            df = df.drop(columns=['URL'])
        # Add new URL columns if they don't exist
        if 'Company URL' not in df.columns:
            df['Company URL'] = ""
        if 'Other URLs' not in df.columns:
            df['Other URLs'] = ""
        return df
    except Exception as e:
        logging.error(f"Error reading existing news file: {e}")
        print(f"⚠️  Warning: Could not read existing news file, starting fresh")
        return pd.DataFrame(columns=['Company', 'Week', 'News Detected', 'Category', 'Description', 'Company URL', 'Other URLs', 'Publishing Date'])


def fuzzy_match_company(company_name, companies_list, threshold=0.85):
    """
    Fuzzy match a company name against a list of known companies
    Returns (matched_company_name, confidence_score) or (None, 0) if no match
    """
    best_match = None
    best_score = 0

    company_name_clean = company_name.strip().lower()

    for known_company in companies_list:
        known_clean = known_company.strip().lower()

        # Calculate similarity ratio
        ratio = SequenceMatcher(None, company_name_clean, known_clean).ratio()

        if ratio > best_score:
            best_score = ratio
            best_match = known_company

    if best_score >= threshold:
        return best_match, best_score
    return None, 0


def categorize_url_source(url, company_webpage):
    """
    Categorize URL as company website or other source
    Returns tuple: (company_url, other_url)
    """
    if not url:
        return "", ""

    try:
        url_domain = urlparse(url).netloc.lower().replace('www.', '')
        company_domain = company_webpage.lower().replace('www.', '').replace('http://', '').replace('https://', '')

        # Remove trailing slashes
        url_domain = url_domain.rstrip('/')
        company_domain = company_domain.rstrip('/')

        # Check if domains match
        if url_domain == company_domain or url_domain in company_domain or company_domain in url_domain:
            return url, ""
        else:
            return "", url
    except Exception as e:
        logging.warning(f"Error parsing URL {url}: {e}")
        return "", url


def create_company_batches(companies_df, batch_size=10):
    """
    Group companies by type and create batches of specified size
    Returns list of batch dictionaries with company info
    """
    batches = []

    # Group by company type
    for company_type in companies_df['Type'].unique():
        type_companies = companies_df[companies_df['Type'] == company_type]

        # Split into batches
        for i in range(0, len(type_companies), batch_size):
            batch = type_companies.iloc[i:i+batch_size]
            batches.append({
                'type': company_type,
                'companies': batch['Company'].tolist(),
                'webpages': dict(zip(batch['Company'], batch['Webpage'])),
                'batch_num': i // batch_size + 1,
                'total_in_type': len(type_companies)
            })

    return batches


def save_companies(companies_df, output_file):
    """Save companies DataFrame to Excel file"""
    try:
        companies_df.to_excel(output_file, index=False)
        logging.info(f"Companies file updated: {output_file}")
    except Exception as e:
        logging.error(f"Error saving companies file: {e}")
        print(f"❌ Error saving companies file: {e}")


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


def query_batch_news(batch_companies, target_week, companies_with_news=None):
    """
    Query Perplexity API for news about a batch of companies
    Returns list of news items as dictionaries
    """
    try:
        Config.validate()

        week_start, week_end = get_week_date_range(target_week)

        # Build company list for query
        company_list_str = ", ".join(batch_companies)

        # For follow-up queries, focus on companies without news
        if companies_with_news:
            missing_companies = [c for c in batch_companies if c not in companies_with_news]
            if not missing_companies:
                return []
            focus_text = f"\n\nIMPORTANT: Particularly search for news about these companies: {', '.join(missing_companies)}"
        else:
            focus_text = ""

        query = f"""
        Find bioplastic industry news published between {week_start.strftime('%B %d, %Y')} and {week_end.strftime('%B %d, %Y')}
        about these companies: {company_list_str}{focus_text}

        CRITICAL REQUIREMENTS:
        - ONLY include news if publication date is within the specified date range
        - Publication date must be confirmed from the source

        For each news item found, categorize into ONE of these categories:
        - Plant Announcement (plant openings, closures, revamps, maintenance, capacity changes)
        - People Moves (key decision makers joining or leaving)
        - M&A (mergers and acquisitions)
        - Litigation (court cases, arbitration, lawsuits)
        - Product Launch (new materials, grades, formulations, innovations)
        - Partnerships (collaborations, joint ventures, R&D agreements)
        - Financial Results (earnings, revenue reports, financial performance)
        - Supply Agreements (offtake agreements, contracts, customer wins)
        - Investment & Funding (capital raises, grants, government funding)
        - Certifications (regulatory approvals, certifications, compliance)

        Return results ONLY as a JSON array with this exact structure:
        [
          {{
            "date": "YYYY-MM-DD",
            "company": "Company Name",
            "category": "Category Name",
            "headline": "News Headline",
            "description": "50-word summary",
            "url": "https://..."
          }}
        ]

        If no news is found, return an empty array: []
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
                    "content": "You are a bioplastics industry news researcher. Provide factual information with exact URLs and dates. Return results as valid JSON only."
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
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                # Parse JSON response
                return parse_json_news_response(content, week_start, week_end)
            else:
                logging.error(f"Unexpected response structure for batch")
                return []

        elif response.status_code == 401:
            logging.error("Authentication failed - check API key")
            print("❌ Authentication failed. Please check your API key.")
            sys.exit(1)

        elif response.status_code == 429:
            logging.warning("Rate limit hit, waiting 30 seconds...")
            print("⚠️  Rate limit hit, waiting 30 seconds...")
            time.sleep(30)
            return query_batch_news(batch_companies, target_week, companies_with_news)

        else:
            logging.error(f"API Error {response.status_code}: {response.text}")
            return []

    except Exception as e:
        logging.error(f"Error querying batch: {e}")
        return []


def parse_json_news_response(content, week_start, week_end):
    """
    Parse JSON response from Perplexity
    Returns list of validated news items as dictionaries
    """
    from dateutil import parser as date_parser
    import re

    # Try to extract JSON from the response
    try:
        # Sometimes the response has markdown code blocks around JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find array brackets
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content

        news_items = json.loads(json_str)

        if not isinstance(news_items, list):
            logging.warning("Response is not a JSON array")
            return []

        validated_news = []

        for item in news_items:
            try:
                # Validate required fields
                if not all(key in item for key in ['date', 'company', 'category', 'description', 'url']):
                    logging.warning(f"Skipping incomplete news item: {item}")
                    continue

                # Parse and validate date
                try:
                    parsed_date = date_parser.parse(item['date'])
                    if not (week_start <= parsed_date.replace(tzinfo=None) <= week_end):
                        logging.warning(f"Date {item['date']} outside week range, skipping")
                        continue
                except Exception as e:
                    logging.warning(f"Could not parse date {item.get('date')}: {e}")
                    continue

                # Add to validated list
                validated_news.append({
                    'date': parsed_date.strftime('%Y-%m-%d'),
                    'company': item['company'].strip(),
                    'category': item['category'].strip(),
                    'headline': item.get('headline', '').strip(),
                    'description': item['description'].strip(),
                    'url': item['url'].strip()
                })

            except Exception as e:
                logging.warning(f"Error processing news item: {e}")
                continue

        return validated_news

    except json.JSONDecodeError as e:
        logging.error(f"JSON parse error: {e}")
        logging.error(f"Content: {content[:500]}")
        return []
    except Exception as e:
        logging.error(f"Error parsing response: {e}")
        return []


def deduplicate_news(news_list):
    """
    Deduplicate news items based on company + category + date
    Returns deduplicated list
    """
    seen = set()
    deduplicated = []

    for item in news_list:
        # Create unique key
        key = (
            item['company'].lower().strip(),
            item['category'].lower().strip(),
            item['date']
        )

        if key not in seen:
            seen.add(key)
            deduplicated.append(item)
        else:
            logging.info(f"Duplicate found: {item['company']} - {item['category']} - {item['date']}")

    return deduplicated


def process_news_with_fuzzy_matching(news_list, companies_df, companies_file):
    """
    Process news items with fuzzy matching and auto-discovery
    Returns tuple: (processed_news_list, updated_companies_df, new_companies_count)
    """
    processed_news = []
    known_companies = companies_df['Company'].tolist()
    new_companies_found = []
    today = datetime.now().strftime('%Y-%m-%d')

    for item in news_list:
        # Try to fuzzy match company name
        matched_company, confidence = fuzzy_match_company(item['company'], known_companies)

        if matched_company:
            # Use the matched company name
            item['company'] = matched_company
            logging.info(f"Fuzzy matched '{item['company']}' to '{matched_company}' (confidence: {confidence:.2f})")
        else:
            # New company discovered
            logging.info(f"New company discovered: {item['company']}")
            print(f"   🆕 New company discovered: {item['company']}")

            # Try to guess company type from context
            guessed_type = guess_company_type(item.get('description', ''))

            # Add to new companies list
            new_companies_found.append({
                'Company': item['company'],
                'Type': guessed_type,
                'Webpage': '',  # Will need to be filled manually
                'Date Added': today
            })

            # Add to known companies list for future matches in this session
            known_companies.append(item['company'])

        processed_news.append(item)

    # Add new companies to DataFrame
    if new_companies_found:
        new_df = pd.DataFrame(new_companies_found)
        companies_df = pd.concat([companies_df, new_df], ignore_index=True)
        # Save updated companies file
        save_companies(companies_df, companies_file)
        print(f"\n✨ Added {len(new_companies_found)} new companies to database")

    return processed_news, companies_df, len(new_companies_found)


def guess_company_type(description):
    """
    Guess company type based on description content
    Returns one of: producer, converter, compounder, equipment, additive
    """
    desc_lower = description.lower()

    # Keywords for each type
    if any(word in desc_lower for word in ['produce', 'production', 'manufacturer', 'manufacturing', 'pla', 'pha', 'biopolymer']):
        return 'producer'
    elif any(word in desc_lower for word in ['convert', 'packaging', 'film', 'bottle', 'container']):
        return 'converter'
    elif any(word in desc_lower for word in ['compound', 'formulation', 'blend', 'masterbatch']):
        return 'compounder'
    elif any(word in desc_lower for word in ['equipment', 'machinery', 'technology provider', 'system', 'extruder']):
        return 'equipment'
    elif any(word in desc_lower for word in ['additive', 'stabilizer', 'plasticizer', 'nucleating agent']):
        return 'additive'
    else:
        return 'producer'  # Default guess


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
    print("🌱 BIOPLASTIC NEWS FETCHER REV1")
    print("=" * 70)

    # Read companies
    print("\n📂 Reading companies file...")
    companies_df = read_companies(INPUT_FILE)
    print(f"✓ Found {len(companies_df)} companies")

    # Read existing news
    print("\n📂 Reading existing news file...")
    news_df = read_existing_news(OUTPUT_FILE)
    print(f"✓ Found {len(news_df)} existing news entries")

    # Ask how many weeks to process backward
    # Check for command-line arguments
    if len(sys.argv) > 1:
        try:
            num_weeks = int(sys.argv[1])
            if not (1 <= num_weeks <= 10):
                print(f"⚠️  Weeks must be between 1 and 10, defaulting to 1")
                num_weeks = 1
        except ValueError:
            print(f"⚠️  Invalid weeks argument, defaulting to 1")
            num_weeks = 1
    else:
        while True:
            try:
                num_weeks = input(f"\n📅 How many weeks to process? (1-10, default: 1): ")
                if num_weeks == "":
                    num_weeks = 1
                    break
                num_weeks = int(num_weeks)
                if 1 <= num_weeks <= 10:
                    break
                print(f"⚠️  Please enter a number between 1 and 10")
            except (ValueError, EOFError):
                print("⚠️  Defaulting to 1 week")
                num_weeks = 1
                break

    # Process each week
    weeks_processed = []

    for week_num in range(num_weeks):
        # Determine target week for this iteration
        target_week = determine_target_week(companies_df, news_df)

        if week_num > 0:
            print("\n" + "=" * 70)
            print(f"📅 PROCESSING WEEK {week_num + 1} OF {num_weeks}")
            print("=" * 70)

        print(f"\n🎯 Target week for processing: {target_week}")

        week_start, week_end = get_week_date_range(target_week)
        print(f"   Date range: {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}")

        # Create batches of 10 companies grouped by type
        batches = create_company_batches(companies_df, batch_size=10)
        print(f"\n📦 Created {len(batches)} batches of companies")

        # Ask user how many batches to process (only on first week)
        if week_num == 0:
            # Check for command-line argument
            if len(sys.argv) > 2:
                if sys.argv[2].lower() == 'all':
                    max_batches = len(batches)
                else:
                    try:
                        max_batches = int(sys.argv[2])
                        if not (1 <= max_batches <= len(batches)):
                            print(f"⚠️  Batches must be between 1 and {len(batches)}, using 2 for testing")
                            max_batches = 2
                    except ValueError:
                        print(f"⚠️  Invalid batches argument, using 2 for testing")
                        max_batches = 2
            else:
                while True:
                    try:
                        max_batches_input = input(f"\n🔢 How many batches to process per week? (1-{len(batches)}, or 'all'): ")
                        if max_batches_input.lower() == 'all':
                            max_batches = len(batches)
                            break
                        max_batches = int(max_batches_input)
                        if 1 <= max_batches <= len(batches):
                            break
                        print(f"⚠️  Please enter a number between 1 and {len(batches)}")
                    except (ValueError, EOFError):
                        print("⚠️  Defaulting to 2 batches for testing")
                        max_batches = 2
                        break

        batches_to_process = batches[:max_batches]

        print(f"\n🔍 Processing {len(batches_to_process)} batches for week {target_week}...")
        print("=" * 70)

        # Collect all news from all batches
        all_news = []
        total_api_calls = 0

        for batch_idx, batch in enumerate(batches_to_process, 1):
            print(f"\n[Batch {batch_idx}/{len(batches_to_process)}] 📦 Type: {batch['type']}")
            print(f"   Companies: {', '.join(batch['companies'][:3])}{'...' if len(batch['companies']) > 3 else ''}")
            print(f"   Total in batch: {len(batch['companies'])}")

            # Stage 1: Initial query
            print(f"\n   🔍 Stage 1: Initial search...")
            news_items = query_batch_news(batch['companies'], target_week)
            total_api_calls += 1

            companies_with_news = set([item['company'] for item in news_items])
            print(f"   ✓ Found {len(news_items)} news items for {len(companies_with_news)} companies")

            all_news.extend(news_items)

            # Stage 2: Complement query #1
            if len(companies_with_news) < len(batch['companies']):
                print(f"\n   🔍 Stage 2: Searching for missing companies...")
                time.sleep(5)  # Rate limiting
                complement_news = query_batch_news(batch['companies'], target_week, companies_with_news)
                total_api_calls += 1

                new_items = [item for item in complement_news if item['company'] not in companies_with_news]
                companies_with_news.update([item['company'] for item in new_items])
                print(f"   ✓ Found {len(new_items)} additional news items")

                all_news.extend(new_items)

            # Stage 3: Complement query #2
            if len(companies_with_news) < len(batch['companies']):
                print(f"\n   🔍 Stage 3: Final search for remaining companies...")
                time.sleep(5)  # Rate limiting
                final_news = query_batch_news(batch['companies'], target_week, companies_with_news)
                total_api_calls += 1

                new_items = [item for item in final_news if item['company'] not in companies_with_news]
                print(f"   ✓ Found {len(new_items)} additional news items")

                all_news.extend(new_items)

            # Rate limiting between batches
            if batch_idx < len(batches_to_process):
                print(f"\n   ⏳ Waiting 5 seconds before next batch...")
                time.sleep(5)

        print("\n" + "=" * 70)
        print(f"📊 PROCESSING NEWS ITEMS FOR WEEK {target_week}")
        print("=" * 70)

        # Deduplicate news
        print(f"\n🔍 Total news items collected: {len(all_news)}")
        all_news = deduplicate_news(all_news)
        print(f"✓ After deduplication: {len(all_news)} unique items")

        # Process with fuzzy matching and auto-discovery
        print(f"\n🔍 Processing with fuzzy matching...")
        all_news, companies_df, new_companies = process_news_with_fuzzy_matching(
            all_news, companies_df, INPUT_FILE
        )

        # Convert to DataFrame format for output
        results = []
        for item in all_news:
            # Categorize URL source
            company_webpage = ""
            company_row = companies_df[companies_df['Company'] == item['company']]
            if len(company_row) > 0:
                company_webpage = company_row.iloc[0]['Webpage']

            company_url, other_url = categorize_url_source(item['url'], company_webpage)

            results.append({
                'Company': item['company'],
                'Week': target_week,
                'News Detected': 'YES',
                'Category': item['category'],
                'Description': item['description'],
                'Company URL': company_url,
                'Other URLs': other_url,
                'Publishing Date': item['date']
            })

        # Add "NO" entries for companies without news
        companies_with_news_set = set([r['Company'] for r in results])
        for batch in batches_to_process:
            for company in batch['companies']:
                if company not in companies_with_news_set:
                    results.append({
                        'Company': company,
                        'Week': target_week,
                        'News Detected': 'NO',
                        'Category': '',
                        'Description': '',
                        'Company URL': '',
                        'Other URLs': '',
                        'Publishing Date': ''
                    })

        # Save results
        results_df = pd.DataFrame(results)
        news_df = pd.concat([news_df, results_df], ignore_index=True)
        save_results(news_df, OUTPUT_FILE)

        # Track week statistics
        week_stats = {
            'week': target_week,
            'batches': len(batches_to_process),
            'companies': sum(len(b['companies']) for b in batches_to_process),
            'api_calls': total_api_calls,
            'news_found': sum(1 for r in results if r['News Detected'] == 'YES'),
            'no_news': sum(1 for r in results if r['News Detected'] == 'NO'),
            'new_companies': new_companies
        }
        weeks_processed.append(week_stats)

        print(f"\n✅ Week {target_week} complete!")
        print(f"   API calls: {total_api_calls}")
        print(f"   News found: {week_stats['news_found']}")
        print(f"   No news: {week_stats['no_news']}")

    # Final summary
    print("\n" + "=" * 70)
    print("✅ ALL PROCESSING COMPLETE!")
    print("=" * 70)
    print(f"\n📊 Overall Summary:")
    print(f"   Weeks processed: {len(weeks_processed)}")
    print(f"   Total API calls: {sum(w['api_calls'] for w in weeks_processed)}")
    print(f"   Total news found: {sum(w['news_found'] for w in weeks_processed)}")
    print(f"   Total new companies: {sum(w['new_companies'] for w in weeks_processed)}")

    print(f"\n📅 Week-by-week breakdown:")
    for w in weeks_processed:
        print(f"   {w['week']}: {w['news_found']} news, {w['api_calls']} API calls")

    print(f"\n💾 Output file: {OUTPUT_FILE}")
    print(f"📋 Companies file: {INPUT_FILE}")
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
