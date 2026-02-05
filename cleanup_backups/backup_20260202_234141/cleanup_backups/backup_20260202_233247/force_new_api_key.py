#!/usr/bin/env python3
"""
Force load new API key and test
"""

import os
import sys
from pathlib import Path

def force_reload_env():
    """Force reload environment variables."""
    print("🔄 FORCE RELOADING ENVIRONMENT")
    print("=" * 50)
    
    # Clear any existing environment variables
    env_vars_to_clear = [
        'RASO_GOOGLE_API_KEY',
        'RASO_GOOGLE_MODEL',
        'RASO_LLM_PROVIDER'
    ]
    
    for var in env_vars_to_clear:
        if var in os.environ:
            print(f"Clearing cached: {var}")
            del os.environ[var]
    
    # Force reload from .env file
    from dotenv import load_dotenv
    load_dotenv(override=True, verbose=True)
    
    # Check what was loaded
    api_key = os.getenv('RASO_GOOGLE_API_KEY')
    if api_key:
        print(f"✅ Loaded API key: {api_key[:20]}...")
        
        if api_key.startswith('AIzaSyDA0ep3x07'):
            print("✅ SUCCESS: Using NEW API key!")
            return True
        else:
            print("❌ ERROR: Still using old API key")
            return False
    else:
        print("❌ ERROR: No API key loaded")
        return False

def test_new_api_key():
    """Test the new API key."""
    print("\n🧪 TESTING NEW API KEY")
    print("=" * 50)
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('RASO_GOOGLE_API_KEY')
        
        # Configure with new key
        genai.configure(api_key=api_key)
        
        # Try with a different model to avoid quota issues
        models_to_try = [
            'gemini-1.5-flash',
            'gemini-1.5-pro', 
            'gemini-2.0-flash-exp'
        ]
        
        for model_name in models_to_try:
            try:
                print(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content("Say 'New API key works'")
                print(f"✅ SUCCESS with {model_name}: {response.text}")
                return True
                
            except Exception as e:
                print(f"❌ Failed with {model_name}: {str(e)[:100]}...")
                continue
        
        print("❌ All models failed")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main function."""
    print("🔧 FORCING NEW GEMINI API KEY")
    print("=" * 60)
    
    # Step 1: Force reload environment
    env_success = force_reload_env()
    
    if not env_success:
        print("\n❌ FAILED: Could not load new API key")
        return
    
    # Step 2: Test new API key
    api_success = test_new_api_key()
    
    print("\n📋 FINAL RESULT")
    print("=" * 50)
    
    if api_success:
        print("✅ SUCCESS: New API key is working!")
        print("🎬 You can now generate videos with Gemini")
    else:
        print("❌ FAILED: New API key has issues")
        print("💡 Possible causes:")
        print("   - New API key also has quota limits")
        print("   - New API key is from same Google project")
        print("   - New API key needs billing enabled")
        print("   - Account-level quota restrictions")

if __name__ == "__main__":
    main()