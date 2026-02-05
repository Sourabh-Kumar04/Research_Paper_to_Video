#!/usr/bin/env python3
"""Test backend connection and API endpoints"""

import requests
import json

def test_backend():
    """Test if backend is running and responding"""
    backend_url = "http://localhost:8000"
    
    print("="*60)
    print("Testing RASO Backend Connection")
    print("="*60 + "\n")
    
    # Test 1: Health check
    print("Test 1: Health Check Endpoint")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"⚠ Backend responded with status {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is NOT running on port 8000")
        print("   Please start the backend with: npm run start (in src/backend)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print()
    
    # Test 2: API info endpoint
    print("Test 2: API Info Endpoint")
    try:
        response = requests.get(f"{backend_url}/api/v1", timeout=5)
        if response.status_code == 200:
            print("✅ API endpoint is accessible!")
            data = response.json()
            print(f"API Name: {data.get('name')}")
            print(f"Version: {data.get('version')}")
        else:
            print(f"⚠ API responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 3: Jobs endpoint
    print("Test 3: Jobs Endpoint")
    try:
        # Try to submit a test job
        test_payload = {
            "paper_input": {
                "type": "title",
                "content": "Test Paper Title"
            }
        }
        response = requests.post(
            f"{backend_url}/api/v1/jobs",
            json=test_payload,
            timeout=5
        )
        if response.status_code in [200, 201]:
            print("✅ Jobs endpoint is working!")
            data = response.json()
            print(f"Job ID: {data.get('job_id')}")
        else:
            print(f"⚠ Jobs endpoint responded with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Backend Connection Test Complete")
    print("="*60)
    
    return True

if __name__ == "__main__":
    test_backend()
