# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bioplastic News Generator is an automated news aggregator for the bioplastic industry. It uses the Perplexity AI API to search for recent news about bioplastic companies and generates content for a Hugo static site.

The system tracks 33+ bioplastic companies across 10 categories with automatic enrichment of company data and intelligent news deduplication using AI-powered search.

## Core Architecture

### Configuration System
- `config.py`: Central configuration module using python-dotenv
  - `Config` class manages API keys, endpoints, and settings
  - `Config.validate()`: Validates environment and creates necessary directories
  - `Config.display_config()`: Shows configuration (masks sensitive data)
  - Key settings: `DEFAULT_MODEL`, `MAX_TOKENS`, `TEMPERATURE`, `DAYS_TO_SEARCH`

### API Integration
- Uses Perplexity AI's chat completions API (sonar models)
- All API calls include `return_citations: True` for credibility
- Standard timeout: 30 seconds for all requests

### Data Structure

**Company Database (`companies.xlsx`)**:
Main database tracking all bioplastic companies with fields:
- `Company`: Company name
- `Type`: Company category (10 categories - see Skills section)
- `Country`: Headquarters location
- `Webpage`: Official company website
- `Description`: 2-3 sentence company overview
- `Primary Materials`: Specific bioplastics (PLA, PHA, PBS, starch-based, etc.)
- `Market Segments`: Industries served (packaging, agriculture, automotive, etc.)
- `Status`: Active/Acquired/Defunct/Unknown
- `Publicly Listed`: Yes/No - whether company is publicly traded
- `Stock Ticker`: Stock exchange symbol (e.g., NASDAQ:DNMR, NYSE:AMCR)
- `Date Added`: When company was added/enriched

**News Database (`companies_news.xlsx`)**:
Tracks discovered news items with deduplication:
- `Company`: Original company name from news source
- `Company matched`: Matched name from companies.xlsx
- `Publishing Date`: Date in YYYY-MM-DD format
- `Headline`: News headline (max 100 chars)
- `Description`: 50-word summary
- `Category`: One of 10 news categories
- `Source URL (company)`: URL if from company website
- `Source URL (other)`: URL if from third-party source
- `Week`: ISO week format (YYYY-WXX)

### Output Organization
- `output/`: Generated news output directory
- `content/news/`: Hugo content directory for static site generation
- `news_cache/`: Cache directory for news data (created by setup)

## Development Commands

### Setup and Testing
```bash
# Initial setup (creates .env, installs deps, creates directories)
./setup.sh

# Test API connection and basic functionality
python3 test_perplexity_api.py

# Install dependencies manually
pip3 install -r requirements.txt
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx
```

## Available Skills

The project includes specialized AI skills (located in `.claude/skills/`) for automated tasks:

### 1. Bioplastic News Fetcher Rev2
**Location**: `.claude/skills/bioplastic-news-fetcher-Rev2/`

**Purpose**: General industry news aggregator that discovers and categorizes bioplastic news.

**Features**:
- General search approach (vs company-specific queries)
- Prioritizes company websites and first-hand announcements
- 10 news categories (Plant Announcement, M&A, Product Launch, Partnerships, etc.)
- Fuzzy matching (85% threshold) to identify companies
- Auto-discovers new companies and adds them to `companies.xlsx`
- Two-layer deduplication system:
  - Layer 1: Week-specific URL exclusion at prompt level
  - Layer 2: All-time URL deduplication in post-processing
- Append mode to accumulate news progressively
- Outputs structured data to `companies_news.xlsx`

**Usage**:
```bash
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py
```

**Key Files**:
- Main script: `fetch_company_news.py`
- Input: `companies.xlsx`
- Output: `companies_news.xlsx`
- Documentation: `SKILL.md`

### 2. Company Enrichment
**Location**: `.claude/skills/company-enrichment/`

**Purpose**: Automatically researches and fills missing company information using AI.

**Features**:
- Identifies companies with incomplete data
- Researches using Perplexity AI
- Fills in missing fields:
  - Type (10 company categories)
  - Country (headquarters location)
  - Description (2-3 sentence overview)
  - Primary Materials (specific bioplastics)
  - Market Segments (industries served)
  - Status (Active/Acquired/Defunct/Unknown)
  - Publicly Listed (Yes/No)
  - Stock Ticker (exchange symbol if publicly traded)
  - Webpage (validates and corrects URLs)
- Only updates empty fields (preserves existing data)
- Creates backup before processing
- Validates all data before saving
- **Automatically deletes companies with Type = "Unknown"** to maintain database quality

**Company Categories**:
1. Bioplastic Producer - Manufactures raw materials
2. Compounder - Blends and compounds materials
3. Converter - Processes into finished products
4. Technology Company - Develops technologies/patents
5. Equipment Manufacturer - Produces processing machinery
6. Additive Producer - Manufactures additives
7. Testing/Certification Company - Labs and certifications
8. Distributor/Trader - Distributes/trades materials
9. Recycling Company - Recycling specialists
10. Waste Management - Biodegradable waste handling

**Usage**:
```bash
python3 .claude/skills/company-enrichment/enrich_companies.py
```

**Key Files**:
- Main script: `enrich_companies.py`
- Input/Output: `companies.xlsx`
- Backup: `companies_backup.xlsx` (auto-created)
- Documentation: `SKILL.md`

**Workflow Integration**:
1. News Fetcher discovers new companies → adds to `companies.xlsx` with name only
2. Company Enrichment researches new companies → fills in all details
3. News Fetcher matches news more accurately with complete company data

## Key Implementation Patterns

### API Request Structure
All Perplexity API calls follow this pattern:
```python
headers = {
    "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": Config.DEFAULT_MODEL,
    "messages": [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user query"}
    ],
    "max_tokens": Config.MAX_TOKENS,
    "temperature": Config.TEMPERATURE,
    "return_citations": True,
    "stream": False
}

response = requests.post(Config.PERPLEXITY_API_URL, headers=headers, json=payload, timeout=30)
```

### News Query Format
Time-bounded queries should include explicit date ranges:
```python
from datetime import datetime, timedelta
today = datetime.now()
week_ago = today - timedelta(days=7)

query = f"""
Find recent news about {company} bioplastics company from the last week.
Time period: {week_ago.strftime('%B %d')} to {today.strftime('%B %d, %Y')}
"""
```

## Security Requirements

### Critical: Never Commit Secrets
- `.env` file must NEVER be committed (already in `.gitignore`)
- API keys should only exist in `.env` file
- Use `Config.display_config()` which masks sensitive data for debugging

### Pre-commit Checklist
Always verify before committing:
```bash
git status  # Verify .env is NOT listed
git diff    # Review all changes
```

## Dependencies

Core dependencies and their purposes:
- `python-dotenv`: Environment variable management
- `requests`/`httpx`: HTTP client for API calls
- `pandas`/`openpyxl`: Company data handling (CSV/Excel/JSON)
- `pyyaml`: Hugo front matter generation
- `markdown`: Content processing
- `python-dateutil`: Date parsing and manipulation

## Perplexity API Models

Available models (in config.py `DEFAULT_MODEL`):
- `sonar`: Faster, cost-effective (default)
- `sonar-pro`: Higher quality responses

Rate limits apply - consider adding delays between requests when processing many companies.

## Integration Points

### Hugo Static Site
- Generated news should be placed in `content/news/` directory
- Files should include Hugo front matter (YAML/TOML)
- Adjust `HUGO_CONTENT_DIR` in config.py to match your Hugo structure

## Project Status

### Completed Features ✅
1. **News Fetching System** - Rev2 skill with general search and deduplication
2. **Company Database** - 30 companies with full enrichment including stock market data
3. **Company Enrichment Skill** - Automatic research and data filling
4. **Stock Market Integration** - Tracks 11 publicly listed companies with tickers
5. **Deduplication System** - Two-layer approach (prompt + post-processing)
6. **Auto-discovery** - New companies automatically added and enriched
7. **Quality Control** - Automatic deletion of "Unknown" companies

### In Progress / Planned
1. **Company Profile Generator Skill** - Generate formatted company profiles for website from `companies.xlsx` data
2. Hugo templates for news display
3. Automated scheduling (cron jobs)
4. News analytics and filtering
5. Integration with Hugo static site generator

## Best Practices

### Running Skills in Sequence
Recommended workflow for new company discovery:

```bash
# Step 1: Fetch news (discovers new companies)
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py

# Step 2: Enrich any new companies
python3 .claude/skills/company-enrichment/enrich_companies.py

# Step 3: Review results
# Check companies.xlsx for newly enriched companies
# Check companies_news.xlsx for new news items
```

### Data Quality
- Always run enrichment after news fetcher discovers new companies
- Backup files are created automatically before modifications
- Review "Unknown" entries periodically - these may need manual research
- Validate company types and statuses quarterly

### API Usage
- News Fetcher: 1 API call per run (~$0.01-0.02)
- Company Enrichment: 1 API call per company (~$0.01-0.02 each)
- Both skills include 2-second delays to respect rate limits
- Monitor API usage in Perplexity dashboard
