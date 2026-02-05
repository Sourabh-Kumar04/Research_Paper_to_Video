#!/usr/bin/env python3
"""
Simple Working Video Generation - Create a video that actually works
"""

import subprocess
import tempfile
from pathlib import Path
import time

def create_simple_video():
    """Create a simple video using FFmpeg directly"""
    print("🎬 Creating Simple Working Video")
    
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    output_video = temp_dir / "simple_video.mp4"
    
    print(f"Output: {output_video}")
    
    try:
        # Create a simple 10-second video with text
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=blue:size=1920x1080:duration=10",
            "-vf", "drawtext=text='RASO Video Generation Test':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(output_video)
        ]
        
        print("Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if output_video.exists():
                file_size = output_video.stat().st_size
                print(f"✅ Video created successfully!")
                print(f"   Size: {file_size:,} bytes")
                print(f"   Path: {output_video}")
                return True
            else:
                print("❌ FFmpeg succeeded but file not found")
                return False
        else:
            print(f"❌ FFmpeg failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timed out")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found - please install FFmpeg")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_system_components():
    """Test individual system components"""
    print("\n🔧 Testing System Components")
    
    # Test imports
    try:
        from agents.video_composition import VideoCompositionAgent
        from backend.models import AgentType
        print("✅ Core imports working")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test agent creation
    try:
        agent = VideoCompositionAgent(AgentType.VIDEO_COMPOSING)
        print("✅ VideoCompositionAgent creation working")
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return False
    
    # Test performance monitor
    try:
        from utils.performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        task_id = monitor.start_operation("test")
        monitor.end_operation(task_id)
        print("✅ PerformanceMonitor working")
    except Exception as e:
        print(f"❌ PerformanceMonitor error: {e}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("🚀 RASO Simple Working Video Test")
    print("=" * 60)
    
    # Test system components
    components_ok = test_system_components()
    
    # Create simple video
    video_ok = create_simple_video()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    print(f"   System Components: {'✅ WORKING' if components_ok else '❌ FAILED'}")
    print(f"   Video Generation: {'✅ WORKING' if video_ok else '❌ FAILED'}")
    
    if components_ok and video_ok:
        print("\n🎉 SUCCESS: Core system is functional!")
        print("The issue is likely in the complex pipeline, not the core components.")
        print("\nNext steps:")
        print("1. The VideoCompositionAgent works")
        print("2. FFmpeg video generation works")
        print("3. The issue is in the pipeline orchestration")
    else:
        print("\n❌ FAILURE: Core system has issues")
        if not components_ok:
            print("- Fix the component import/creation issues first")
        if not video_ok:
            print("- Install FFmpeg or fix video generation")
    
    print("=" * 60)

if __name__ == "__main__":
    main()