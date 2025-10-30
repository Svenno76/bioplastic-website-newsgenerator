---
name: bioplastic-news-fetcher
description: Automatically fetches bioplastic news from company websites using Perplexity API. Reads companies from companies.xlsx, searches their websites for news in specific weeks, and outputs results to companies_news.xlsx with news detection flags, descriptions, and URLs. Intelligently processes current week or backtracks to find weeks that need processing.
---

# Bioplastic News Fetcher Skill

This skill automates the process of fetching bioplastic-related news from company websites using the Perplexity API.

## How It Works

1. **Read Input**: Loads `companies.xlsx` from `/home/sven/bioplastic-website-newsgenerator/`
   - Column A: Company name
   - Column B: Company type (producer/converter/additive producer/compounder/equipment manufacturer/technology company)
   - Column C: Company webpage

2. **Determine Week**:
   - Starts with the current ISO week (e.g., "2025-W42")
   - Checks if all companies in output file have "News detected" = YES for current week
   - If yes, moves to previous week, repeats until finding a week that needs processing

3. **User Input**: Asks how many news stories to find (how many companies to process)

4. **Search News**: For each company without an entry for the target week:
   - Queries Perplexity API using `site:{webpage}` operator to search only company website
   - Looks for bioplastic-related news/press releases from that specific week
   - Extracts: news detected (YES/NO), 50-word description, exact URL
   - Adds 5-second delay between API calls to avoid rate limits

5. **Output Results**: Appends to `companies_news.xlsx`:
   - Column A: Company name
   - Column B: ISO week (e.g., "2025-W43")
   - Column C: News detected (YES/NO or empty)
   - Column D: 50-word description (or empty)
   - Column E: Exact URL of news story from company webpage

6. **Error Logging**: Any errors are logged to `bioplastic_news_errors.log`

## When to Use This Skill

Invoke this skill when you want to:
- Fetch latest bioplastic news for companies in the database
- Update the news tracking spreadsheet
- Search for company press releases and announcements
- Monitor bioplastic industry developments from official company sources

## Usage

Simply say:
- "Run the bioplastic news fetcher"
- "Fetch news for companies"
- "Update company news database"
- "Check for new bioplastic news"

## Technical Details

- Uses Perplexity API with site-specific search
- Rate limited: 5 seconds between API calls
- Appends to existing data (never overwrites)
- Skips already-processed company/week combinations
- Searches only official company websites (no third-party news)

## Files

- Main script: `fetch_company_news.py`
- Input: `/home/sven/bioplastic-website-newsgenerator/companies.xlsx`
- Output: `/home/sven/bioplastic-website-newsgenerator/companies_news.xlsx`
- Errors: `/home/sven/bioplastic-website-newsgenerator/bioplastic_news_errors.log`
