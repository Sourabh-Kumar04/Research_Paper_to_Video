#!/usr/bin/env python3
"""
Video Composition Bridge Script for TypeScript Video Template Engine.
Composes final video from audio and animation assets using PythonVideoComposer.
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.python_video_composer import PythonVideoComposer


class VideoCompositionBridge:
    """Bridge between TypeScript and Python video composition."""
    
    def __init__(self):
        self.video_composer = PythonVideoComposer()
    
    async def compose_from_assets(
        self, 
        audio_assets_path: str, 
        animation_assets_path: str, 
        output_path: str,
        format_spec: str = "mp4",
        resolution: str = "1280x720",
        quality: str = "1080p"
    ) -> Dict[str, Any]:
        """Compose video from audio and animation assets."""
        try:
            # Load audio assets
            with open(audio_assets_path, 'r', encoding='utf-8') as f:
                audio_data = json.load(f)
            
            # Load animation assets
            with open(animation_assets_path, 'r', encoding='utf-8') as f:
                animation_data = json.load(f)
            
            # Convert to objects expected by video composer
            audio_assets = self._create_audio_assets_from_data(audio_data)
            animation_assets = self._create_animation_assets_from_data(animation_data)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Compose video
            result = self.video_composer.compose_video(audio_assets, animation_assets, output_path)
            
            return {
                "success": result.success,
                "output_path": result.output_path,
                "file_size": result.file_size,
                "duration": result.duration,
                "resolution": list(result.resolution),
                "method_used": result.method_used,
                "errors": result.errors,
                "warnings": result.warnings
            }
            
        except Exception as e:
            return {
                "success": False,
                "output_path": output_path,
                "file_size": 0,
                "duration": 0.0,
                "resolution": [0, 0],
                "method_used": "none",
                "errors": [f"Video composition error: {str(e)}"],
                "warnings": []
            }
    
    def _create_audio_assets_from_data(self, audio_data: Dict[str, Any]):
        """Create audio assets object from JSON data."""
        # Create a simple object that matches what PythonVideoComposer expects
        class AudioAssets:
            def __init__(self, scenes_data, total_duration, sample_rate):
                self.scenes = [self._create_audio_scene(scene) for scene in scenes_data]
                self.total_duration = total_duration
                self.sample_rate = sample_rate
            
            def _create_audio_scene(self, scene_data):
                class AudioScene:
                    def __init__(self, scene_id, file_path, duration, transcript, timing_markers):
                        self.scene_id = scene_id
                        self.file_path = file_path
                        self.duration = duration
                        self.transcript = transcript
                        self.timing_markers = timing_markers
                
                return AudioScene(
                    scene_data["scene_id"],
                    scene_data["file_path"],
                    scene_data["duration"],
                    scene_data["transcript"],
                    scene_data["timing_markers"]
                )
        
        return AudioAssets(
            audio_data["scenes"],
            audio_data["total_duration"],
            audio_data["sample_rate"]
        )
    
    def _create_animation_assets_from_data(self, animation_data: Dict[str, Any]):
        """Create animation assets object from JSON data."""
        # Create a simple object that matches what PythonVideoComposer expects
        class AnimationAssets:
            def __init__(self, scenes_data, total_duration, resolution):
                self.scenes = [self._create_animation_scene(scene) for scene in scenes_data]
                self.total_duration = total_duration
                self.resolution = resolution
            
            def _create_animation_scene(self, scene_data):
                class AnimationScene:
                    def __init__(self, scene_id, file_path, duration, framework, resolution, frame_rate, status):
                        self.scene_id = scene_id
                        self.file_path = file_path
                        self.duration = duration
                        self.framework = framework
                        self.resolution = resolution
                        self.frame_rate = frame_rate
                        self.status = status
                
                return AnimationScene(
                    scene_data["scene_id"],
                    scene_data["file_path"],
                    scene_data["duration"],
                    scene_data["framework"],
                    scene_data["resolution"],
                    scene_data["frame_rate"],
                    scene_data["status"]
                )
        
        return AnimationAssets(
            animation_data["scenes"],
            animation_data["total_duration"],
            animation_data["resolution"]
        )


def main():
    """Main entry point for the bridge script."""
    parser = argparse.ArgumentParser(description="Compose video from audio and animation assets")
    parser.add_argument("--audio-assets", required=True, help="Path to audio assets JSON file")
    parser.add_argument("--animation-assets", required=True, help="Path to animation assets JSON file")
    parser.add_argument("--output-path", required=True, help="Output path for composed video")
    parser.add_argument("--format", default="mp4", help="Output format")
    parser.add_argument("--resolution", default="1280x720", help="Output resolution")
    parser.add_argument("--quality", default="1080p", help="Output quality")
    
    args = parser.parse_args()
    
    # Compose video
    bridge = VideoCompositionBridge()
    result = asyncio.run(bridge.compose_from_assets(
        args.audio_assets,
        args.animation_assets,
        args.output_path,
        args.format,
        args.resolution,
        args.quality
    ))
    
    # Output result as JSON
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()