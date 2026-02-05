#!/usr/bin/env python3
"""
Fix FFmpeg PATH and Test Video Generation
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def setup_ffmpeg_path():
    """Add local FFmpeg to PATH"""
    # Get current directory
    current_dir = Path.cwd()
    ffmpeg_bin = current_dir / "ffmpeg" / "bin"
    
    if ffmpeg_bin.exists():
        # Add to PATH
        current_path = os.environ.get('PATH', '')
        if str(ffmpeg_bin) not in current_path:
            os.environ['PATH'] = str(ffmpeg_bin) + os.pathsep + current_path
            print(f"✅ Added FFmpeg to PATH: {ffmpeg_bin}")
        else:
            print("✅ FFmpeg already in PATH")
        return True
    else:
        print(f"❌ FFmpeg not found at: {ffmpeg_bin}")
        return False

def test_ffmpeg():
    """Test FFmpeg functionality"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg working: {version_line}")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        return False
    except Exception as e:
        print(f"❌ FFmpeg test error: {e}")
        return False

def create_test_video():
    """Create a test video with FFmpeg"""
    temp_dir = Path(tempfile.mkdtemp())
    output_video = temp_dir / "test_video.mp4"
    
    print(f"Creating test video: {output_video}")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=green:size=1920x1080:duration=5",
            "-vf", "drawtext=text='RASO Test Video - FFmpeg Working!':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(output_video)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and output_video.exists():
            file_size = output_video.stat().st_size
            print(f"✅ Test video created successfully!")
            print(f"   Size: {file_size:,} bytes")
            print(f"   Path: {output_video}")
            return True
        else:
            print(f"❌ Video creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Video creation error: {e}")
        return False

def test_video_composition_agent():
    """Test VideoCompositionAgent with FFmpeg working"""
    try:
        from agents.video_composition import VideoCompositionAgent
        from backend.models import AgentType
        
        agent = VideoCompositionAgent(AgentType.VIDEO_COMPOSING)
        
        # Test performance monitor methods
        operation_id = agent.performance_monitor.start_operation("test_operation")
        agent.performance_monitor.end_operation(operation_id, success=True)
        
        print("✅ VideoCompositionAgent with PerformanceMonitor working")
        return True
        
    except Exception as e:
        print(f"❌ VideoCompositionAgent error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔧 RASO FFmpeg Fix and Test")
    print("=" * 50)
    
    # Step 1: Setup FFmpeg PATH
    print("1. Setting up FFmpeg PATH...")
    ffmpeg_setup = setup_ffmpeg_path()
    
    # Step 2: Test FFmpeg
    print("\n2. Testing FFmpeg...")
    ffmpeg_working = test_ffmpeg()
    
    # Step 3: Create test video
    print("\n3. Creating test video...")
    video_created = create_test_video()
    
    # Step 4: Test VideoCompositionAgent
    print("\n4. Testing VideoCompositionAgent...")
    agent_working = test_video_composition_agent()
    
    # Results
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"   FFmpeg Setup: {'✅' if ffmpeg_setup else '❌'}")
    print(f"   FFmpeg Working: {'✅' if ffmpeg_working else '❌'}")
    print(f"   Video Creation: {'✅' if video_created else '❌'}")
    print(f"   Agent Working: {'✅' if agent_working else '❌'}")
    
    all_working = ffmpeg_setup and ffmpeg_working and video_created and agent_working
    
    if all_working:
        print("\n🎉 SUCCESS! All components working!")
        print("The RASO video generation system is now functional.")
        print("\nNext steps:")
        print("1. Restart the backend server to pick up FFmpeg")
        print("2. Submit a new video generation job")
        print("3. Jobs should now complete successfully")
    else:
        print("\n❌ Some components still have issues")
        if not ffmpeg_setup or not ffmpeg_working:
            print("- FFmpeg installation/PATH issues")
        if not video_created:
            print("- Video creation problems")
        if not agent_working:
            print("- Agent/system integration issues")
    
    print("=" * 50)

if __name__ == "__main__":
    main()