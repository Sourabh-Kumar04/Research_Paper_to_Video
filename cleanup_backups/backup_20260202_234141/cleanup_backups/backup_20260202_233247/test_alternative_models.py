#!/usr/bin/env python3
"""
Test alternative Gemini models that might have separate quotas
"""

import os

def test_alternative_models():
    """Test different Gemini models."""
    print("🧪 TESTING ALTERNATIVE GEMINI MODELS")
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
        
        # Try different models that might have separate quotas
        models_to_try = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
            'gemini-pro-vision',
            'text-bison-001',
            'chat-bison-001'
        ]
        
        for model_name in models_to_try:
            try:
                print(f"Testing: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hello, just say 'working'")
                print(f"✅ SUCCESS: {model_name} - {response.text}")
                return model_name
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    print(f"❌ Quota exceeded: {model_name}")
                elif "404" in error_msg:
                    print(f"❌ Not found: {model_name}")
                elif "400" in error_msg:
                    print(f"❌ Bad request: {model_name}")
                else:
                    print(f"❌ Error: {model_name} - {error_msg[:50]}...")
        
        print("❌ All alternative models failed")
        return None
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return None

def main():
    """Main test."""
    working_model = test_alternative_models()
    
    print("\n📋 RESULT")
    print("=" * 30)
    
    if working_model:
        print(f"✅ FOUND WORKING MODEL: {working_model}")
        print("🔧 Update your .env file to use this model")
        print(f"   RASO_GOOGLE_MODEL={working_model}")
    else:
        print("❌ NO WORKING MODELS FOUND")
        print("💡 Solutions:")
        print("   1. Wait 24 hours for quota reset")
        print("   2. Enable billing on Google Cloud")
        print("   3. Use different Google account")

if __name__ == "__main__":
    main()