#!/usr/bin/env python3
"""Check job status and get detailed error information."""

import requests
import json

job_id = "d3b34f39-88e6-4e3c-a338-0ba0b28557c1"

try:
    response = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
    if response.status_code == 200:
        data = response.json()
        print("Job Status Details:")
        print(f"  Job ID: {data['job_id']}")
        print(f"  Status: {data['status']}")
        print(f"  Progress: {data['progress']}%")
        print(f"  Current Agent: {data['current_agent']}")
        print(f"  Created: {data['created_at']}")
        print(f"  Updated: {data['updated_at']}")
        
        if data.get('error_message'):
            print(f"  Error: {data['error_message']}")
        
        if data.get('result'):
            print(f"  Result: {data['result']}")
    else:
        print(f"Failed to get job status: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")