#!/usr/bin/env python3
"""
End-to-end test with "Attention Is All You Need" paper
"""

import requests
import time
import json

def test_attention_paper():
    """Test with the actual Attention Is All You Need paper"""
    print("🧪 Testing: Attention Is All You Need Paper")
    print("=" * 60)
    
    # Submit job with the paper title
    job_data = {
        "paper_input": {
            "type": "title",
            "content": "Attention Is All You Need"
        },
        "options": {
            "quality": "medium",
            "duration": 120
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
            
            # Monitor job progress
            print(f"\n📊 Monitoring job progress...")
            print("-" * 60)
            
            max_checks = 120  # 20 minutes max
            check_count = 0
            last_status = None
            last_agent = None
            
            while check_count < max_checks:
                time.sleep(10)  # Check every 10 seconds
                check_count += 1
                
                try:
                    status_response = requests.get(
                        f"http://localhost:8000/api/jobs/{job_id}",
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        current_status = status.get('status')
                        current_agent = status.get('current_agent')
                        progress = status.get('progress', 0)
                        
                        # Only print if something changed
                        if current_status != last_status or current_agent != last_agent:
                            print(f"[{check_count}] Status: {current_status} | "
                                  f"Agent: {current_agent} | Progress: {progress:.1f}%")
                            last_status = current_status
                            last_agent = current_agent
                        
                        # Check if job is complete or failed
                        if current_status == 'completed':
                            print("\n" + "=" * 60)
                            print("🎉 Job completed successfully!")
                            print(f"   Final progress: {progress}%")
                            
                            # Try to get download info
                            download_response = requests.get(
                                f"http://localhost:8000/api/jobs/{job_id}/download",
                                timeout=5
                            )
                            if download_response.status_code == 200:
                                download_info = download_response.json()
                                print(f"   Download URL: {download_info.get('download_url')}")
                            
                            return True
                            
                        elif current_status == 'failed':
                            print("\n" + "=" * 60)
                            print("❌ Job failed!")
                            error_msg = status.get('error_message', 'Unknown error')
                            print(f"   Error: {error_msg}")
                            print(f"   Last agent: {current_agent}")
                            print(f"   Progress: {progress}%")
                            return False
                            
                    else:
                        print(f"⚠️  Failed to get status: {status_response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️  Error checking status: {e}")
                    
            print("\n" + "=" * 60)
            print("⏱️  Timeout: Job did not complete within 20 minutes")
            return False
                
        else:
            print(f"❌ Job submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_attention_paper()
    exit(0 if success else 1)
