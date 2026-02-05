#!/usr/bin/env python3
"""
Submit a test job through the frontend API to see what happens
"""

import requests
import json
import time

print("Testing job submission through API...")
print("=" * 80)

# Submit a job
url = "http://localhost:8000/api/v1/jobs"
payload = {
    "paper_input": {
        "type": "title",
        "content": "Test Paper for API Verification"
    },
    "options": {
        "quality": "medium",
        "duration": 120
    }
}

print(f"POST {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        job_id = response.json().get('job_id')
        print(f"\n✅ Job created: {job_id}")
        print(f"\nYou can check status at:")
        print(f"  http://localhost:8000/api/v1/jobs/{job_id}")
        print(f"\nYou can download at:")
        print(f"  http://localhost:8000/api/v1/jobs/{job_id}/download")
        
        # Wait a bit and check status
        print(f"\nWaiting 5 seconds to check initial status...")
        time.sleep(5)
        
        status_response = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
        print(f"\nStatus: {json.dumps(status_response.json(), indent=2)}")
    else:
        print(f"\n❌ Job submission failed")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
