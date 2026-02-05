#!/usr/bin/env python3
"""
Test what's running on port 3000
"""

import requests

print("Testing localhost:3000...")
print("=" * 80)

try:
    response = requests.get("http://localhost:3000", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content length: {len(response.text)} bytes")
    print("\nFirst 500 characters:")
    print(response.text[:500])
    
    # Check if it's the React app
    if "react" in response.text.lower() or "raso" in response.text.lower():
        print("\n✅ This is the RASO React frontend")
    else:
        print("\n❓ Unknown application")
        
except Exception as e:
    print(f"❌ Error: {e}")
