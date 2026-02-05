#!/usr/bin/env python3
"""
Simple test to submit a job and check its status
"""

import requests
import time
import json

def test_job_submission():
    """Test submitting a simple job"""
    print("🧪 Testing Job Submission")
    print("=" * 50)
    
    # Submit a job
    job_data = {
        "paper_input": {
            "type": "title",
            "content": "Test: Simple Video Generation"
        },
        "options": {
            "quality": "low",
            "duration": 30
        }
    }
    
    try:
        print("📤 Submitting job...")
        response = requests.post(
            "http://localhost:8000/api/jobs",
            json=job_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Job submitted successfully")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {result.get('status')}")
            
            # Wait a moment and check status
            time.sleep(3)
            
            print(f"\n📊 Checking job status...")
            status_response = requests.get(
                f"http://localhost:8000/api/jobs/{job_id}",
                timeout=5
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ Job status retrieved")
                print(f"   Status: {status.get('status')}")
                print(f"   Progress: {status.get('progress', 0)}%")
                if status.get('error_message'):
                    print(f"   Error: {status.get('error_message')}")
                if status.get('current_agent'):
                    print(f"   Current Agent: {status.get('current_agent')}")
            else:
                print(f"❌ Failed to get job status: {status_response.status_code}")
                print(f"   Response: {status_response.text}")
                
        else:
            print(f"❌ Job submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_job_submission()
