# 🌱 Bioplastic News Generator

An automated news aggregator for bioplastic industry updates, powered by Perplexity AI and integrated with Hugo static site generator.

## 📋 Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Git (for version control)
- Hugo (for your website)
- Perplexity API key

### 2. Installation

1. **Clone or create your repository:**
   ```bash
   git init bioplastic-news-generator
   cd bioplastic-news-generator
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   
   a. Get your Perplexity API key:
      - Go to https://www.perplexity.ai/settings/api
      - Generate an API key
   
   b. Copy the example environment file:
      ```bash
      cp .env.example .env
      ```
   
   c. Edit `.env` and add your API key:
      ```
      PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx
      ```

4. **Test the API connection:**
   ```bash
   python test_perplexity_api.py
   ```

### 3. 🔒 Security Best Practices

- **NEVER commit `.env` to Git** - it's already in `.gitignore`
- Keep your API keys secret
- Use environment variables for all sensitive data
- Regularly rotate your API keys
- Monitor your API usage to detect any unauthorized access

### 4. 📁 Project Structure

```
bioplastic-news-generator/
│
├── .env                    # Your API keys (NEVER commit this!)
├── .env.example           # Template for environment variables
├── .gitignore            # Files to exclude from Git
├── config.py             # Configuration module
├── requirements.txt      # Python dependencies
├── test_perplexity_api.py # API test script
│
├── bioplastic_companies.json  # Company database (JSON)
├── bioplastic_companies.csv   # Company database (CSV)
├── bioplastic_companies.xlsx  # Company database (Excel)
│
├── output/               # Generated news output
│   └── ...
│
└── content/news/        # Hugo content directory
    └── ...
```

### 5. 🚀 Quick Start

1. Set up your `.env` file with the API key
2. Run the test script: `python test_perplexity_api.py`
3. If tests pass, you're ready to build the news generator!

### 6. 🛡️ Git Commands for Safe Commits

Before committing, always check you're not including sensitive data:

```bash
# Check what files will be committed
git status

# Verify .env is NOT in the list
# If .env appears, make sure .gitignore is working

# Add files (but not .env!)
git add .
git status  # Double-check .env is not staged

# Commit
git commit -m "Add news generator setup"

# If you accidentally staged .env:
git reset HEAD .env
```

### 7. 📊 Available Company Data

The project includes a database of 50 bioplastic companies in 5 categories:
- **Bioplastic Producers** (15 companies)
- **Converters** (12 companies)
- **Compounders** (8 companies)
- **Technology/Equipment Companies** (8 companies)
- **Additive Producers** (7 companies)

### 8. 🔍 API Models

Perplexity offers different models:
- `sonar` - Faster, cost-effective (default)
- `sonar-pro` - Higher quality responses

Update the model in `config.py` based on your needs and budget.

### 9. ⚠️ Troubleshooting

**API Key Not Found:**
- Make sure `.env` file exists
- Check the key name is exactly `PERPLEXITY_API_KEY`
- Ensure no extra spaces or quotes around the key

**Rate Limiting:**
- Perplexity has rate limits
- Add delays between requests if processing many companies
- Consider upgrading your API plan for higher limits

**No News Found:**
- Some companies may not have recent news
- Try adjusting the time period in config.py
- Consider using more general search terms

### 10. 📝 Next Steps

1. ✅ Set up environment and test API
2. 🔄 Build the main news fetching script
3. 🎨 Create Hugo templates for news display
4. ⏰ Set up automated scheduling (cron job)
5. 📊 Add news analytics and filtering

## 📄 License

Your license here

## 🤝 Contributing

Contributions welcome! Please ensure you never commit API keys or sensitive data.

---

**Remember:** Keep your API keys secret and never commit them to version control!
