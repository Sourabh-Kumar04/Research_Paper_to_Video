#!/usr/bin/env python3
"""
Test script to verify the RASO video generation system is working.
"""

import requests
import json
import time

def test_video_generation():
    """Test the video generation API."""
    
    # Test health endpoint
    print("🔍 Testing health endpoint...")
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print("✅ Backend is healthy:", response.json())
    else:
        print("❌ Backend health check failed")
        return False
    
    # Test job submission
    print("\n🚀 Testing video generation job submission...")
    
    job_data = {
        "paper_input": {
            "type": "title",
            "content": "This is a test research paper about artificial intelligence and machine learning. It discusses the latest advances in neural networks and their applications in computer vision and natural language processing."
        },
        "options": {
            "quality": "medium",
            "duration": 60,
            "voice": "default"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/jobs",
            json=job_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            job_info = response.json()
            job_id = job_info.get("job_id")
            print(f"✅ Job submitted successfully! Job ID: {job_id}")
            
            # Monitor job status
            print("\n⏳ Monitoring job status...")
            for i in range(30):  # Check for up to 5 minutes
                status_response = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
                if status_response.status_code == 200:
                    status_info = status_response.json()
                    status = status_info.get("status")
                    progress = status_info.get("progress", 0)
                    current_agent = status_info.get("current_agent", "unknown")
                    
                    print(f"📊 Status: {status}, Progress: {progress}%, Agent: {current_agent}")
                    
                    if status == "completed":
                        print("🎉 Job completed successfully!")
                        
                        # Try to get download info
                        download_response = requests.get(f"http://localhost:8000/api/jobs/{job_id}/download")
                        if download_response.status_code == 200:
                            download_info = download_response.json()
                            print(f"📥 Download available: {download_info}")
                        
                        return True
                    elif status == "failed":
                        error_msg = status_info.get("error_message", "Unknown error")
                        print(f"❌ Job failed: {error_msg}")
                        return False
                    
                    time.sleep(10)  # Wait 10 seconds before checking again
                else:
                    print(f"⚠️ Failed to get job status: {status_response.status_code}")
                    break
            
            print("⏰ Job monitoring timed out")
            return False
            
        else:
            print(f"❌ Job submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing video generation: {e}")
        return False

def test_cinematic_endpoints():
    """Test the cinematic API endpoints."""
    
    print("\n🎬 Testing cinematic API endpoints...")
    
    # Test cinematic settings endpoint
    try:
        response = requests.get("http://localhost:8000/api/v1/cinematic/settings/profiles")
        if response.status_code == 200:
            print("✅ Cinematic profiles endpoint working")
        else:
            print(f"⚠️ Cinematic profiles endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Cinematic profiles endpoint error: {e}")
    
    # Test visual description endpoint
    try:
        test_data = {
            "scene_id": "test-scene",
            "content": "A test scene with mathematical equations and diagrams"
        }
        response = requests.post(
            "http://localhost:8000/api/v1/cinematic/visual-description",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Visual description endpoint working")
        else:
            print(f"⚠️ Visual description endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Visual description endpoint error: {e}")

if __name__ == "__main__":
    print("🧪 RASO System Test")
    print("=" * 50)
    
    # Test basic functionality
    success = test_video_generation()
    
    # Test cinematic features
    test_cinematic_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 RASO system is working correctly!")
    else:
        print("⚠️ RASO system test completed with some issues")
    
    print("\n🌐 You can access:")
    print("  • Backend API: http://localhost:8000")
    print("  • API Documentation: http://localhost:8000/docs")
    print("  • Health Check: http://localhost:8000/health")
    print("\n📝 To start the frontend:")
    print("  cd src/frontend")
    print("  npm start")