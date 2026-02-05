#!/usr/bin/env python3
"""
Test the download endpoint to see what's being served
"""

import requests
import sys

# Get the most recent job ID
job_id = "7e327548-62d4-4af0-8cb2-bb70a88deb9d"

print(f"Testing download for job: {job_id}")
print("=" * 80)

# Test the download endpoint
url = f"http://localhost:8000/api/v1/jobs/{job_id}/download"
print(f"Requesting: {url}")

try:
    response = requests.get(url, stream=True)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        # Get content length
        content_length = int(response.headers.get('Content-Length', 0))
        print(f"\n✅ Download successful!")
        print(f"Content-Length: {content_length} bytes ({content_length / 1024 / 1024:.2f} MB)")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        # Check if it's a real video (> 1MB)
        if content_length > 1000000:
            print(f"✅ This is a REAL video (> 1MB)")
        else:
            print(f"❌ This looks like a PLACEHOLDER (< 1MB)")
            
        # Save first 1KB to check
        first_kb = response.raw.read(1024)
        if b'ftyp' in first_kb or b'moov' in first_kb:
            print(f"✅ Valid MP4 file signature detected")
        else:
            print(f"❌ Invalid MP4 file signature")
            
    else:
        print(f"❌ Download failed!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
