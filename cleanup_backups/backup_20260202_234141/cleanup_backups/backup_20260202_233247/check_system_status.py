#!/usr/bin/env python3
"""
System Status Check - Verify Gemini is available
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def check_system_status():
    """Check if system is operational (Gemini available)."""
    
    print("🔍 CHECKING SYSTEM STATUS")
    print("=" * 50)
    
    # Check Gemini API key
    gemini_api_key = os.getenv('RASO_GOOGLE_API_KEY')
    if not gemini_api_key:
        print("❌ SYSTEM DOWN: Gemini API key not configured")
        return False
    
    if not (gemini_api_key.startswith('AIza') or len(gemini_api_key) > 30):
        print("❌ SYSTEM DOWN: Invalid Gemini API key format")
        return False
    
    print(f"✅ Gemini API key configured: {gemini_api_key[:10]}...")
    
    # Try to import and initialize Gemini client
    try:
        from llm.gemini_client import GeminiClient, get_gemini_client
        client = get_gemini_client()
        print("✅ Gemini client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ SYSTEM DOWN: Gemini client failed to initialize: {e}")
        return False

if __name__ == "__main__":
    is_operational = check_system_status()
    
    print("\n" + "=" * 50)
    if is_operational:
        print("✅ SYSTEM OPERATIONAL: Gemini AI service is available")
        print("🎬 Video generation will use Gemini-generated Manim code")
    else:
        print("❌ SYSTEM DOWN: Gemini AI service is not available")
        print("🚫 Video generation is disabled until Gemini is restored")
    
    sys.exit(0 if is_operational else 1)
