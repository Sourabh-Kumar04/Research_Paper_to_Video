#!/usr/bin/env python3
"""
Fix Gemini API key loading issue
"""

import os
from pathlib import Path

def check_env_files():
    """Check all .env files for API keys."""
    print("🔍 CHECKING ALL .ENV FILES")
    print("=" * 50)
    
    env_files = [
        ".env",
        ".env.local", 
        ".env.production",
        "src/.env",
        ".env.example"
    ]
    
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"\n📁 Found: {env_file}")
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if 'RASO_GOOGLE_API_KEY' in line:
                    if line.strip().startswith('#'):
                        print(f"   Line {i}: {line.strip()} (COMMENTED)")
                    else:
                        key_part = line.split('=')[1].strip()[:20] if '=' in line else 'invalid'
                        print(f"   Line {i}: RASO_GOOGLE_API_KEY={key_part}... (ACTIVE)")

def fix_env_file():
    """Fix the .env file to ensure new API key is used."""
    print("\n🔧 FIXING .ENV FILE")
    print("=" * 50)
    
    env_file = ".env"
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Remove any old API key lines (commented or not)
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if 'RASO_GOOGLE_API_KEY' in line:
            if line.strip().startswith('#'):
                print(f"Removing commented line: {line.strip()}")
                continue  # Skip commented lines
            else:
                print(f"Found active line: {line.strip()}")
                new_lines.append(line)  # Keep active line
        else:
            new_lines.append(line)
    
    # Write back the cleaned content
    with open(env_file, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Cleaned .env file")

def test_api_key_loading():
    """Test API key loading after fix."""
    print("\n🧪 TESTING API KEY LOADING")
    print("=" * 50)
    
    # Clear any cached environment
    if 'RASO_GOOGLE_API_KEY' in os.environ:
        del os.environ['RASO_GOOGLE_API_KEY']
    
    # Load fresh
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.getenv('RASO_GOOGLE_API_KEY')
    if api_key:
        print(f"✅ API key loaded: {api_key[:20]}...")
        
        # Check if it's the new key
        if api_key.startswith('AIzaSyDA0ep3x07'):
            print("✅ Using NEW API key")
            return True
        elif api_key.startswith('AIzaSyCAxMfE0Y30'):
            print("⚠️ Still using OLD API key")
            return False
        else:
            print("❓ Unknown API key format")
            return False
    else:
        print("❌ No API key found")
        return False

def restart_system():
    """Instructions to restart system."""
    print("\n🔄 RESTART INSTRUCTIONS")
    print("=" * 50)
    print("1. Stop any running backend processes")
    print("2. Close and reopen your terminal/PowerShell")
    print("3. Restart the backend: python start_backend_now.bat")
    print("4. Test video generation again")
    print()
    print("This ensures the new API key is loaded fresh.")

def main():
    """Main fix function."""
    print("🔧 FIXING GEMINI API KEY LOADING")
    print("=" * 60)
    
    # Step 1: Check all env files
    check_env_files()
    
    # Step 2: Fix the main .env file
    fix_env_file()
    
    # Step 3: Test loading
    success = test_api_key_loading()
    
    # Step 4: Provide restart instructions
    restart_system()
    
    print("\n📋 SUMMARY")
    print("=" * 50)
    if success:
        print("✅ New API key is now configured")
        print("🔄 Restart your system to use the new key")
    else:
        print("❌ Still issues with API key loading")
        print("🔧 Manual intervention may be needed")

if __name__ == "__main__":
    main()