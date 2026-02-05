#!/usr/bin/env python3
"""
Test script to verify frontend-backend integration
Tests that both services are running and can communicate
"""

import requests
import time
import json

def test_backend_health():
    """Test that backend is healthy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_frontend_accessibility():
    """Test that frontend is accessible"""
    try:
        response = requests.get("http://localhost:3002", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend accessibility failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend accessibility failed: {e}")
        return False

def test_api_job_submission():
    """Test job submission through backend API"""
    try:
        job_data = {
            "paper_input": {
                "type": "title",
                "content": "Test Integration: AI-Powered Video Generation"
            },
            "options": {
                "quality": "medium",
                "duration": 60
            }
        }
        
        response = requests.post(
            "http://localhost:8000/api/jobs",
            json=job_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Job submission successful")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Status: {result.get('status')}")
            return True, result.get('job_id')
        else:
            print(f"❌ Job submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Job submission failed: {e}")
        return False, None

def test_job_status_check(job_id):
    """Test job status checking"""
    if not job_id:
        return False
        
    try:
        response = requests.get(f"http://localhost:8000/api/jobs/{job_id}", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ Job status check successful")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Progress: {result.get('progress', 0)}%")
            return True
        else:
            print(f"❌ Job status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Job status check failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 Running Frontend-Backend Integration Tests")
    print("=" * 50)
    
    # Test backend health
    backend_ok = test_backend_health()
    
    # Test frontend accessibility
    frontend_ok = test_frontend_accessibility()
    
    # Test API functionality
    api_ok = False
    job_id = None
    if backend_ok:
        api_ok, job_id = test_api_job_submission()
        
        if api_ok and job_id:
            # Wait a moment then check job status
            time.sleep(2)
            test_job_status_check(job_id)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Backend Health: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"   Frontend Access: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"   API Functionality: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if backend_ok and frontend_ok and api_ok:
        print("\n🎉 All tests passed! Frontend and backend are working together.")
        print("   You can now:")
        print("   • Open http://localhost:3002 in your browser")
        print("   • Submit video generation jobs through the UI")
        print("   • Monitor job progress in real-time")
    else:
        print("\n⚠️  Some tests failed. Please check the services.")

if __name__ == "__main__":
    main()