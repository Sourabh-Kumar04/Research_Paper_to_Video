#!/usr/bin/env python3
"""
Test Professional Video Generation
Generates a sample professional video to compare with current output.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.professional_video_generator import create_professional_scene_video

async def test_professional_video():
    """Test professional video generation."""
    
    print("🎬 Testing Professional Video Generation")
    print("=" * 60)
    
    # Sample scene data (based on "Attention is All You Need" paper)
    scene_data = {
        'title': 'Sequential Processing Bottlenecks in RNNs and CNNs',
        'narration': (
            'Traditional recurrent neural networks process sequences one step at a time, '
            'creating a bottleneck that prevents parallel computation. '
            'Convolutional networks, while parallel, struggle with long-range dependencies. '
            'The Transformer architecture solves both problems through self-attention, '
            'enabling both parallel processing and effective capture of long-distance relationships.'
        ),
        'duration': 12.0,
        'visual_type': 'text',
        'scene_type': 'problem',
        'equations': []
    }
    
    output_path = Path(__file__).parent / "output" / "test_professional.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📝 Scene Info:")
    print(f"   Title: {scene_data['title']}")
    print(f"   Duration: {scene_data['duration']}s")
    print(f"   Type: {scene_data['visual_type']}")
    
    print(f"\n🎨 Generating professional cinematic video...")
    print(f"   Output: {output_path}")
    
    # Generate video
    success = await create_professional_scene_video(
        scene_data=scene_data,
        output_path=str(output_path),
        style='cinematic'
    )
    
    if success:
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ Professional video generated successfully!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"\n📊 Quality Features:")
        print(f"   ✓ Film grain texture")
        print(f"   ✓ Animated fade transitions")
        print(f"   ✓ Professional typography")
        print(f"   ✓ Color-coded elements")
        print(f"   ✓ Shadow effects")
        print(f"   ✓ Progress indicator")
        print(f"   ✓ 24fps cinematic framerate")
        print(f"   ✓ Near-lossless quality (CRF 17)")
        
        print(f"\n🎬 Open the video to see the improvements!")
        print(f"   Compare with your current video output.")
        
    else:
        print(f"\n❌ Failed to generate professional video")
        print(f"   Check if FFmpeg is installed and accessible")
    
    print("\n" + "=" * 60)
    
    return success


async def test_with_equations():
    """Test with mathematical equations (requires Manim)."""
    
    print("\n🧮 Testing with Mathematical Content")
    print("=" * 60)
    
    scene_data = {
        'title': 'The Attention Mechanism',
        'narration': (
            'The core innovation of the Transformer is the scaled dot-product attention. '
            'Given queries Q, keys K, and values V, attention is computed as '
            'softmax of Q times K transpose divided by square root of dimension, '
            'multiplied by V. This allows the model to focus on relevant parts '
            'of the input sequence dynamically.'
        ),
        'duration': 15.0,
        'visual_type': 'manim',
        'scene_type': 'technical',
        'equations': [
            r'Attention(Q, K, V) = softmax(\frac{QK^T}{\sqrt{d_k}})V',
            r'Q = XW^Q',
            r'K = XW^K',
            r'V = XW^V'
        ]
    }
    
    output_path = Path(__file__).parent / "output" / "test_professional_manim.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📝 Scene Info:")
    print(f"   Title: {scene_data['title']}")
    print(f"   Duration: {scene_data['duration']}s")
    print(f"   Type: {scene_data['visual_type']}")
    print(f"   Equations: {len(scene_data['equations'])}")
    
    print(f"\n🎨 Generating professional video with Manim animations...")
    print(f"   Output: {output_path}")
    print(f"   Note: This requires Manim to be installed")
    
    success = await create_professional_scene_video(
        scene_data=scene_data,
        output_path=str(output_path),
        style='cinematic'
    )
    
    if success:
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ Professional Manim video generated!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"   Features: Mathematical animations with professional styling")
    else:
        print(f"\n⚠️  Manim video generation not available")
        print(f"   Install Manim: pip install manim")
        print(f"   Or check if it fell back to text video successfully")
    
    return success


def main():
    """Main test function."""
    
    print("\n🚀 RASO Professional Video Generation Test")
    print("=" * 60)
    print("This will generate professional-quality videos to compare")
    print("with your current basic output.")
    print("=" * 60)
    
    # Test basic professional video
    success1 = asyncio.run(test_professional_video())
    
    # Ask if user wants to test Manim
    print("\n" + "=" * 60)
    response = input("\n🧮 Test Manim integration? (requires Manim installed) [y/N]: ")
    
    if response.lower() in ['y', 'yes']:
        success2 = asyncio.run(test_with_equations())
    else:
        print("\nSkipping Manim test. Install with: pip install manim")
        success2 = True
    
    if success1:
        print("\n" + "=" * 60)
        print("✅ Professional video generation test completed!")
        print("\n📁 Output files:")
        print("   output/test_professional.mp4")
        if success2 and response.lower() in ['y', 'yes']:
            print("   output/test_professional_manim.mp4")
        print("\n🎬 Compare these with your current video output!")
        print("=" * 60)
    else:
        print("\n❌ Test failed. Check FFmpeg installation.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
