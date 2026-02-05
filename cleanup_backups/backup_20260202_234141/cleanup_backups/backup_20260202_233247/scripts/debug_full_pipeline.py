#!/usr/bin/env python3
"""Debug the full pipeline to see exactly what's happening with video generation."""

import asyncio
import requests
import time
import json
from pathlib import Path


async def debug_full_pipeline():
    """Run the full pipeline and debug the video generation process."""
    print("🔍 Debugging Full RASO Pipeline")
    print("=" * 50)
    
    # Check backend
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend not running")
            return False
    except:
        print("❌ Backend not accessible")
        return False
    
    print("✅ Backend is running")
    
    # Submit job
    test_paper = {
        "paper_input": {
            "type": "title",
            "content": "Attention Is All You Need"
        }
    }
    
    try:
        print("📄 Submitting job...")
        response = requests.post("http://localhost:8000/api/jobs", json=test_paper, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Job submission failed: {response.status_code}")
            print(response.text)
            return False
        
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"✅ Job created: {job_id}")
        
        # Monitor progress with detailed logging
        print("⏳ Monitoring progress...")
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
            
            status_data = status_response.json()
            status = status_data["status"]
            progress = status_data.get("progress", 0)
            current_agent = status_data.get("current_agent", "unknown")
            
            print(f"   Status: {status}, Progress: {progress}%, Agent: {current_agent}")
            
            if status == "completed":
                print("✅ Job completed!")
                
                # Examine the job result in detail
                print("\n🔍 Examining Job Result:")
                print(f"   Job ID: {status_data['job_id']}")
                print(f"   Status: {status_data['status']}")
                print(f"   Progress: {status_data['progress']}%")
                print(f"   Created: {status_data['created_at']}")
                print(f"   Updated: {status_data['updated_at']}")
                
                # Check if there's a result
                if status_data.get("result"):
                    result = status_data["result"]
                    print(f"   Result keys: {list(result.keys())}")
                    
                    # Check video information
                    if "video" in result:
                        video_info = result["video"]
                        print(f"\n📹 Video Information:")
                        print(f"   File Path: {video_info.get('file_path', 'NOT SET')}")
                        print(f"   Duration: {video_info.get('duration', 'NOT SET')}")
                        print(f"   Resolution: {video_info.get('resolution', 'NOT SET')}")
                        print(f"   File Size: {video_info.get('file_size', 'NOT SET')}")
                        
                        # Check if the file actually exists
                        video_path = video_info.get('file_path')
                        if video_path:
                            if Path(video_path).exists():
                                actual_size = Path(video_path).stat().st_size
                                print(f"   ✅ File exists on disk: {actual_size} bytes")
                                
                                # Check file content
                                with open(video_path, 'rb') as f:
                                    first_bytes = f.read(100)
                                
                                if b'# RASO Mock Video File' in first_bytes:
                                    print("   ❌ File contains mock content!")
                                    print("   This means the video composition agent fell back to mock file creation")
                                    
                                    # Show some of the mock content
                                    with open(video_path, 'r') as f:
                                        mock_content = f.read(300)
                                    print(f"   Mock content preview:\n{mock_content}")
                                    
                                elif first_bytes.startswith(b'\x00\x00\x00') and b'ftyp' in first_bytes:
                                    print("   ✅ File contains real MP4 content!")
                                    
                                    # Validate with FFprobe
                                    from utils.video_utils import video_utils
                                    duration = video_utils.get_video_duration(video_path)
                                    print(f"   Video duration: {duration} seconds")
                                    
                                    if duration > 0:
                                        print("   ✅ Video is valid and playable")
                                        return True
                                    else:
                                        print("   ❌ Video appears corrupted")
                                        return False
                                else:
                                    print("   ⚠️  File contains unknown content")
                                    print(f"   First 50 bytes: {first_bytes[:50]}")
                                    return False
                            else:
                                print(f"   ❌ File does not exist on disk: {video_path}")
                                return False
                        else:
                            print("   ❌ No file path in video info")
                            return False
                    else:
                        print("   ❌ No video information in result")
                        return False
                else:
                    print("   ❌ No result data")
                    return False
                
                break
                
            elif status == "failed":
                error = status_data.get("error_message", "Unknown error")
                print(f"❌ Job failed: {error}")
                return False
            
            await asyncio.sleep(3)
        else:
            print("❌ Job timed out")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the debug test."""
    success = await debug_full_pipeline()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Pipeline generates real MP4 videos correctly!")
    else:
        print("❌ Pipeline has issues with video generation.")
        print("Check the detailed output above to identify the problem.")


if __name__ == "__main__":
    asyncio.run(main())