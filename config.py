"""
Configuration module for Bioplastic News Generator
Handles environment variables and configuration settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Configuration class for API keys and settings"""
    
    # API Keys
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    
    # API Endpoints
    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
    
    # Default settings
    DEFAULT_MODEL = "sonar"  # or "sonar-pro" for better quality
    MAX_TOKENS = 2000
    TEMPERATURE = 0.2  # Lower for more focused/factual responses
    
    # News search settings
    DAYS_TO_SEARCH = 7  # Last week
    MAX_RESULTS_PER_COMPANY = 3
    
    # Output settings
    OUTPUT_DIR = Path('./output')
    HUGO_CONTENT_DIR = Path('./content/news')  # Adjust to your Hugo structure
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        if not cls.PERPLEXITY_API_KEY:
            raise ValueError(
                "PERPLEXITY_API_KEY not found! Please:\n"
                "1. Copy .env.example to .env\n"
                "2. Add your Perplexity API key to the .env file\n"
                "3. Never commit the .env file to Git!"
            )
        
        # Create directories if they don't exist
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.HUGO_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        
        return True

    @classmethod
    def display_config(cls):
        """Display current configuration (hiding sensitive data)"""
        print("Current Configuration:")
        print("-" * 40)
        print(f"API Key Set: {'✓' if cls.PERPLEXITY_API_KEY else '✗'}")
        if cls.PERPLEXITY_API_KEY:
            print(f"API Key: {cls.PERPLEXITY_API_KEY[:10]}...{cls.PERPLEXITY_API_KEY[-4:]}")
        print(f"Model: {cls.DEFAULT_MODEL}")
        print(f"Days to Search: {cls.DAYS_TO_SEARCH}")
        print(f"Output Directory: {cls.OUTPUT_DIR}")
        print(f"Hugo Content Directory: {cls.HUGO_CONTENT_DIR}")
        print("-" * 40)
