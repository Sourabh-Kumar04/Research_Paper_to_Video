#!/usr/bin/env python3
"""
Final test of new API key with correct model names
"""

import os

def test_new_api_key():
    """Test new API key with correct models."""
    print("🧪 TESTING NEW GEMINI API KEY")
    print("=" * 50)
    
    # Read API key from .env
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('RASO_GOOGLE_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    print(f"API Key: {api_key[:20]}...")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Try correct model names
        models_to_try = [
            'gemini-2.0-flash-exp',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest',
            'models/gemini-2.0-flash-exp'
        ]
        
        for model_name in models_to_try:
            try:
                print(f"Testing: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say 'New API key works!'")
                print(f"✅ SUCCESS: {response.text}")
                return True
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"❌ Quota exceeded: {model_name}")
                elif "404" in error_msg:
                    print(f"❌ Model not found: {model_name}")
                else:
                    print(f"❌ Error with {model_name}: {error_msg[:50]}...")
        
        print("❌ All models failed")
        return False
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def main():
    """Main test."""
    success = test_new_api_key()
    
    print("\n📋 RESULT")
    print("=" * 30)
    
    if success:
        print("✅ NEW API KEY WORKS!")
        print("🎬 Ready for Gemini-only video generation")
    else:
        print("❌ NEW API KEY HAS ISSUES")
        print("💡 Check:")
        print("   - API key validity")
        print("   - Billing enabled")
        print("   - Quota limits")

if __name__ == "__main__":
    main()