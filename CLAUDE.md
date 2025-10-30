# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bioplastic News Generator is an automated news aggregator for the bioplastic industry. It uses the Perplexity AI API to search for recent news about bioplastic companies and generates content for a Hugo static site.

The system tracks ~50 bioplastic companies across 5 categories (Producers, Converters, Compounders, Technology/Equipment, Additives) and monitors their news using AI-powered search.

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
- `Companies/bioplastic_companies.json`: Company database with fields:
  - `Name`: Company name
  - `Type`: Producer/Converter/Compounder/Technology/Additive
  - `Website`: Company website
  - `CW-YYYY`: Calendar week tracking (e.g., "CW-42-2025")
  - `News detected`: Empty field for tracking news
  - `Description`: Empty field for company descriptions

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

### Future Development
The README outlines planned features:
1. Main news fetching script (not yet implemented)
2. Hugo templates for news display
3. Automated scheduling (cron jobs)
4. News analytics and filtering
