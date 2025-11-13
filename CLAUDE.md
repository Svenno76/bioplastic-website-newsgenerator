# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

### Essential Commands

```bash
# Environment setup
python3 -m venv venv
source venv/bin/activate              # Activate virtual environment
python3 -m pip install -r requirements.txt

# Verify setup
python3 test_perplexity_api.py        # Test API connection
python3 -c "from config import Config; Config.validate(); Config.display_config()"

# Single-source workflow (fast, ~30 seconds)
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py
python3 .claude/skills/company-enrichment/enrich_companies.py

# Multi-source workflow (comprehensive, ~2 minutes)
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py && \
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py && \
python3 .claude/skills/company-enrichment/enrich_companies.py && \
python3 .claude/skills/news-story-generator/generate_news_stories.py

# Quick diagnostics
git status && git diff                 # View pending changes
tail -20 news_story_generator_errors.log  # Check for errors
ls -lt content/news/ | head -5         # Recent generated stories
```

### Data Queries

```bash
# Company database status
python3 -c "import pandas as pd; df = pd.read_excel('companies.xlsx'); print(f'Total: {len(df)}, Enriched: {len(df[df[\"Type\"].notna()])}')"

# Pending news (not yet converted to stories)
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); pending = df[df['Story Generated'] == 'No']; print(f'Pending: {len(pending)}')"

# News statistics
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); print('By Category:'); print(df['Category'].value_counts())"
```

---

## Project Overview

Bioplastic News Generator is an automated news aggregator for the bioplastic industry. It uses the Perplexity AI API to search for recent news about bioplastic companies and generates content for a Hugo static site.

The system tracks 34+ bioplastic companies across 10 categories with automatic enrichment of company data and intelligent news deduplication using AI-powered search.

## File Structure

```
/
├── config.py                           # Central configuration (API keys, settings)
├── test_perplexity_api.py              # API connection test script
├── setup.sh                            # Initial setup script
├── requirements.txt                    # Python dependencies
│
├── companies.xlsx                      # Main company database (34+ companies)
├── companies_news.xlsx                 # Aggregated news database
├── companies_backup.xlsx               # Auto-generated backup before enrichment
│
├── .env                               # API keys (NEVER commit!)
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore rules
│
├── venv/                              # Python virtual environment (auto-created)
│
├── .claude/skills/
│   ├── bioplastic-news-fetcher-Rev2/  # News aggregation (Perplexity) [TRACKED]
│   │   ├── fetch_company_news.py      # Main script
│   │   └── SKILL.md                   # Documentation
│   │
│   ├── company-enrichment/            # Company data enrichment [TRACKED]
│   │   ├── enrich_companies.py        # Main script
│   │   └── SKILL.md                   # Documentation
│   │
│   ├── gemini-news-fetcher/           # Alternative news source (Gemini) [GITIGNORED]
│   │   ├── fetch_gemini_news.py       # Main script
│   │   └── SKILL.md                   # Documentation
│   │
│   ├── news-story-generator/          # Hugo markdown generator [GITIGNORED]
│   │   ├── generate_news_stories.py   # Main script
│   │   └── SKILL.md                   # Documentation
│   │
│   ├── news-credibility-scorer/       # Verifies news credibility [GITIGNORED]
│   │   ├── score_news_credibility.py  # Main script
│   │   └── SKILL.md                   # Documentation
│   │
│   └── excel-formatter/               # Reusable Excel formatting [GITIGNORED]
│       ├── format_excel.py            # Main script
│       └── SKILL.md                   # Documentation
│
├── output/                            # Generated news output directory
├── content/news/                      # Hugo content directory for markdown files
├── news_cache/                        # Cache directory (auto-created by setup)
│
├── CLAUDE.md                          # This file - development guidance
├── README.md                          # Project overview and setup
└── transcript.md                      # Session documentation
```

### Gitignored Skills (Experimental Features)
These skills are not tracked in Git as they require local setup or are experimental:
- **gemini-news-fetcher**: Requires local Gemini CLI installation
- **news-story-generator**: Requires local Hugo site directory path
- **news-credibility-scorer**: Validates news accuracy (experimental)
- **excel-formatter**: Reusable formatting automation (experimental)

## Core Architecture

### Configuration System
- `config.py`: Central configuration module using python-dotenv
  - `Config` class manages API keys, endpoints, and settings
  - `Config.validate()`: Validates environment and creates necessary directories
  - `Config.display_config()`: Shows configuration (masks sensitive data)
  - Key settings: `DEFAULT_MODEL`, `MAX_TOKENS`, `TEMPERATURE`, `DAYS_TO_SEARCH`

### Python Environment
- **Required**: Python 3.8 or higher
- **Virtual Environment**: Uses `venv/` directory (auto-created by setup.sh)
- **Activation**: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- **Dependencies**: All installed via `requirements.txt`

**Virtual Environment Best Practices**:
```bash
# Create and activate
python3 -m venv venv
source venv/bin/activate

# Install dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Deactivate when done
deactivate
```

### API Integration
- Uses Perplexity AI's chat completions API (sonar models)
- All API calls include `return_citations: True` for credibility
- Standard timeout: 30 seconds for all requests
- Gemini CLI integration for alternative news sourcing (requires local Gemini installation)

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
Tracks discovered news items with deduplication, unique IDs, and generation status:
- `ID`: Unique identifier for each news item (auto-assigned sequentially)
- `Company`: Original company name from news source
- `Company matched`: Matched name from companies.xlsx
- `Publishing Date`: Date in YYYY-MM-DD format
- `Headline`: News headline (max 100 chars)
- `Description`: 50-word summary
- `Category`: One of 10 news categories
- `Source URL (company)`: URL if from company website
- `Source URL (other)`: URL if from third-party source
- `Week`: ISO week format (YYYY-WXX)
- `Source Skill`: Which fetcher found the news (Gemini/Perplexity Rev2)
- `Story Generated`: Yes/No - whether Hugo news story has been created

### Output Organization
- `output/`: Generated news output directory
- `content/news/`: Hugo content directory for static site generation
- `news_cache/`: Cache directory for news data (created by setup)

### Excel File Formatting
Both skills automatically format Excel files for optimal usability:

**Clickable URLs**:
- All URLs become clickable hyperlinks
- Automatically adds `https://` prefix to URLs starting with `www.` or plain domains
- Blue hyperlink styling applied

**Column Widths** (`companies_news.xlsx`):
- ID: 8 | Company: 20 | Company matched: 20 | Publishing Date: 15
- Headline: 50 (wrapped) | Description: 60 (wrapped) | Category: 20
- Source URL (company): 40 | Source URL (other): 40 | Week: 12 | Source Skill: 15 | Story Generated: 15

**Column Widths** (`companies.xlsx`):
- Company: 25 | Type: 20 | Country: 15 | Webpage: 40 (clickable)
- Description: 70 (wrapped) | Primary Materials: 50 (wrapped) | Market Segments: 50 (wrapped)
- Status: 12 | Publicly Listed: 15 | Stock Ticker: 15 | Date Added: 15

**Text Wrapping**: Long text fields automatically wrap for better readability

### Column Purposes and Usage

**For News Processing**:
- `ID`: Unique identifier, used when generating specific stories
- `Company matched`: Standardized company name from `companies.xlsx`, used for matching and reporting
- `Publishing Date`: Original publication date in YYYY-MM-DD format
- `Headline`: News title, becomes Hugo article title
- `Story Generated`: Tracks which articles have been published to the website

**For Deduplication**:
- `Source URL (company)` and `Source URL (other)`: Prevent duplicate entries across multiple fetches
- `Week`: Helps identify if news is within current reporting period; used in deduplication logic

**For Analytics & Reporting**:
- `Category`: Segments news by type (M&A, Product Launch, Partnerships, etc.) for analytics
- `Source Skill`: Tracks which fetcher discovered the news (Gemini or Perplexity Rev2) for source attribution

## Workflow Architecture

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA FLOW OVERVIEW                       │
└─────────────────────────────────────────────────────────────────┘

OPTION 1: SINGLE-SOURCE WORKFLOW (Fast, ~30 seconds)
═════════════════════════════════════════════════════════════════

  companies.xlsx
      ↓
  [Rev2 News Fetcher: Perplexity API]
      │ └─→ Discovers new companies → adds to companies.xlsx
      │
      ↓
  companies_news.xlsx
      │ └─→ Contains: ID, Company matched, Headline, URLs, Category
      │
      ↓
  [Company Enrichment]
      │ └─→ Fills missing data for new companies
      │
      ↓
  enriched companies.xlsx


OPTION 2: MULTI-SOURCE WORKFLOW (Comprehensive, ~2 minutes)
═════════════════════════════════════════════════════════════════

  companies.xlsx
      ↓ ╔═══════════════════════════════════════════╗
      ├─→║ News Fetcher 1: Gemini (real-time web)  ║
      │  ╚═══════════════════════════════════════════╝
      │            ↓ (finds news + new companies)
      │
      ├─→║ News Fetcher 2: Perplexity Rev2         ║
      │  ╚═══════════════════════════════════════════╝
      │            ↓ (finds additional news)
      │
      ↓
  companies_news.xlsx (deduplicated by URL)
      │ └─→ All news merged with no duplicates
      │
      ↓
  [Company Enrichment]
      │ └─→ Fills missing data for all new companies
      │
      ↓
  enriched companies.xlsx
      │
      ↓
  [News Story Generator]
      │ └─→ Uses Perplexity to write 200-250 word articles
      │
      ↓
  /home/sven/bioplastic-website/content/news/*.md (Hugo articles)
```

### Processing Timeline & Performance

| Stage | Tool | Time | Cost | Notes |
|-------|------|------|------|-------|
| News Fetch (Perplexity) | Rev2 Fetcher | 5-10s | ~$0.01 | General industry search |
| News Fetch (Gemini) | Gemini Fetcher | 10-15s | Free | Real-time web search |
| Company Enrichment | Enricher | 2-30s | $0.01-0.10 | Depends on new companies |
| Story Generation | Generator | 30-60s | $0.01-0.03 | 1 API call per article |
| **Total (Multi-Source)** | **All** | **~2 min** | **~$0.05** | Full workflow |

**Key Points**:
- Fetchers deduplicate by URL automatically, so running multiple sources avoids duplicate news
- Enrichment improves fuzzy matching accuracy for all subsequent news fetches
- Story generator only processes items with `Story Generated = 'No'`
- Deduplication uses two-layer approach: prompt-level (week-specific) + code-level (all-time)

## Development Commands

### Initial Setup
```bash
# Initial setup (creates .env, installs deps, creates directories)
./setup.sh

# Or manual setup:
cp .env.example .env
# Edit .env and add your API key: PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx
pip3 install -r requirements.txt
```

### Quick Workflows
```bash
# Complete workflow: fetch → enrich → generate
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py && \
python3 .claude/skills/company-enrichment/enrich_companies.py && \
python3 .claude/skills/news-story-generator/generate_news_stories.py

# Multi-source comprehensive workflow (Gemini + Perplexity)
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py && \
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py && \
python3 .claude/skills/company-enrichment/enrich_companies.py && \
python3 .claude/skills/news-story-generator/generate_news_stories.py
```

### Testing & Verification
```bash
# Test API connection
python3 test_perplexity_api.py

# Verify configuration
python3 -c "from config import Config; Config.validate(); Config.display_config()"

# Check companies in database
python3 -c "import pandas as pd; df = pd.read_excel('companies.xlsx'); print(f'Total companies: {len(df)}'); print(df[['Company', 'Type', 'Country']].head())"

# Find companies needing enrichment
python3 -c "import pandas as pd; df = pd.read_excel('companies.xlsx'); missing = df[df['Type'].isna()]; print(f'Companies needing enrichment: {len(missing)}'); print(missing[['Company']])"

# Check pending news (not yet converted to stories)
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); pending = df[df['Story Generated'] == 'No']; print(f'Pending articles: {len(pending)}'); print(pending[['ID', 'Company matched', 'Headline']])"

# Get news statistics
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); print('News by Category:'); print(df['Category'].value_counts()); print('\nNews by Company (top 10):'); print(df['Company matched'].value_counts().head(10))"
```

### Debugging
```bash
# View current git status and changes
git status
git diff

# Check error logs
tail -f news_story_generator_errors.log

# List recently generated stories
ls -lt /home/sven/bioplastic-website/content/news/ | head -10

# Generate specific story by ID
python3 .claude/skills/news-story-generator/generate_news_stories.py 12
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
- **Excel formatting**: Clickable URLs, optimized column widths, text wrapping for long fields

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
- **Excel formatting**: Clickable URLs (auto-adds https://), optimized column widths, text wrapping

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

### 3. Gemini News Fetcher
**Location**: `.claude/skills/gemini-news-fetcher/`
**Status**: Project skill (gitignored)

**Purpose**: Alternative news source using Google's Gemini AI with real-time web search capabilities.

**Features**:
- Real-time web search capability for current news
- Same 10 news categories as Rev2
- Fuzzy matching (85% threshold) for company identification
- Auto-discovers new companies and adds them to `companies.xlsx`
- URL-based deduplication to prevent duplicate entries
- Tags news items with "Gemini search" source marker
- **Excel formatting**: Clickable URLs, optimized column widths, text wrapping

**Usage**:
```bash
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py
```

**Key Files**:
- Main script: `fetch_gemini_news.py`
- Input: `companies.xlsx`
- Output: `companies_news.xlsx` (appends)
- Documentation: `SKILL.md`

**Key Differences from Rev2**:
- Uses Gemini CLI instead of Perplexity API
- No direct API costs (uses free/existing Gemini tier)
- Real-time web search capabilities
- Alternative AI perspective may discover different sources

**Requirements**:
- Gemini CLI installed at `/home/sven/.nvm/versions/node/v20.19.5/bin/gemini`
- Same Python dependencies as other skills (pandas, openpyxl, fuzzywuzzy)

**Advantages**:
- **Complementary Coverage**: Different AI model may find news sources missed by Perplexity
- **Cost Effective**: No API costs beyond existing Gemini tier
- **Real-time Data**: Access to very recent web data
- **Alternative Perspective**: Provides validation/cross-checking of Perplexity results

**Recommended Multi-Source Workflow**:
For comprehensive news coverage, use both fetchers then enrich:
```bash
# Step 1: Fetch from Gemini (real-time web search)
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py

# Step 2: Fetch from Perplexity (specialized search)
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py

# Step 3: Enrich any new companies discovered by either source
python3 .claude/skills/company-enrichment/enrich_companies.py
```

### 4. News Story Generator
**Location**: `.claude/skills/news-story-generator/`
**Status**: Project skill (gitignored)

**Purpose**: Converts news items from `companies_news.xlsx` into Hugo-formatted markdown files using **Perplexity AI to research and write substantive 200-250 word articles**.

**Features**:
- **AI-Powered Content Generation**: Uses Perplexity API to research each news item and write professional 200-250 word articles
- **Context-Aware Writing**: AI understands the bioplastics industry and writes relevant, insightful content
- **Citation Removal**: Automatically strips citation brackets [1], [2], etc. from generated content
- **Word Count Validation**: Logs warnings if articles are outside 150-300 word range
- **Automatic Fallback**: If API fails, falls back to template-based content generation
- **ID-Based Selection**: Generate stories for specific news items by ID (e.g., `python3 generate_news_stories.py 12`)
- **News ID Display**: Shows list of available news with IDs when run without arguments
- **Hugo Front Matter**: Generates YAML front matter with title, date, tags, category, company, source
- **Smart Slug Generation**: Creates URL-friendly filenames (e.g., "teknor-apex-acquires-danimer-scientific")
- **Auto-Tagging**: Generates relevant tags based on company name, category, and keywords
- **Duplicate Detection**: Skips stories that already exist (based on filename)
- **Rate Limiting**: 3-second delay between API calls to respect rate limits
- **Date-Based Filenames**: Uses format `YYYY-MM-DD-slug.md` for proper Hugo sorting

**AI Research Process**:
1. Extracts headline, description, company, category, and source URL from news data
2. Sends to Perplexity API with specialized journalism prompt
3. AI writes 200-250 word article with context, background, and industry significance
4. Validates word count and logs results
5. Falls back to template-based content if API fails

**Usage**:
```bash
# Generate all news stories
python3 .claude/skills/news-story-generator/generate_news_stories.py

# Generate story for specific news ID
python3 .claude/skills/news-story-generator/generate_news_stories.py 12
```

**API Configuration**:
- Requires `PERPLEXITY_API_KEY` in `.env` file
- API timeout: 45 seconds per request
- Rate limit delay: 3 seconds between requests
- Cost: ~$0.001-0.003 per article (very affordable)

**Key Files**:
- Main script: `generate_news_stories.py`
- Input: `companies_news.xlsx`
- Output: `/home/sven/bioplastic-website/content/news/*.md`
- Logs: `news_story_generator_errors.log`
- Documentation: `SKILL.md`

**Output Configuration**:
- Hugo directory: `/home/sven/bioplastic-website/content/news/`
- Change by editing `HUGO_NEWS_DIR` variable in script

**Workflow Integration**:
Run after news fetching and enrichment as the final step to publish AI-researched, professionally-written content to the Hugo website.

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
- `pandas`: DataFrame operations and Excel file I/O
- `openpyxl`: Excel formatting (clickable URLs, column widths, text wrapping)
- `fuzzywuzzy`/`python-Levenshtein`: Fuzzy string matching for company names
- `pyyaml`: Hugo front matter generation
- `markdown`: Content processing
- `python-dateutil`: Date parsing and manipulation

## Perplexity API Models

Available models (in config.py `DEFAULT_MODEL`):
- `sonar`: Faster, cost-effective (default)
- `sonar-pro`: Higher quality responses

Rate limits apply - consider adding delays between requests when processing many companies.

## Performance & Optimization

### Expected Execution Times

**Individual Skills**:
| Skill | Time | Depends On | Notes |
|-------|------|-----------|-------|
| Rev2 News Fetcher | 5-10s | Perplexity API speed | ~$0.01 per run |
| Gemini Fetcher | 10-15s | Gemini CLI response | Free tier available |
| Company Enrichment | 2-30s | # of new companies | ~$0.01-0.10 per company |
| Story Generator | 30-90s | # of pending articles | ~1-3s per article |

**Full Workflows**:
```bash
# Single-source (fastest)
Single Fetcher + Enrichment = ~20-40 seconds (minimal cost)

# Multi-source (comprehensive)
Gemini + Perplexity + Enrichment + Generator = ~2-3 minutes (low cost)
```

### Performance Factors

**Slow API Responses**:
- Perplexity API: Usually responds in 3-7 seconds
- If exceeding 15 seconds: Check API dashboard for quota/rate limits
- If Gemini is slow: May need to wait for CLI startup (~5 seconds)

**Slow Enrichment**:
- First company: ~2-3 seconds (includes model load time)
- Subsequent companies: ~0.5-1 second each
- 10 new companies: ~10-15 seconds total

**Slow Story Generation**:
- First article: ~3-5 seconds (includes model load time)
- Subsequent articles: ~1-2 seconds each
- 10 pending articles: ~15-25 seconds total

### Optimization Tips

**To speed up enrichment**:
```bash
# Only enrich companies without Type field
python3 .claude/skills/company-enrichment/enrich_companies.py
# Skips already-enriched companies automatically
```

**To speed up story generation**:
```bash
# Generate specific articles instead of all pending
python3 .claude/skills/news-story-generator/generate_news_stories.py 5  # Just article ID 5
python3 .claude/skills/news-story-generator/generate_news_stories.py 1 2 3  # Multiple IDs
```

**To reduce API costs**:
```bash
# Use Gemini for daily monitoring (free)
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py

# Use Perplexity for weekly comprehensive runs
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py  # Once per week

# Skip story generation if not needed
# Only run when you have time to publish new content
```

**To monitor performance**:
```bash
# Time a workflow execution
time python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py
time python3 .claude/skills/company-enrichment/enrich_companies.py

# Check API quotas
# Visit https://www.perplexity.ai/settings/api to see usage
```

### Memory Usage
- All operations use minimal memory (~100-200MB)
- Excel files with 100+ companies: ~5-10MB on disk
- No issues with typical hardware (2GB+ RAM recommended)

## Integration Points

### Hugo Static Site
- Generated news should be placed in `content/news/` directory
- Files should include Hugo front matter (YAML/TOML)
- Adjust `HUGO_CONTENT_DIR` in config.py to match your Hugo structure

## Data Backup & Recovery

### Automatic Backups
The system automatically creates backups before potentially destructive operations:

```bash
# Before enrichment runs
companies_backup.xlsx     # Auto-created, safe to keep or delete

# Before news generation
No automatic backup of companies_news.xlsx (data only appends)
```

### Manual Backup Strategy

```bash
# Create manual backup before running enrichment
cp companies.xlsx "companies_backup_$(date +%Y%m%d_%H%M%S).xlsx"
cp companies_news.xlsx "companies_news_backup_$(date +%Y%m%d_%H%M%S).xlsx"

# View backup history
ls -lh companies*.xlsx

# Restore from backup
cp companies_backup.xlsx companies.xlsx        # From auto-backup
cp "companies_backup_20251113_143022.xlsx" companies.xlsx  # From manual backup
```

### Excel File Handling Notes

**Important Limitations**:
- **openpyxl** (used for formatting) may lose some formatting when re-saving
  - Workaround: Keep a copy of formatted file before major operations
  - Formatting (URLs, column widths, text wrap) is reapplied on each write
- **Cell comments and annotations** may not survive formatting operations
  - If you add manual notes, save them separately or add as row descriptions
- **Merged cells**: Some complex merged cell structures may not persist
  - Simple merges are preserved; avoid complex formatting
- **Macro-enabled files**: Not supported by pandas/openpyxl
  - Use .xlsx format only (not .xlsm)

### Recovery Procedures

**If companies.xlsx is corrupted**:
```bash
# Option 1: Restore from backup
cp companies_backup.xlsx companies.xlsx

# Option 2: Restore from git (if not yet committed)
git checkout companies.xlsx

# Option 3: Restore from dated backup
cp "companies_backup_20251113_143022.xlsx" companies.xlsx
```

**If companies_news.xlsx is corrupted**:
```bash
# Option 1: Restore from backup (if available)
cp "companies_news_backup_20251113_143022.xlsx" companies_news.xlsx

# Option 2: Re-fetch news (will deduplicate automatically)
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py
# Note: This appends to existing data, so use empty file if complete re-fetch needed
rm companies_news.xlsx
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py

# Option 3: Restore from git
git checkout companies_news.xlsx
```

**If accidentally deleted news stories**:
```bash
# Check git history
git log --follow --oneline content/news/

# Restore specific date
git checkout HEAD~5 -- content/news/  # Restore from 5 commits ago

# Or restore single article
git checkout HEAD -- content/news/YYYY-MM-DD-slug.md
```

## Project Status

### Completed Features ✅
1. **News Fetching System (Perplexity Rev2)** - Tracked in git, production-ready
2. **Company Database** - 34+ companies with full enrichment including stock market data (tracked)
3. **Company Enrichment Skill** - Automatic research and data filling with quality control (tracked)
4. **Stock Market Integration** - Tracks publicly listed companies with stock tickers (tracked)
5. **Deduplication System** - Two-layer approach (prompt + post-processing) to prevent duplicates (tracked)
6. **Multi-Source Capability** - Alternative Gemini fetcher for complementary coverage (gitignored)
7. **Auto-discovery** - New companies automatically added with name-only entries (tracked)
8. **Quality Control** - Automatic deletion of "Unknown" companies to maintain data quality (tracked)
9. **Excel Formatting** - Clickable URLs, optimized column widths, text wrapping (2025-11-05, tracked)
10. **News Story Generator** - Hugo markdown generation with AI-powered 200-250 word articles (gitignored, 2025-11-10)
11. **News Credibility Scorer** - Verifies news against company websites with 0-100 credibility scores (gitignored, 2025-11-12)
12. **Excel Formatter Skill** - Reusable automation for consistent Excel formatting (gitignored, 2025-11-12)

### Files Not in Git (Project Skills)
These files are intentionally gitignored as they are experimental features or require local setup:

**Experimental/Alternative Skills**:
- `.claude/skills/gemini-news-fetcher/` - Alternative news fetcher using Google Gemini CLI (requires local Gemini installation)
- `.claude/skills/news-story-generator/` - Hugo content generator with AI-powered articles (requires local Hugo site path)
- `.claude/skills/news-credibility-scorer/` - Verifies news against company websites, assigns credibility scores (0-100)
- `.claude/skills/excel-formatter/` - Reusable Excel formatting automation for consistent styling and formatting

**Generated/Temporary Files** (auto-created during operations):
- `companies_backup.xlsx` - Auto-created before enrichment (can be regenerated)
- Generated Hugo markdown files in `/home/sven/bioplastic-website/content/news/` (tracked in separate Hugo repo)

### In Progress / Planned
1. **Company Profile Generator Skill** - Generate formatted company profiles for website from `companies.xlsx` data
2. Hugo templates for news display
3. Automated scheduling (cron jobs or GitHub Actions)
4. News analytics dashboard and filtering UI

## Troubleshooting

### News Not Being Found or Inconsistent Results
**Symptoms**: Few news items discovered, or same news found by different fetchers
- Check if company names in `companies.xlsx` match actual company names (fuzzy matching uses 85% threshold)
- Verify `DAYS_TO_SEARCH` in config.py (default: 7 days) - reduce for more results from recent period
- Run `test_perplexity_api.py` to confirm API access and quota
- Check Perplexity API usage at https://www.perplexity.ai/settings/api to ensure quota isn't exceeded
- For Gemini fetcher, verify Gemini CLI is installed at `/home/sven/.nvm/versions/node/v20.19.5/bin/gemini`

**Solution**: Run enrichment after fetching - matching improves with complete company data:
```bash
python3 .claude/skills/company-enrichment/enrich_companies.py
```

### Duplicate News Items Appearing
**Symptoms**: Same news item appears multiple times in `companies_news.xlsx`
- URL-based deduplication should prevent this, but check:
  - Are `Source URL (company)` and `Source URL (other)` columns populated correctly?
  - Did you run the fetchers in immediate succession (without manual edits)?
- Manually remove duplicates by comparing `Source URL` columns and keeping the first occurrence with complete metadata

**Solution**: Always run enrichment before second fetcher to ensure company name standardization:
```bash
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py
python3 .claude/skills/company-enrichment/enrich_companies.py
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py
```

### Story Generation Failures
**Symptoms**: Articles not being generated, or `Story Generated` column not updating
- Check `news_story_generator_errors.log` for specific error messages
- Verify Perplexity API key is valid: `python3 test_perplexity_api.py`
- Confirm Hugo output directory exists: `/home/sven/bioplastic-website/content/news/`
- Check that `Story Generated` column values are exactly "No" (case-sensitive)

**Solution**:
```bash
# Verify pending articles exist
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); print(df[df['Story Generated'] == 'No'][['ID', 'Company matched', 'Headline']])"

# Try generating specific article
python3 .claude/skills/news-story-generator/generate_news_stories.py 5
```

### Excel File Corruption or Unexpected Changes
**Symptoms**: Missing data, corrupted formatting, or column shifts
- Before enrichment, `companies_backup.xlsx` is created automatically
- If main file is corrupted, restore from backup:
  ```bash
  cp companies_backup.xlsx companies.xlsx
  ```
- If `companies_news.xlsx` is corrupted beyond repair, the data can be re-fetched (will deduplicate automatically)

### Excel File Handling Issues
**Symptoms**: URLs not clickable, column widths wrong, or formatting lost after running skills
- **Cause**: openpyxl library limitations - some Excel features don't persist
- **Note**: This is normal behavior - formatting is reapplied on each write
- **Workaround**: Formatting (URLs, widths, wrapping) is automatically reapplied when skills run
- **If manual formatting is important**: Keep a separate reference copy before running skills

**Symptoms**: File opens slowly or shows "File is corrupted" warning
- **Cause**: Possible file corruption from unexpected shutdown or large data additions
- **Solution**: Restore from backup and check disk space
- **Prevention**: Always shut down skills cleanly (Ctrl+C), don't kill process mid-write

**Symptoms**: Merged cells, custom colors, or special formatting disappear
- **Known Limitation**: openpyxl doesn't fully preserve all Excel features
- **Affected Features**:
  - Cell colors (custom fill colors)
  - Merged cells (complex ones may break)
  - Cell comments
  - Conditional formatting
- **Recommendation**: Keep formatting simple; use column widths and text wrapping only

### Company Enrichment Not Working
**Symptoms**: "Unknown" companies not being researched, or enrichment stops early
- Run `Config.validate()` to verify Perplexity API access
- Check that `PERPLEXITY_API_KEY` is set correctly in `.env`
- Company Enrichment automatically deletes companies with `Type = "Unknown"` - this is intentional quality control
- If a company should be kept, manually add its Type before running enrichment

**Solution**: Check error logs and verify API:
```bash
python3 test_perplexity_api.py
python3 .claude/skills/company-enrichment/enrich_companies.py
```

## Best Practices

### Running Skills in Sequence

**Option 1: Single Source (Perplexity Rev2)**
```bash
# Step 1: Fetch news (discovers new companies)
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py

# Step 2: Enrich any new companies
python3 .claude/skills/company-enrichment/enrich_companies.py

# Step 3: Review results
# Check companies.xlsx for newly enriched companies
# Check companies_news.xlsx for new news items
```

**Option 2: Multi-Source (Comprehensive Coverage)**
For best coverage, use both Gemini and Perplexity fetchers, then generate Hugo content:
```bash
# Step 1: Fetch from Gemini (real-time web search)
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py

# Step 2: Fetch from Perplexity (specialized search)
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py

# Step 3: Enrich any new companies discovered by either source
python3 .claude/skills/company-enrichment/enrich_companies.py

# Step 4: Generate Hugo news stories for website
python3 .claude/skills/news-story-generator/generate_news_stories.py

# Step 5: Review results
# Both fetchers deduplicate by URL, so no duplicate news items
# Check companies_news.xlsx for new news items
# Check /home/sven/bioplastic-website/content/news/ for generated stories
```

### Data Quality
- Always run enrichment after news fetcher discovers new companies
- Backup files are created automatically before modifications
- Review "Unknown" entries periodically - these may need manual research
- Validate company types and statuses quarterly

### API Usage
- **Perplexity News Fetcher (Rev2)**: 1 API call per run (~$0.01-0.02)
- **Gemini News Fetcher**: Uses Gemini CLI (free tier available, no direct API costs)
- **Company Enrichment**: 1 API call per company (~$0.01-0.02 each)
- **News Story Generator**: 1 API call per news item (~$0.001-0.003 each)
- All Perplexity-based skills include delays to respect rate limits (2-3 seconds)
- Monitor Perplexity API usage in dashboard
- For cost optimization: Use Gemini fetcher for daily checks, Perplexity for weekly comprehensive runs

### Estimated Costs
For a typical workflow processing 10 news items:
- News Fetcher Rev2: $0.01-0.02 (1 call)
- Company Enrichment: $0.03-0.06 (3 new companies)
- News Story Generator: $0.01-0.03 (10 articles)
- **Total**: ~$0.05-0.11 per workflow run (very affordable)

### Role-Based Workflows

#### For News Editor
Check what articles are pending publication:
```bash
# List all articles waiting to be generated
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); pending = df[df['Story Generated'] == 'No']; print(f'Pending: {len(pending)} articles'); print(pending[['ID', 'Company matched', 'Headline', 'Publishing Date']])"

# Generate stories for all pending articles
python3 .claude/skills/news-story-generator/generate_news_stories.py

# Or generate a specific article by ID
python3 .claude/skills/news-story-generator/generate_news_stories.py 5

# Review recently generated content
ls -lt /home/sven/bioplastic-website/content/news/ | head -10
```

#### For Company Database Manager
Track company data completeness and run enrichment:
```bash
# Check companies needing enrichment
python3 -c "import pandas as pd; df = pd.read_excel('companies.xlsx'); missing = df[df['Type'].isna()]; print(f'Companies needing enrichment: {len(missing)}'); print(missing[['Company', 'Country']])"

# Run enrichment to fill missing data
python3 .claude/skills/company-enrichment/enrich_companies.py

# Verify enrichment results
python3 -c "import pandas as pd; df = pd.read_excel('companies.xlsx'); print(f'Total companies: {len(df)}'); print(f'Fully enriched: {len(df[df[\"Type\"].notna()])}'); print(f'Publicly listed: {len(df[df[\"Publicly Listed\"] == \"Yes\"])}')"

# Check for data quality issues
python3 -c "import pandas as pd; df = pd.read_excel('companies.xlsx'); print('Status breakdown:'); print(df['Status'].value_counts())"
```

#### For Content Researcher / Analyst
Analyze news trends and coverage:
```bash
# News statistics by category
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); print('News by Category:'); print(df['Category'].value_counts())"

# Top companies in news
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); print('Top 15 Companies in News:'); print(df['Company matched'].value_counts().head(15))"

# Recent news (last 7 days)
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); df['Publishing Date'] = pd.to_datetime(df['Publishing Date']); recent = df[df['Publishing Date'] >= pd.Timestamp.now() - pd.Timedelta(days=7)]; print(f'News from last 7 days: {len(recent)}'); print(recent[['Company matched', 'Headline', 'Publishing Date', 'Category']])"

# Compare fetcher coverage
python3 -c "import pandas as pd; df = pd.read_excel('companies_news.xlsx'); print('News by Source:'); print(df['Source Skill'].value_counts())"
```

#### For System Administrator / Ops
Monitor system health and run full workflows:
```bash
# Verify all components are ready
python3 test_perplexity_api.py
python3 -c "from config import Config; Config.validate(); Config.display_config()"

# Run complete workflow with both fetchers
python3 .claude/skills/gemini-news-fetcher/fetch_gemini_news.py && \
python3 .claude/skills/bioplastic-news-fetcher-Rev2/fetch_company_news.py && \
python3 .claude/skills/company-enrichment/enrich_companies.py && \
python3 .claude/skills/news-story-generator/generate_news_stories.py

# Check system logs
echo "=== News Generator Errors ===" && tail -20 news_story_generator_errors.log
echo "=== Git Status ===" && git status
echo "=== Recent Stories ===" && ls -lt /home/sven/bioplastic-website/content/news/ | head -5
```
