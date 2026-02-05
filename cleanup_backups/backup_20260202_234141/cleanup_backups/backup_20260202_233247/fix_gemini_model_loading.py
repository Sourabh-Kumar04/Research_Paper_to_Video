#!/usr/bin/env python3
"""
Fix Gemini model loading issue - force correct environment loading
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def fix_gemini_model_loading():
    """Fix the Gemini model loading issue."""
    
    print("🔧 FIXING GEMINI MODEL LOADING ISSUE")
    print("=" * 60)
    
    # Clear any existing environment variables
    env_vars_to_clear = [
        'RASO_GOOGLE_MODEL',
        'RASO_SCRIPT_LLM_MODEL', 
        'RASO_MANIM_LLM_MODEL',
        'RASO_ANALYSIS_LLM_MODEL'
    ]
    
    print("🧹 CLEARING EXISTING ENVIRONMENT VARIABLES:")
    for var in env_vars_to_clear:
        if var in os.environ:
            old_value = os.environ[var]
            del os.environ[var]
            print(f"  ❌ Cleared {var}: {old_value}")
        else:
            print(f"  ✅ {var}: Not set")
    
    print()
    
    # Force reload .env file
    print("📁 FORCE RELOADING .env FILE:")
    env_file = Path('.env')
    if env_file.exists():
        print(f"  ✅ Found .env file: {env_file.absolute()}")
        
        # Load with override=True to force reload
        load_dotenv(env_file, override=True)
        print("  ✅ Reloaded .env file with override=True")
    else:
        print("  ❌ .env file not found!")
        return False
    
    print()
    
    # Verify new values
    print("🔍 VERIFYING NEW ENVIRONMENT VARIABLES:")
    for var in env_vars_to_clear:
        value = os.getenv(var, 'NOT SET')
        print(f"  {var}: {value}")
    
    print()
    
    # Test Gemini client with new values
    print("🤖 TESTING GEMINI CLIENT WITH NEW VALUES:")
    
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        from llm.gemini_client import GeminiClient
        
        # Create new client instance
        client = GeminiClient()
        
        print(f"  Default model: {client.default_model}")
        print(f"  Script model: {client.script_model}")
        print(f"  Manim model: {client.manim_model}")
        print(f"  Analysis model: {client.analysis_model}")
        
        # Check if we're using Gemma models
        if 'gemma' in client.manim_model.lower():
            print("  ✅ SUCCESS: Using Gemma model!")
            return True
        else:
            print("  ❌ FAILURE: Still using old model")
            return False
            
    except Exception as e:
        print(f"  ❌ Error creating Gemini client: {e}")
        return False

def update_env_file_directly():
    """Directly update the .env file to ensure correct values."""
    
    print("📝 UPDATING .env FILE DIRECTLY:")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("  ❌ .env file not found!")
        return False
    
    # Read current content
    content = env_file.read_text()
    
    # Replace old model references
    replacements = {
        'RASO_GOOGLE_MODEL=gemini-2.0-flash-exp': 'RASO_GOOGLE_MODEL=models/gemma-3-27b-it',
        'RASO_SCRIPT_LLM_MODEL=gemini-2.0-flash-exp': 'RASO_SCRIPT_LLM_MODEL=models/gemma-3-27b-it',
        'RASO_MANIM_LLM_MODEL=gemini-2.0-flash-exp': 'RASO_MANIM_LLM_MODEL=models/gemma-3-27b-it',
        'RASO_ANALYSIS_LLM_MODEL=gemini-2.0-flash-exp': 'RASO_ANALYSIS_LLM_MODEL=models/gemma-3-27b-it'
    }
    
    updated = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            updated = True
            print(f"  ✅ Updated: {old} → {new}")
    
    if updated:
        # Write back to file
        env_file.write_text(content)
        print("  ✅ .env file updated successfully")
        return True
    else:
        print("  ✅ .env file already has correct values")
        return True

if __name__ == "__main__":
    print("🚀 STARTING GEMINI MODEL FIX")
    print("=" * 60)
    
    # Step 1: Update .env file directly
    env_updated = update_env_file_directly()
    print()
    
    # Step 2: Fix environment loading
    if env_updated:
        model_fixed = fix_gemini_model_loading()
        
        print()
        print("📋 FINAL RESULTS:")
        print("=" * 60)
        
        if model_fixed:
            print("✅ SUCCESS: Gemini model loading fixed!")
            print("✅ System now configured to use Gemma models")
            print("✅ Ready to test video generation")
        else:
            print("❌ FAILURE: Model loading still has issues")
            print("❌ Manual intervention may be required")
    else:
        print("❌ FAILURE: Could not update .env file")