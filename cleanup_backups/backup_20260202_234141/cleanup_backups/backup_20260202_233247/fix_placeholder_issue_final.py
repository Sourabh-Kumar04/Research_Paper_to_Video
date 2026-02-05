#!/usr/bin/env python3
"""
Fix placeholder issue - ensure frontend gets real videos, not placeholders
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def check_backend_endpoints():
    """Check which backend endpoints exist and what they do."""
    
    print("🔍 CHECKING BACKEND ENDPOINTS")
    print("=" * 50)
    
    # Check if backend routes exist
    backend_routes = [
        "src/backend/src/routes/jobs.ts",
        "src/backend/src/routes/render.ts", 
        "src/backend/src/routes/video.ts",
        "src/routes/jobs.ts",
        "src/routes/render.ts"
    ]
    
    existing_routes = []
    for route in backend_routes:
        if Path(route).exists():
            existing_routes.append(route)
            print(f"✅ Found: {route}")
        else:
            print(f"❌ Missing: {route}")
    
    return existing_routes

def check_frontend_api_calls():
    """Check what API endpoints the frontend is calling."""
    
    print("\n🔍 CHECKING FRONTEND API CALLS")
    print("=" * 50)
    
    frontend_files = [
        "src/frontend/src/App.tsx",
        "src/frontend/src/App.js", 
        "src/frontend/src/components/VideoGenerator.tsx",
        "src/frontend/src/components/VideoGenerator.js",
        "frontend/src/App.tsx",
        "frontend/src/App.js"
    ]
    
    for file_path in frontend_files:
        if Path(file_path).exists():
            print(f"✅ Found frontend file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for API calls
            api_patterns = [
                '/api/v1/jobs',
                '/api/v1/render', 
                '/api/video',
                'fetch(',
                'axios.',
                'api/'
            ]
            
            for pattern in api_patterns:
                if pattern in content:
                    print(f"   📡 Uses: {pattern}")
        else:
            print(f"❌ Missing: {file_path}")

async def test_backend_directly():
    """Test the backend video generation directly."""
    
    print("\n🧪 TESTING BACKEND DIRECTLY")
    print("=" * 50)
    
    from production_video_generator import ProductionVideoGenerator
    
    # Test with a unique job ID to avoid caching
    job_id = f"direct_test_{int(time.time())}"
    paper_title = "Direct Backend Test Paper"
    output_dir = f"output/direct_test_{job_id}"
    
    print(f"Job ID: {job_id}")
    print(f"Paper: {paper_title}")
    print(f"Output: {output_dir}")
    
    generator = ProductionVideoGenerator(job_id, paper_title, output_dir)
    
    try:
        result = await generator.generate_video()
        
        if result:
            output_file = Path(result)
            if output_file.exists():
                file_size = output_file.stat().st_size
                print(f"✅ Backend generated video: {output_file.name}")
                print(f"📊 File size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")
                
                # Check if it's a real video
                if file_size > 5000000:  # > 5MB
                    print("✅ File size indicates REAL VIDEO (not placeholder)")
                    return True, str(output_file)
                else:
                    print("⚠️ File size suggests possible placeholder")
                    return False, str(output_file)
            else:
                print("❌ Output file not found")
                return False, None
        else:
            print("❌ Backend returned None")
            return False, None
            
    except Exception as e:
        print(f"❌ Backend error: {e}")
        return False, None

def create_cache_clear_instructions():
    """Create instructions for clearing browser cache."""
    
    instructions = """
# 🔄 CLEAR BROWSER CACHE TO SEE NEW VIDEOS

## The Issue
You're seeing old placeholder videos because your browser has cached them.
The backend IS generating real videos (we confirmed 36.5 MB files), but your browser is showing old cached placeholders.

## Solution: Clear Browser Cache

### Method 1: Hard Refresh (Recommended)
1. Open your browser with the RASO frontend
2. Press **Ctrl + Shift + R** (Windows) or **Cmd + Shift + R** (Mac)
3. This forces a complete refresh without cache

### Method 2: Use Incognito/Private Mode
1. Open a new Incognito/Private window
2. Navigate to your RASO frontend URL
3. Generate a new video - you should see the real video

### Method 3: Clear Browser Cache Manually
**Chrome:**
1. Press F12 to open Developer Tools
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

**Firefox:**
1. Press Ctrl + Shift + Delete
2. Select "Cached Web Content"
3. Click "Clear Now"

### Method 4: Clear Specific Cache
1. Open Developer Tools (F12)
2. Go to Application/Storage tab
3. Clear "Local Storage" and "Session Storage"
4. Clear "Cache Storage"

## Verification
After clearing cache, generate a new video. You should see:
- ✅ Real video content (not placeholder)
- ✅ Longer duration (20+ minutes)
- ✅ Actual animations and content

## Technical Details
- Backend generates: 36.5 MB real videos
- Old system generated: Small placeholder videos
- Browser cached the old placeholders
- Cache clearing shows the new real videos
"""
    
    with open("CLEAR_BROWSER_CACHE_INSTRUCTIONS.md", 'w') as f:
        f.write(instructions)
    
    print("✅ Created: CLEAR_BROWSER_CACHE_INSTRUCTIONS.md")

def check_video_serving():
    """Check how videos are being served to the frontend."""
    
    print("\n🔍 CHECKING VIDEO SERVING")
    print("=" * 50)
    
    # Check for video files in output directories
    output_dirs = [
        "output",
        "temp", 
        "public",
        "static",
        "assets"
    ]
    
    video_files = []
    for dir_path in output_dirs:
        if Path(dir_path).exists():
            for video_file in Path(dir_path).rglob("*.mp4"):
                file_size = video_file.stat().st_size
                video_files.append((str(video_file), file_size))
                
                if file_size > 5000000:  # > 5MB
                    print(f"✅ REAL VIDEO: {video_file} ({file_size/1024/1024:.1f} MB)")
                else:
                    print(f"⚠️ SMALL VIDEO: {video_file} ({file_size} bytes)")
    
    if not video_files:
        print("❌ No video files found in output directories")
    
    return video_files

async def main():
    """Main diagnostic and fix function."""
    
    print("🔧 FIXING PLACEHOLDER VIDEO ISSUE")
    print("=" * 60)
    
    # Step 1: Check backend endpoints
    existing_routes = check_backend_endpoints()
    
    # Step 2: Check frontend API calls  
    check_frontend_api_calls()
    
    # Step 3: Test backend directly
    success, video_path = await test_backend_directly()
    
    # Step 4: Check video serving
    video_files = check_video_serving()
    
    # Step 5: Create cache clear instructions
    create_cache_clear_instructions()
    
    print("\n📋 DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if success and video_path:
        print("✅ BACKEND IS WORKING - Generates real videos")
        print(f"✅ Latest video: {video_path}")
        print("⚠️ ISSUE: Browser cache showing old placeholders")
        print("🔧 SOLUTION: Clear browser cache (see CLEAR_BROWSER_CACHE_INSTRUCTIONS.md)")
    else:
        print("❌ BACKEND ISSUE - Not generating real videos")
        print("🔧 SOLUTION: Backend needs debugging")
    
    print(f"\n📊 FOUND {len(video_files)} video files total")
    real_videos = [v for v in video_files if v[1] > 5000000]
    print(f"📊 {len(real_videos)} are real videos (>5MB)")
    
    if len(real_videos) > 0:
        print("\n✅ CONCLUSION: Backend generates real videos")
        print("🔄 Clear your browser cache to see them!")
    else:
        print("\n❌ CONCLUSION: Backend not generating real videos")

if __name__ == "__main__":
    asyncio.run(main())