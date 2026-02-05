#!/usr/bin/env python3
"""
Test if Gemini can be imported and initialized
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=True)

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("=" * 80)
print("TESTING GEMINI IMPORT AND INITIALIZATION")
print("=" * 80)

# Check API key
api_key = os.getenv('RASO_GOOGLE_API_KEY')
print(f"\n1. API Key Check:")
if api_key:
    print(f"   ✅ API key found: {api_key[:10]}...")
    print(f"   Length: {len(api_key)}")
    print(f"   Starts with 'AIza': {api_key.startswith('AIza')}")
else:
    print(f"   ❌ API key NOT found!")

# Try to import Gemini client
print(f"\n2. Import Test:")
try:
    from llm.gemini_client import GeminiClient, get_gemini_client
    print(f"   ✅ Gemini client imported successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to initialize Gemini client
print(f"\n3. Initialization Test:")
try:
    client = get_gemini_client()
    print(f"   ✅ Gemini client initialized successfully")
    print(f"   Model: {client.default_model}")
    print(f"   Script model: {client.script_model}")
    print(f"   Manim model: {client.manim_model}")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to generate Manim code
print(f"\n4. Manim Code Generation Test:")
try:
    import asyncio
    
    async def test_manim_generation():
        code = await client.generate_manim_code(
            "Test Scene",
            "This is a test scene description",
            10.0
        )
        return code
    
    manim_code = asyncio.run(test_manim_generation())
    print(f"   ✅ Manim code generated successfully")
    print(f"   Code length: {len(manim_code)} characters")
    print(f"\n   First 500 characters:")
    print(f"   {manim_code[:500]}")
except Exception as e:
    print(f"   ❌ Manim generation failed: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
