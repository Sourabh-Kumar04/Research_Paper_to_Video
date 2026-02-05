#!/usr/bin/env python3
"""Debug the video composition system to find why it's falling back to mock files."""

import asyncio
import tempfile
from pathlib import Path
from agents.video_composition import VideoCompositionAgent
from backend.models import AgentType
from backend.models.animation import AnimationAssets, RenderedScene, VideoResolution
from backend.models.audio import AudioAssets, AudioScene
from utils.video_utils import video_utils
from utils.quality_presets import quality_manager


async def debug_video_composition():
    """Debug the video composition system step by step."""
    print("🔧 Debugging Video Composition System")
    print("=" * 50)
    
    # Check system requirements
    print("1. System Requirements Check:")
    ffmpeg_available = video_utils.is_ffmpeg_available()
    print(f"   FFmpeg Available: {'✅' if ffmpeg_available else '❌'}")
    
    if ffmpeg_available:
        print(f"   FFmpeg Path: {video_utils.get_ffmpeg_path()}")
        print(f"   FFprobe Path: {video_utils.get_ffprobe_path()}")
    else:
        print("   ❌ FFmpeg not available - this is the problem!")
        return False
    
    # Check quality presets
    print("\n2. Quality Presets Check:")
    try:
        encoding_params = quality_manager.get_preset("medium")
        print(f"   ✅ Medium preset loaded: {encoding_params.resolution} @ {encoding_params.bitrate}")
    except Exception as e:
        print(f"   ❌ Quality preset error: {e}")
        return False
    
    # Create video composition agent
    print("\n3. Agent Initialization:")
    try:
        agent = VideoCompositionAgent(AgentType.VIDEO_COMPOSING)
        print("   ✅ VideoCompositionAgent created")
    except Exception as e:
        print(f"   ❌ Agent creation failed: {e}")
        return False
    
    # Check agent configuration
    print("\n4. Agent Configuration:")
    try:
        config = agent.config
        print(f"   Data Path: {config.data_path}")
        print(f"   Temp Path: {config.temp_path}")
        
        # Check if paths exist and are writable
        data_path = Path(config.data_path)
        temp_path = Path(config.temp_path)
        
        print(f"   Data Path Exists: {'✅' if data_path.exists() else '❌'}")
        print(f"   Temp Path Exists: {'✅' if temp_path.exists() else '❌'}")
        
        # Try to create directories if they don't exist
        data_path.mkdir(parents=True, exist_ok=True)
        temp_path.mkdir(parents=True, exist_ok=True)
        
        print(f"   Data Path Writable: {'✅' if data_path.is_dir() else '❌'}")
        print(f"   Temp Path Writable: {'✅' if temp_path.is_dir() else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False
    
    # Test placeholder video creation
    print("\n5. Placeholder Video Creation Test:")
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            placeholder_path = tmp_file.name
        
        await agent._create_production_placeholder_video(
            placeholder_path, 3.0, encoding_params
        )
        
        if Path(placeholder_path).exists():
            file_size = Path(placeholder_path).stat().st_size
            print(f"   ✅ Placeholder created: {file_size} bytes")
            
            # Quick validation
            duration = video_utils.get_video_duration(placeholder_path)
            print(f"   Duration: {duration} seconds")
            
            # Clean up
            Path(placeholder_path).unlink()
            
            if file_size > 1000 and duration > 0:
                print("   ✅ Placeholder video is valid")
            else:
                print("   ❌ Placeholder video is invalid")
                return False
        else:
            print("   ❌ Placeholder creation failed - no file created")
            return False
            
    except Exception as e:
        print(f"   ❌ Placeholder creation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test full composition method
    print("\n6. Full Composition Method Test:")
    try:
        # Create mock assets
        animations = AnimationAssets(
            scenes=[
                RenderedScene(
                    scene_id='test_scene',
                    file_path='nonexistent_animation.mp4',
                    duration=5.0,
                    framework='manim',
                    resolution=VideoResolution(width=1920, height=1080),
                    frame_rate=30
                )
            ],
            total_duration=5.0,
            resolution=VideoResolution(width=1920, height=1080)
        )
        
        audio = AudioAssets(
            scenes=[
                AudioScene(
                    scene_id='test_scene',
                    file_path='nonexistent_audio.wav',
                    duration=5.0,
                    transcript='Test audio for debugging video composition.'
                )
            ],
            total_duration=5.0
        )
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        print(f"   Testing composition to: {output_path}")
        
        # Test the production composition method
        success = await agent._compose_video_production(animations, audio, output_path, "medium")
        
        if success and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"   ✅ Composition successful: {file_size} bytes")
            
            # Check if it's a real video or mock file
            with open(output_path, 'rb') as f:
                first_bytes = f.read(100)
            
            if b'# RASO Mock Video File' in first_bytes:
                print("   ❌ Generated mock file (composition methods failed)")
                return False
            else:
                print("   ✅ Generated real video file")
                
                # Validate with FFprobe
                duration = video_utils.get_video_duration(output_path)
                print(f"   Duration: {duration} seconds")
                
                # Clean up
                Path(output_path).unlink()
                
                return duration > 0
        else:
            print("   ❌ Composition failed - no output file")
            return False
            
    except Exception as e:
        print(f"   ❌ Composition test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the debug test."""
    success = await debug_video_composition()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Video composition system is working correctly!")
        print("The issue may be in the pipeline integration.")
    else:
        print("❌ Video composition system has issues.")
        print("Check the errors above to identify the problem.")


if __name__ == "__main__":
    asyncio.run(main())