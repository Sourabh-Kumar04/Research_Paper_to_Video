#!/usr/bin/env python3
"""
Test new Gemini API key with both old and new packages
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_old_gemini_package():
    """Test with old google.generativeai package."""
    print("🧪 TESTING OLD GEMINI PACKAGE (google.generativeai)")
    print("=" * 60)
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('RASO_GOOGLE_API_KEY')
        if not api_key:
            print("❌ No API key found")
            return False
        
        print(f"✅ API key loaded: {api_key[:10]}...")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Try to create a model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✅ Model created successfully")
        
        # Try a simple generation
        response = model.generate_content("Say hello")
        print(f"✅ Generation successful: {response.text[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Old package failed: {e}")
        return False

def test_new_gemini_package():
    """Test with new google.genai package."""
    print("\n🧪 TESTING NEW GEMINI PACKAGE (google.genai)")
    print("=" * 60)
    
    try:
        import google.genai as genai
        
        api_key = os.getenv('RASO_GOOGLE_API_KEY')
        if not api_key:
            print("❌ No API key found")
            return False
        
        print(f"✅ API key loaded: {api_key[:10]}...")
        
        # Configure client
        client = genai.Client(api_key=api_key)
        print("✅ Client created successfully")
        
        # Try a simple generation
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents="Say hello"
        )
        print(f"✅ Generation successful: {response.text[:50]}...")
        
        return True
        
    except ImportError:
        print("❌ New package not installed (google.genai)")
        return False
    except Exception as e:
        print(f"❌ New package failed: {e}")
        return False

def main():
    """Test both packages."""
    print("🔍 TESTING GEMINI API KEY WITH BOTH PACKAGES")
    print("=" * 70)
    
    old_works = test_old_gemini_package()
    new_works = test_new_gemini_package()
    
    print("\n📋 TEST RESULTS")
    print("=" * 50)
    
    if old_works:
        print("✅ OLD PACKAGE WORKS: google.generativeai")
    else:
        print("❌ OLD PACKAGE FAILED: google.generativeai")
    
    if new_works:
        print("✅ NEW PACKAGE WORKS: google.genai")
    else:
        print("❌ NEW PACKAGE FAILED: google.genai")
    
    print("\n💡 RECOMMENDATION:")
    if old_works and not new_works:
        print("🔧 Continue using old package (google.generativeai)")
        print("📝 Your API key works with the current system")
    elif new_works:
        print("🔧 Upgrade to new package (google.genai)")
        print("📝 Install: pip install google-genai")
    else:
        print("❌ API key may be invalid or quota exceeded")
        print("📝 Check your Gemini API console")

if __name__ == "__main__":
    main()