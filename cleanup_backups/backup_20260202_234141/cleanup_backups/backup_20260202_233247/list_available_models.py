#!/usr/bin/env python3
"""
List available Gemini models for your API key
"""

import os

def list_available_models():
    """List all available models."""
    print("🔍 LISTING AVAILABLE GEMINI MODELS")
    print("=" * 60)
    
    # Read API key
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('RASO_GOOGLE_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    print(f"API Key: {api_key[:20]}...")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        print("Available models:")
        models = genai.list_models()
        
        working_models = []
        for model in models:
            print(f"📋 {model.name}")
            
            # Try to use each model
            try:
                test_model = genai.GenerativeModel(model.name)
                response = test_model.generate_content("Hi")
                print(f"   ✅ WORKS: {response.text[:30]}...")
                working_models.append(model.name)
            except Exception as e:
                if "429" in str(e):
                    print(f"   ❌ QUOTA EXCEEDED")
                else:
                    print(f"   ❌ ERROR: {str(e)[:50]}...")
        
        return working_models
        
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return []

def main():
    """Main function."""
    working_models = list_available_models()
    
    print("\n📋 SUMMARY")
    print("=" * 40)
    
    if working_models:
        print(f"✅ FOUND {len(working_models)} WORKING MODELS:")
        for model in working_models:
            print(f"   - {model}")
        print("\n🔧 Update .env to use a working model:")
        print(f"   RASO_GOOGLE_MODEL={working_models[0]}")
    else:
        print("❌ NO WORKING MODELS FOUND")
        print("🚨 ALL MODELS HIT QUOTA LIMITS")
        print("\n💡 SOLUTIONS:")
        print("   1. ⏰ Wait 24 hours for quota reset")
        print("   2. 💳 Enable billing on Google Cloud Console")
        print("   3. 👤 Use different Google account")
        print("   4. 🔄 Try again tomorrow")

if __name__ == "__main__":
    main()