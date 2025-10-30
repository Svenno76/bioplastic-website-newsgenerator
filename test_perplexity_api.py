#!/usr/bin/env python3
"""
Test script for Perplexity API
Tests basic connectivity and news search functionality
"""

import json
import requests
from datetime import datetime, timedelta
from config import Config

def test_perplexity_connection():
    """Test basic connection to Perplexity API"""
    try:
        # Validate configuration
        Config.validate()
        Config.display_config()
        
        print("\n🔍 Testing Perplexity API Connection...")
        
        # Prepare test query
        test_query = "What are the latest developments in bioplastics industry in the last week?"
        
        headers = {
            "Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": Config.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides concise, factual information about recent bioplastics industry news."
                },
                {
                    "role": "user",
                    "content": test_query
                }
            ],
            "max_tokens": Config.MAX_TOKENS,
            "temperature": Config.TEMPERATURE,
            "return_citations": True,  # Important for news credibility
            "return_images": False,
            "return_related_questions": False,
            "stream": False
        }
        
        print(f"📡 Sending request to: {Config.PERPLEXITY_API_URL}")
        print(f"📝 Test query: {test_query}\n")
        
        response = requests.post(
            Config.PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Check response status
        if response.status_code == 200:
            print("✅ API Connection Successful!\n")
            
            data = response.json()
            
            # Display the response
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print("📰 API Response:")
                print("-" * 60)
                print(content)
                print("-" * 60)
                
                # Check for citations
                if 'citations' in data:
                    print(f"\n📚 Citations provided: {len(data.get('citations', []))} sources")
                
                # Display usage stats if available
                if 'usage' in data:
                    print(f"\n📊 Token Usage:")
                    print(f"   Prompt tokens: {data['usage'].get('prompt_tokens', 'N/A')}")
                    print(f"   Completion tokens: {data['usage'].get('completion_tokens', 'N/A')}")
                    print(f"   Total tokens: {data['usage'].get('total_tokens', 'N/A')}")
                
                # Save test response for debugging
                with open('test_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("\n💾 Full response saved to: test_response.json")
                
                return True
            else:
                print("⚠️ Unexpected response structure:")
                print(json.dumps(data, indent=2))
                return False
                
        elif response.status_code == 401:
            print("❌ Authentication Failed!")
            print("   Please check your API key in the .env file")
            return False
            
        elif response.status_code == 429:
            print("⚠️ Rate limit exceeded!")
            print("   Please wait a moment before trying again")
            return False
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Please check your internet connection.")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Perplexity API. Please check your internet connection.")
        return False
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_company_news_search():
    """Test searching for specific company news"""
    try:
        print("\n\n🏭 Testing Company-Specific News Search...")
        
        # Test with a major bioplastic company
        company = "NatureWorks"
        
        # Create a more specific query
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        query = f"""
        Find recent news about {company} bioplastics company from the last week.
        Focus on: new products, partnerships, investments, research developments, or market expansions.
        Provide factual information with dates if available.
        Time period: {week_ago.strftime('%B %d')} to {today.strftime('%B %d, %Y')}
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
                    "content": "You are a bioplastics industry news researcher. Provide factual, dated information from reliable sources."
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
        
        print(f"🔍 Searching news for: {company}")
        print(f"📅 Time period: Last 7 days\n")
        
        response = requests.post(
            Config.PERPLEXITY_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"📰 News for {company}:")
                print("-" * 60)
                print(content)
                print("-" * 60)
                
                # Save company test
                with open(f'test_{company.lower()}_news.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"\n💾 Response saved to: test_{company.lower()}_news.json")
                
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error in company news search: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 PERPLEXITY API TEST SUITE")
    print("=" * 70)
    
    # First, check if .env file exists
    from pathlib import Path
    
    if not Path('.env').exists():
        print("\n⚠️  No .env file found!")
        print("\n📝 Instructions:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("\n2. Edit .env and add your Perplexity API key:")
        print("   PERPLEXITY_API_KEY=your_actual_key_here")
        print("\n3. Get your API key from: https://www.perplexity.ai/settings/api")
        print("\n4. Run this test again")
        exit(1)
    
    # Run tests
    connection_test = test_perplexity_connection()
    
    if connection_test:
        company_test = test_company_news_search()
        
        if company_test:
            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED!")
            print("=" * 70)
            print("\nYour Perplexity API is working correctly!")
            print("You can now proceed with building the news generator.")
        else:
            print("\n⚠️ Company search test failed, but basic API works.")
    else:
        print("\n❌ Connection test failed. Please check your API key and internet connection.")
