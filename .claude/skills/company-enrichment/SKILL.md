---
name: company-enrichment
description: Enriches bioplastic company data by automatically filling in missing fields (Type, Country, Description, Primary Materials, Market Segments, Status, Webpage validation) using AI-powered research. Processes companies with incomplete data and validates existing information.
---

# Company Enrichment Skill

Automatically researches and fills in missing company information in `companies.xlsx` using Perplexity AI.

## What It Does

This skill identifies companies with incomplete data and uses AI to research and fill in:

1. **Type** - Company category from predefined list
2. **Country** - Headquarters location
3. **Description** - Brief company overview (2-3 sentences)
4. **Primary Materials** - Specific bioplastics produced/used (PLA, PHA, PBS, etc.)
5. **Market Segments** - Industries served (packaging, agriculture, automotive, etc.)
6. **Status** - Active/Acquired/Defunct/Unknown
7. **Publicly Listed** - Whether company is publicly traded (Yes/No)
8. **Stock Ticker** - Stock exchange symbol if publicly listed
9. **Webpage** - Validates and corrects company website
10. **Date Added** - Timestamp when company was enriched

**Important**: After enrichment, the skill automatically deletes any companies with Type = "Unknown" to maintain database quality.

## Company Type Categories

The skill classifies companies into these categories:

1. **Bioplastic Producer** - Manufactures bioplastic raw materials (resins, polymers)
2. **Compounder** - Blends and compounds bioplastic materials
3. **Converter** - Processes bioplastics into finished products
4. **Technology Company** - Develops bioplastic technologies, patents, processes
5. **Equipment Manufacturer** - Produces machinery for processing bioplastics
6. **Additive Producer** - Manufactures additives for bioplastic formulations
7. **Testing/Certification Company** - Labs for biodegradability testing, certifications
8. **Distributor/Trader** - Distributes/trades bioplastic materials
9. **Recycling Company** - Mechanical or chemical recycling specialists
10. **Waste Management** - Handles biodegradable waste, composting facilities

## How It Works

### Phase 1: Identify Incomplete Records

Scans `companies.xlsx` for companies with empty/missing fields:
- Missing Type
- Missing Country
- Missing Description
- Missing Primary Materials
- Missing Market Segments
- Missing Status

### Phase 2: AI Research

For each incomplete company:

1. **Single API Call** to Perplexity AI requesting:
   - Company type classification
   - Headquarters country
   - Brief description (2-3 sentences)
   - Primary bioplastic materials
   - Target market segments
   - Company status (active/acquired/defunct)
   - Official website verification

2. **Structured JSON Response** with all fields

### Phase 3: Data Validation

- **Type validation**: Must match one of 10 predefined categories
- **Country validation**: Valid country name
- **URL validation**: Checks webpage format and accessibility
- **Status validation**: Active/Acquired/Defunct/Unknown only
- **Description length**: 50-150 words

### Phase 4: Update Database

- Fills in missing fields only (preserves existing data)
- Adds timestamp in "Date Added" field
- Saves updated `companies.xlsx`
- Generates enrichment report

## Usage

Simply say:
- "Run company enrichment"
- "Enrich company data"
- "Fill in missing company information"
- "Update companies.xlsx with missing data"

## Processing Modes

### Mode 1: Incomplete Records Only (Default)
Processes only companies with one or more empty fields.

### Mode 2: Specific Company
Research a single company by name:
- "Enrich data for NatureWorks"
- "Update information for BASF"

### Mode 3: All Companies (Full Refresh)
Re-research all companies to update information:
- "Refresh all company data"
- "Update all companies"

## Example Output

```
======================================================================
🏢 COMPANY ENRICHMENT SKILL
======================================================================

📂 Loading companies.xlsx...
  ✓ Loaded 33 companies
  ⚠️  Found 6 companies with incomplete data

🔍 Enriching company data...

[1/6] Researching: Berry Global
📡 Calling Perplexity API...
✓ Research complete
  Type: Converter
  Country: United States
  Primary Materials: PLA, PHA, Bio-PE
  Market Segments: Packaging, Consumer Products
  Status: Active
  ✓ Updated Berry Global

[2/6] Researching: Roquette Frères
📡 Calling Perplexity API...
✓ Research complete
  Type: Bioplastic Producer
  Country: France
  Primary Materials: Starch-based bioplastics, PLA precursors
  Market Segments: Food Packaging, Agriculture
  Status: Active
  ✓ Updated Roquette Frères

...

💾 Saving results...
  ✓ Updated companies.xlsx

======================================================================
✅ ENRICHMENT COMPLETE!
======================================================================
  Companies processed: 6
  Successfully enriched: 6
  Errors: 0

📊 Category breakdown:
     Bioplastic Producer: 2
     Converter: 2
     Compounder: 1
     Additive Producer: 1
======================================================================
```

## Technical Details

### API Integration
- Uses Perplexity AI `sonar` or `sonar-pro` model
- Single API call per company
- 30-second timeout per request
- Returns structured JSON for reliable parsing

### Error Handling
- Retries on API failures (max 2 retries)
- Falls back to "Unknown" for missing data
- Logs errors to `company_enrichment_errors.log`
- Preserves existing data if API fails

### Data Safety
- **Never overwrites existing data** (only fills empty fields)
- Creates backup before processing (`companies_backup.xlsx`)
- Validates all data before saving
- Rollback capability on errors

### Performance
- Processes ~6-10 companies per minute
- Cost: ~$0.01-0.02 per company (sonar model)
- Can process in batches to manage API rate limits

## Field Descriptions

### Type
One of 10 predefined categories. This categorization helps filter and analyze companies by their role in the bioplastic value chain.

### Country
Headquarters location. Uses full country names (e.g., "United States" not "USA").

### Description
2-3 sentence overview covering:
- What the company does
- Key products or services
- Notable achievements or specialties

### Primary Materials
Specific bioplastics the company works with:
- **Polyesters**: PLA, PHA, PBS, PBAT, PCL
- **Starch-based**: Thermoplastic starch (TPS)
- **Cellulose-based**: Cellulose acetate, regenerated cellulose
- **Bio-PE**: Bio-based polyethylene
- **Bio-PP**: Bio-based polypropylene
- **Bio-PET**: Bio-based polyethylene terephthalate
- **Others**: Chitosan, algae-based, protein-based

### Market Segments
Industries/applications:
- Packaging (rigid, flexible, film)
- Agriculture (mulch film, pots, controlled release)
- Automotive (interior parts, under-hood components)
- Medical (disposables, implants, drug delivery)
- Textiles (fibers, nonwovens)
- Consumer goods (utensils, bottles, bags)
- Electronics (casings, films)
- Construction (insulation, profiles)

### Status
Current operational status:
- **Active**: Currently operating
- **Acquired**: Bought by another company (note parent in Description)
- **Defunct**: No longer operating
- **Unknown**: Status unclear

### Webpage
Official company website. Validates URL format and checks accessibility.

### Publicly Listed
Indicates whether the company is publicly traded on a stock exchange:
- **Yes**: Company is publicly traded and has a stock ticker
- **No**: Private company or not publicly traded

This information is useful for:
- Tracking financial news and quarterly reports
- Monitoring stock price movements related to bioplastic announcements
- Identifying investment opportunities in the sector

### Stock Ticker
Stock exchange symbol for publicly listed companies. Includes exchange prefix when available:
- **NASDAQ:DNMR** - Danimer Scientific (US)
- **NYSE:AMCR** - Amcor (US)
- **FWB:BAS** - BASF (Germany - Frankfurt)
- **TSE:4118** - Kaneka Corporation (Japan - Tokyo)
- **Euronext:CRBN** - Corbion (Netherlands)
- **B3:BRKM5** - Braskem (Brazil)
- **ASX:CNN** - Cardia Bioplastics (Australia)

Empty for private companies.

## Data Quality Management

### Automatic Cleanup
After enrichment, the skill automatically **deletes companies with Type = "Unknown"**. This happens when:
- The company cannot be classified into any of the 10 defined categories
- The entity is not actually a company (e.g., market reports, industry publications)
- Insufficient information exists to determine company type

This ensures the database maintains high quality and only contains actual bioplastic companies.

**Example deletions**:
- "Global Biopolymers Market" - Market research report, not a company
- "Packaging Insights" - News publication, not a bioplastic company
- "PLASTICS" - Industry association, not a company

## Integration with News Fetcher

This skill complements the news fetcher (Rev2):

1. **News Fetcher** discovers new companies → adds to `companies.xlsx` with name only
2. **Company Enrichment** researches new companies → fills in all details
3. **News Fetcher** matches news more accurately with complete company data

## When to Run

- **After news fetching**: When Rev2 adds new companies with incomplete data
- **Database maintenance**: Periodically to keep company information current
- **New imports**: After manually adding company names to the database
- **Data quality checks**: To fill in missing fields from historical records

## Limitations

- Relies on publicly available information
- Some private companies may have limited data
- API may not always find accurate information
- Market segments and materials are best-effort estimates
- Requires manual verification for critical data

## Future Enhancements

1. ~~Add stock ticker lookup for public companies~~ ✅ Implemented
2. Employee count estimation
3. Financial data integration (revenue, funding)
4. Social media profile discovery
5. Key personnel identification
6. Competitor analysis
7. Technology patent search
8. Sustainability certifications lookup
9. Automatic validation of stock tickers via API
10. Historical company status tracking (track acquisitions over time)

## Files

- Main script: `.claude/skills/company-enrichment/enrich_companies.py`
- Input: `companies.xlsx`
- Output: `companies.xlsx` (updated), `companies_backup.xlsx`
- Logs: `company_enrichment_errors.log`

## Configuration

Configurable in `config.py`:
- `ENRICHMENT_BATCH_SIZE`: Companies per batch (default: 10)
- `ENRICHMENT_MODEL`: API model to use (default: "sonar")
- `ENRICHMENT_RETRY_COUNT`: Retry attempts (default: 2)
- `ENRICHMENT_BACKUP`: Create backup before processing (default: True)
