#!/bin/bash

# Bioplastic News Generator - Setup Script
# This script helps you set up the project safely

echo "======================================"
echo "🌱 Bioplastic News Generator Setup"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

echo "✅ pip3 found"

# Check if .env.example exists
if [ ! -f ".env.example" ]; then
    echo "❌ .env.example not found in current directory."
    echo "   Please run this script from the project root."
    exit 1
fi

# Check if .env already exists
if [ -f ".env" ]; then
    echo ""
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file."
    else
        cp .env.example .env
        echo "✅ Created new .env from .env.example"
    fi
else
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create necessary directories
echo ""
echo "📁 Creating project directories..."
mkdir -p output
mkdir -p content/news
mkdir -p news_cache
echo "✅ Directories created"

# Check if Git is initialized
if [ ! -d ".git" ]; then
    echo ""
    read -p "Initialize Git repository? (Y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        git init
        echo "✅ Git repository initialized"
    fi
fi

# Final instructions
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Add your Perplexity API key to .env:"
echo "   Open .env and replace 'your_actual_api_key_here' with your key"
echo "   Get your key from: https://www.perplexity.ai/settings/api"
echo ""
echo "2. Test the API connection:"
echo "   python3 test_perplexity_api.py"
echo ""
echo "3. Never commit .env to Git!"
echo "   The .gitignore file is already configured to exclude it."
echo ""
echo "======================================"
echo "Happy news aggregating! 🚀"
echo "======================================"
