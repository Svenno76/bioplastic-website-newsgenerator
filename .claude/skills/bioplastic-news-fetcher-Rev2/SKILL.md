---
name: bioplastic-news-fetcher-Rev2
description: General bioplastic news aggregator prioritizing company websites. Searches for industry news from the last 7 days, categorizes into 10 news types, uses fuzzy matching (85% threshold) to identify companies, validates dates and filters non-company entities, auto-discovers new companies, and outputs structured data with Category, Headline, and URL fields.
---

# Bioplastic News Fetcher Rev2

A quality-focused, general-search approach to fetching bioplastic industry news that prioritizes first-hand company announcements and applies strict validation filters.

## Philosophy: General Search vs Company-Specific

**Rev1 Approach:** Query for specific companies in batches
**Rev2 Approach:** Search for general bioplastic news and match companies afterward

### Key Differences from Rev1

1. **General Industry Search** - Casts a wider net to find any bioplastic news
2. **Company Website Priority** - Explicitly prioritizes first-hand company announcements
3. **10 News Categories** - Same categories as Rev1 (Plant Announcement, M&A, Product Launch, etc.)
4. **Strict Validation** - Filters out non-companies, validates dates and categories
5. **Fuzzy Matching** - Matches company names with 85% similarity threshold
6. **Auto-Discovery** - Adds new companies to database automatically (name only)
7. **Restructured Output** - Includes: Company matched, Category, Headline, separate URL columns
8. **Quality over Quantity** - Single API call returning 5-10 validated items

## How It Works

### Phase 1: News Discovery

1. **Single API Call**: Queries Perplexity for bioplastic news from ACTUAL COMPANIES
   - Time range: Last 7 days (strictly enforced)
   - Target: 5-10 news items (configurable)
   - Priority: Company websites, press releases, official announcements
   - Exclusions: Market reports, industry associations, news publications
   - Categories: Only news in the 10 predefined categories

2. **JSON Response**: Requests structured JSON with fields:
   - Company: Company name (actual companies only)
   - PublishingDate: Date in YYYY-MM-DD format (must be within range)
   - Headline: Concise headline (max 100 characters)
   - Description: 50-word summary
   - Category: One of 10 predefined categories
   - SourceURL: URL where news was found (preferably company website)

### Phase 2: Validation & Filtering

1. **Non-Company Filter**:
   - Rejects entities containing: 'market', 'industry', 'report', 'insights', 'analysis', 'news', 'publication', 'association', 'research', 'study', 'survey', 'forecast', 'outlook'
   - Example: "Global Biopolymers Market" → Rejected ❌
   - Example: "Braskem" → Accepted ✓

2. **Date Validation**:
   - Parses publishing date
   - Verifies date is within specified range (e.g., Oct 23-30, 2025)
   - Rejects news outside the window

3. **Category Validation**:
   - Validates category is one of the 10 predefined categories
   - Rejects items with invalid/missing categories

4. **Field Validation**:
   - Ensures all required fields present: Company, PublishingDate, Headline, Description, Category, SourceURL

### Phase 3: Company Matching

1. **Fuzzy Matching** (85% threshold):
   - Loads companies from `companies.xlsx`
   - Compares each validated news item's company name against known companies
   - Matches variations: "BASF" = "BASF SE" = "BASF Biopolymers"
   - Returns best match if score >= 85%

2. **Auto-Discovery**:
   - If no match found (score < 85%), marks as new company
   - Adds company to `companies.xlsx` with:
     - Company name (from news)
     - Empty Type, Webpage, Description (for manual entry later)

### Phase 4: URL Categorization

1. **Company URL vs Other URL**:
   - For matched companies: checks if source URL matches company's webpage domain
   - If match: stores in "Source URL (company)" column
   - If no match: stores in "Source URL (other)" column
   - For new companies: always stores in "Other URL" (no known webpage yet)

### Phase 5: Output

Updates/creates two files:

**companies.xlsx** (with any new companies):
- Column A: Company
- Column B: Type (empty for new companies)
- Column C: Webpage (empty for new companies)
- Column D: Description (empty for new companies)

**companies_news.xlsx** (restructured format):
- Column A: Company (original name from news)
- Column B: Company matched (matched name from companies.xlsx, or empty if new)
- Column C: Publishing Date (YYYY-MM-DD)
- Column D: Headline (max 100 characters)
- Column E: Description (50 words)
- Column F: Category (one of 10 categories)
- Column G: Source URL (company) (if from company website)
- Column H: Source URL (other) (if from third-party news site)
- Column I: Week (ISO format: YYYY-WXX)

## News Categories (Same as Rev1)

1. **Plant Announcement** - Plant openings, closures, revamps, maintenance, capacity changes
2. **People Moves** - Key decision makers joining or leaving
3. **M&A** - Mergers and acquisitions
4. **Litigation** - Court cases, arbitration, lawsuits
5. **Product Launch** - New materials, grades, formulations, innovations
6. **Partnerships** - Collaborations, joint ventures, R&D agreements
7. **Financial Results** - Earnings, revenue reports, financial performance
8. **Supply Agreements** - Offtake agreements, contracts, customer wins
9. **Investment & Funding** - Capital raises, grants, government funding
10. **Certifications** - Regulatory approvals, certifications, compliance

## When to Use This Skill

Invoke Rev2 when you want to:
- Quickly test the news fetching system with small batches
- Discover new companies in the bioplastic space
- Get a broad overview of recent industry news
- Find news that might not appear on company websites (e.g., M&A rumors, analyst reports)
- Test API integration without processing hundreds of companies

## Usage

Simply say:
- "Run bioplastic news fetcher Rev2"
- "Fetch news using Rev2"
- "Test Rev2 news fetcher"
- "Find new bioplastic companies"

## Technical Details

### Efficiency
- **Single API call** per run (vs Rev1's 30-90 calls)
- **5-10 items** per run (configurable)
- **~5-10 seconds** total execution time
- **Low cost** for testing and small-scale monitoring

### Data Quality Features
- **Multi-layer validation**: Non-company filter, date validation, category validation, field validation
- **Strict date filtering**: Only news within specified date range (e.g., last 7 days)
- **Category enforcement**: All news must fit into one of 10 predefined categories
- **JSON response parsing**: Handles markdown cleanup automatically
- **Fuzzy matching**: Prevents duplicates from company name variations
- **ISO week calculation**: Time-based tracking compatible with Rev1
- **Source URL categorization**: Separates company vs third-party news sources
- **Automatic new company detection**: Adds discoveries to companies.xlsx

### Important Notes
- **API Date Accuracy**: Perplexity may return news outside the requested date range. Rev2's validation layer filters these out, but this means you may get fewer valid results than requested.
- **Company Website Priority**: While the prompt prioritizes company websites, search results may still include third-party news sites. The URL categorization helps identify the source.
- **Quality over Quantity**: Rev2 prioritizes validation and quality, which may result in fewer news items per run compared to Rev1.

### Fuzzy Matching Algorithm
- Uses fuzzywuzzy library with Levenshtein distance
- Threshold: 85% similarity
- Case-insensitive comparison
- Returns best match above threshold
- Examples:
  - "BASF" matches "BASF SE" (95%)
  - "Nature Works" matches "NatureWorks" (92%)
  - "Total Corbion PLA" matches "TotalEnergies Corbion" (70% - no match)

## Example Output

```
======================================================================
🌱 BIOPLASTIC NEWS FETCHER REV2
======================================================================

📂 Loading companies file...
  ✓ Loaded 27 companies

🔍 Fetching bioplastic news from October 23 to October 30, 2025...
📡 Calling Perplexity API...
✓ API call successful

📄 Raw response:
[
  {
    "Company": "Braskem",
    "PublishingDate": "2025-10-29",
    "Headline": "Braskem advances biopolymer production with Renewable Innovation Center",
    "Description": "Braskem continues expanding its biobased product portfolio...",
    "Category": "Plant Announcement",
    "SourceURL": "https://www.packagingdive.com/news/..."
  },
  ...
]

✓ Successfully parsed 10 news items

🔍 Processing 10 news items...
  ⚠️  Skipping 'CJ Biomaterials': Date 2025-10-06 outside range
  ⚠️  Skipping 'Teknor Apex': Date 2025-06-01 outside range
  ✓ Matched 'Braskem' to 'Braskem' (score: 100)
  ⚠️  Skipping 'Green Dot Bioplastics': Date 2025-10-15 outside range
  ⚠️  Skipping 'Global Biopolymers Market': Not a company (contains 'market')
  ...

💾 Saving results...
  ✓ Updated companies.xlsx
  ✓ Saved 1 news items to companies_news.xlsx

======================================================================
✅ REV2 PROCESSING COMPLETE!
======================================================================
  Valid news items: 1
  New companies discovered: 0
  Total companies in database: 27

📊 Category breakdown:
     Plant Announcement: 1
======================================================================
```

## Comparison: Rev1 vs Rev2

| Aspect | Rev1 | Rev2 |
|--------|------|------|
| Search approach | Company-specific batches | General industry search |
| API calls | 30-90 per run | 1 per run |
| News items per run | 30-100+ | 5-10 |
| Processing time | 15-20 minutes | 5-10 seconds |
| Best for | Weekly bulk processing | Testing & discovery |
| Company discovery | Automatic with type guessing | Automatic (name only) |
| News coverage | Comprehensive | Broad overview |
| Cost per run | Medium | Very low |
| Use case | Production weekly runs | Testing & exploration |

## Recommendations

- **For testing**: Use Rev2 to validate API integration and data flow
- **For discovery**: Use Rev2 to find new companies entering the market
- **For production**: Use Rev1 for comprehensive weekly news aggregation
- **For quick checks**: Run Rev2 daily for headline news monitoring

## Recent Improvements (2025-10-30)

### 1. Append Mode (Instead of Overwrite)
**Problem**: Each run was overwriting `companies_news.xlsx`, losing previous data.

**Solution**: Modified `save_results()` function to:
- Check if `companies_news.xlsx` exists
- Read existing data and append new items
- Display total count after appending

**Result**: Progressive data accumulation across multiple runs.

### 2. Two-Layer Deduplication System
**Problem**: Multiple runs were creating duplicate news items in the database.

**Solution**: Implemented a two-layer deduplication approach:

#### Layer 1: Prompt-Level (Week-Specific URL Exclusion)
- **Before API call**: Reads existing `companies_news.xlsx`
- **Filters for current ISO week**: Only considers URLs from the same week
- **Builds exclusion list**: Extracts all URLs (both company and other sources)
- **Adds to prompt**: Tells API to exclude these specific URLs
- **Benefit**: Prevents API from wasting tokens fetching already-covered news

```python
# Example: Week 2025-W44 has 11 items with 5 unique URLs
exclude_urls = ['url1', 'url2', 'url3', 'url4', 'url5']
# Added to API prompt: "EXCLUDE news from these URLs (already covered this week):"
```

#### Layer 2: Post-Processing (All-Time URL Deduplication)
- **Before saving**: Checks ALL existing URLs in the file (not just current week)
- **Filters new items**: Removes any that match existing URLs
- **Safety net**: Catches duplicates the API might return despite exclusion
- **Benefit**: Guarantees zero duplicates in the database

```python
# Compares new items against ALL existing URLs
existing_urls = set(existing_df['Source URL (company)'] + existing_df['Source URL (other)'])
news_df_filtered = news_df[~news_df.urls.isin(existing_urls)]
```

### 3. Test Results

**Run 1** (Initial test):
- Fetched: 10 items from API
- Valid after date filtering: 3 items
- Duplicates removed: 2
- Added to database: 1 new item
- Total: 12 → 13 items

**Run 2** (Confirmation test):
- Fetched: 10 items from API
- Valid after date filtering: 5 items
- Duplicates removed: 2
- Added to database: 3 new items
- Total: 13 → 16 items
- New companies discovered: Roquette Frères, BASF SE

### 4. Why Both Layers?

**Layer 1 (Prompt)**: Reduces API waste by requesting different sources, but API may still ignore instructions.

**Layer 2 (Code)**: Guarantees no duplicates make it to the database, regardless of API behavior.

Together, they provide robust deduplication while optimizing API usage.

## Future Enhancements

Potential improvements for Rev2:
1. Increase max_items to 20-30 for more comprehensive single-batch coverage
2. ~~Add category classification (like Rev1's 10 categories)~~ ✅ Already implemented
3. Implement multiple API calls with different query angles
4. ~~Add deduplication across multiple runs~~ ✅ Implemented 2025-10-30
5. Integrate with Rev1's complementary query logic

## Files

- Main script: `.claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py`
- Input: `companies.xlsx` (20+ companies)
- Output: `companies_news.xlsx` (restructured format)
- Errors: `bioplastic_news_errors.log`

Rev2 is ideal for quick testing, new company discovery, and small-scale news monitoring.
