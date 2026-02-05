#!/usr/bin/env python3
"""
Simple test of new Gemini API key
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_gemini_api():
    """Test Gemini API with current setup."""
    print("🧪 TESTING GEMINI API")
    print("=" * 40)
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('RASO_GOOGLE_API_KEY')
        print(f"API Key: {api_key[:15]}...")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Create model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Simple test
        print("Testing simple generation...")
        response = model.generate_content("Hello, respond with just 'API works'")
        
        print(f"✅ SUCCESS: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_gemini_api()