#!/usr/bin/env python3
"""
Animation Generation Bridge Script for TypeScript Video Template Engine.
Generates animation assets from script data using SimpleAnimationGenerator.
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.simple_animation_generator import SimpleAnimationGenerator
from backend.models.script import NarrationScript, Scene


class AnimationGenerationBridge:
    """Bridge between TypeScript and Python animation generation."""
    
    def __init__(self):
        self.animation_generator = SimpleAnimationGenerator()
    
    async def generate_from_script_file(self, script_path: str, output_dir: str) -> Dict[str, Any]:
        """Generate animation assets from script file."""
        try:
            # Load script data
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # Convert to NarrationScript object
            script = self._create_script_from_data(script_data)
            
            # Generate animation assets
            animation_assets = await self.animation_generator.generate_animation_assets(script, output_dir)
            
            # Save animation assets metadata
            assets_data = self._serialize_animation_assets(animation_assets)
            assets_path = Path(output_dir) / "animation_assets.json"
            
            with open(assets_path, 'w', encoding='utf-8') as f:
                json.dump(assets_data, f, indent=2)
            
            return {
                "success": True,
                "animation_assets_path": str(assets_path),
                "total_duration": animation_assets.total_duration,
                "scene_count": len(animation_assets.scenes),
                "resolution": f"{animation_assets.resolution.width}x{animation_assets.resolution.height}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_script_from_data(self, script_data: Dict[str, Any]) -> NarrationScript:
        """Create NarrationScript object from JSON data."""
        scenes = []
        
        for scene_data in script_data.get("scenes", []):
            scene = Scene(
                id=scene_data["id"],
                title=scene_data["title"],
                narration=scene_data["narration"],
                duration=scene_data["duration"],
                concepts=scene_data.get("concepts", []),
                visual_type=scene_data.get("visual_type", "remotion")
            )
            scenes.append(scene)
        
        return NarrationScript(
            scenes=scenes,
            total_duration=script_data.get("total_duration", 0),
            word_count=script_data.get("word_count", 0),
            target_audience=script_data.get("target_audience", "general"),
            language=script_data.get("language", "en")
        )
    
    def _serialize_animation_assets(self, animation_assets) -> Dict[str, Any]:
        """Serialize animation assets to JSON-compatible format."""
        return {
            "scenes": [
                {
                    "scene_id": scene.scene_id,
                    "file_path": scene.file_path,
                    "duration": scene.duration,
                    "framework": scene.framework,
                    "resolution": {
                        "width": scene.resolution.width,
                        "height": scene.resolution.height
                    },
                    "frame_rate": scene.frame_rate,
                    "status": scene.status.value
                }
                for scene in animation_assets.scenes
            ],
            "total_duration": animation_assets.total_duration,
            "resolution": {
                "width": animation_assets.resolution.width,
                "height": animation_assets.resolution.height
            }
        }


async def main():
    """Main entry point for the bridge script."""
    parser = argparse.ArgumentParser(description="Generate animation assets from script")
    parser.add_argument("--script-path", required=True, help="Path to script JSON file")
    parser.add_argument("--output-dir", required=True, help="Output directory for animation files")
    
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate animations
    bridge = AnimationGenerationBridge()
    result = await bridge.generate_from_script_file(args.script_path, args.output_dir)
    
    # Output result as JSON
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    asyncio.run(main())