#!/usr/bin/env python3
"""
Debug script to check what Gemini model is actually being loaded
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def debug_gemini_model():
    """Debug what model is being loaded."""
    
    print("🔍 DEBUGGING GEMINI MODEL CONFIGURATION")
    print("=" * 60)
    
    # Check environment variables
    print("📋 ENVIRONMENT VARIABLES:")
    print(f"RASO_GOOGLE_MODEL: {os.getenv('RASO_GOOGLE_MODEL', 'NOT SET')}")
    print(f"RASO_SCRIPT_LLM_MODEL: {os.getenv('RASO_SCRIPT_LLM_MODEL', 'NOT SET')}")
    print(f"RASO_MANIM_LLM_MODEL: {os.getenv('RASO_MANIM_LLM_MODEL', 'NOT SET')}")
    print(f"RASO_ANALYSIS_LLM_MODEL: {os.getenv('RASO_ANALYSIS_LLM_MODEL', 'NOT SET')}")
    print(f"RASO_GOOGLE_API_KEY: {os.getenv('RASO_GOOGLE_API_KEY', 'NOT SET')[:20]}...")
    print()
    
    # Check Gemini client initialization
    try:
        from llm.gemini_client import GeminiClient
        
        print("🤖 GEMINI CLIENT INITIALIZATION:")
        client = GeminiClient()
        
        print(f"Default model: {client.default_model}")
        print(f"Script model: {client.script_model}")
        print(f"Manim model: {client.manim_model}")
        print(f"Analysis model: {client.analysis_model}")
        print(f"API key: {client.api_key[:20]}...")
        print()
        
        # Test if models are working
        print("🧪 TESTING MODEL ACCESS:")
        
        import google.generativeai as genai
        
        # List available models
        print("Available models:")
        try:
            models = genai.list_models()
            for model in models:
                if 'gemma' in model.name.lower():
                    print(f"  ✅ {model.name}")
                elif 'gemini' in model.name.lower():
                    print(f"  🔵 {model.name}")
        except Exception as e:
            print(f"  ❌ Error listing models: {e}")
        
        print()
        
        # Test specific model
        print(f"🎯 TESTING CONFIGURED MODEL: {client.manim_model}")
        try:
            model = genai.GenerativeModel(model_name=client.manim_model)
            print("  ✅ Model initialized successfully")
            
            # Try a simple generation
            response = model.generate_content("Say hello")
            if response.text:
                print(f"  ✅ Model response: {response.text[:50]}...")
            else:
                print("  ❌ Empty response from model")
                
        except Exception as e:
            print(f"  ❌ Model test failed: {e}")
        
    except Exception as e:
        print(f"❌ Gemini client initialization failed: {e}")

if __name__ == "__main__":
    debug_gemini_model()