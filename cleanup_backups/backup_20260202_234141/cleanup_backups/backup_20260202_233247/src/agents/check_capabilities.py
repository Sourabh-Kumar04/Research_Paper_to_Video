#!/usr/bin/env python3
"""
Capabilities Check Script for TypeScript Video Template Engine.
Checks availability of Python video generation components.
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_capabilities():
    """Check all video generation capabilities."""
    capabilities = {
        "python_available": True,
        "audio_generation": False,
        "animation_generation": False,
        "video_composition": False,
        "tts_engines": [],
        "video_libraries": [],
        "ffmpeg_available": False,
        "recommended_actions": []
    }
    
    # Check audio generation
    try:
        from agents.simple_audio_generator import SimpleAudioGenerator
        audio_gen = SimpleAudioGenerator()
        capabilities["audio_generation"] = True
        capabilities["tts_engines"] = audio_gen.get_available_engines()
        
        if not capabilities["tts_engines"]:
            capabilities["recommended_actions"].append("Install TTS engine: pip install pyttsx3")
    except Exception as e:
        capabilities["recommended_actions"].append(f"Fix audio generation: {str(e)}")
    
    # Check animation generation
    try:
        from agents.simple_animation_generator import SimpleAnimationGenerator
        anim_gen = SimpleAnimationGenerator()
        anim_caps = anim_gen.get_capabilities()
        capabilities["animation_generation"] = True
        capabilities["ffmpeg_available"] = anim_caps.get("ffmpeg_available", False)
        
        if not capabilities["ffmpeg_available"]:
            capabilities["recommended_actions"].append("Install FFmpeg for animations")
    except Exception as e:
        capabilities["recommended_actions"].append(f"Fix animation generation: {str(e)}")
    
    # Check video composition
    try:
        from agents.python_video_composer import PythonVideoComposer
        video_composer = PythonVideoComposer()
        video_caps = video_composer.get_capabilities()
        capabilities["video_composition"] = True
        
        # Check available video libraries
        video_libs = []
        if video_caps.get("moviepy_available", False):
            video_libs.append("moviepy")
        if video_caps.get("opencv_available", False):
            video_libs.append("opencv")
        if video_caps.get("pil_available", False):
            video_libs.append("pil")
        
        capabilities["video_libraries"] = video_libs
        
        if not video_libs:
            capabilities["recommended_actions"].append("Install video libraries: pip install moviepy opencv-python Pillow")
        elif "moviepy" not in video_libs:
            capabilities["recommended_actions"].append("Install MoviePy for better quality: pip install moviepy")
            
    except Exception as e:
        capabilities["recommended_actions"].append(f"Fix video composition: {str(e)}")
    
    # Overall readiness
    capabilities["ready_for_production"] = (
        capabilities["audio_generation"] and 
        capabilities["animation_generation"] and 
        capabilities["video_composition"] and
        len(capabilities["video_libraries"]) > 0
    )
    
    return capabilities


def main():
    """Main entry point."""
    try:
        capabilities = check_capabilities()
        print(json.dumps(capabilities, indent=2))
        sys.exit(0)
    except Exception as e:
        error_result = {
            "python_available": False,
            "error": str(e),
            "recommended_actions": ["Fix Python environment setup"]
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()