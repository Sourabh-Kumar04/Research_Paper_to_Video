#!/usr/bin/env python3
"""Download and examine the generated video file."""

import requests
import json
from pathlib import Path

# Use the successful job ID
job_id = "60aaeb8b-1ed1-46af-84d5-aff84d1700"

try:
    # Download the video
    response = requests.get(f"http://localhost:8000/api/jobs/{job_id}/download")
    
    if response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        print(f"Content-Type: {content_type}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        # Save the file
        output_path = f"downloaded_video_{job_id}.mp4"
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Video saved to: {output_path}")
        
        # Check if it's a real video file
        with open(output_path, 'rb') as f:
            first_bytes = f.read(100)
            
        print(f"First 100 bytes (hex): {first_bytes.hex()}")
        print(f"First 100 bytes (text): {first_bytes}")
        
        # Check if it starts with MP4 signature
        if first_bytes.startswith(b'\x00\x00\x00') and b'ftyp' in first_bytes:
            print("✅ This appears to be a real MP4 file!")
        elif b'# RASO Mock Video File' in first_bytes:
            print("❌ This is a mock text file")
        else:
            print("⚠️  Unknown file format")
        
        # Try to get video info using FFprobe
        try:
            import subprocess
            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                print("\n📊 Video Information:")
                format_info = info.get("format", {})
                print(f"  Format: {format_info.get('format_name', 'unknown')}")
                print(f"  Duration: {format_info.get('duration', 'unknown')} seconds")
                print(f"  Size: {format_info.get('size', 'unknown')} bytes")
                
                streams = info.get("streams", [])
                for i, stream in enumerate(streams):
                    print(f"  Stream {i}: {stream.get('codec_type', 'unknown')} - {stream.get('codec_name', 'unknown')}")
            else:
                print(f"❌ FFprobe failed: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️  Could not analyze with FFprobe: {e}")
        
    else:
        print(f"❌ Failed to download: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")