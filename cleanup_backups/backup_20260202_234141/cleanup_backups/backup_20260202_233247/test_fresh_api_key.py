#!/usr/bin/env python3
"""
Fresh test of API key without any imports
"""

import os

# Read .env file manually
def read_env_file():
    """Read .env file manually."""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        return env_vars
    except Exception as e:
        print(f"Error reading .env: {e}")
        return {}

def main():
    """Test API key loading."""
    print("🧪 FRESH API KEY TEST")
    print("=" * 40)
    
    # Read .env manually
    env_vars = read_env_file()
    api_key = env_vars.get('RASO_GOOGLE_API_KEY', 'Not found')
    
    print(f"From .env file: {api_key[:20]}...")
    
    # Set in environment
    os.environ['RASO_GOOGLE_API_KEY'] = api_key
    
    # Test with Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Try different models
        models = ['gemini-1.5-flash', 'gemini-1.5-pro']
        
        for model_name in models:
            try:
                print(f"Testing {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hello")
                print(f"✅ {model_name} works: {response.text[:30]}...")
                return True
            except Exception as e:
                print(f"❌ {model_name} failed: {str(e)[:50]}...")
        
        return False
        
    except Exception as e:
        print(f"❌ Import/config failed: {e}")
        return False

if __name__ == "__main__":
    main()