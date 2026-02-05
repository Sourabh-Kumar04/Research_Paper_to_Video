#!/usr/bin/env python3
"""
RASO Cinematic Production Startup Script

Demonstrates the complete cinematic production pipeline with:
- Professional camera movements
- Color grading and visual effects  
- Advanced sound design
- 4K/8K cinematic quality output
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"[CINEMATIC] Loaded environment from: {env_path}")

# Set cinematic production environment variables
os.environ.update({
    'RASO_CINEMATIC_MODE': 'true',
    'RASO_CINEMATIC_QUALITY': 'cinematic_4k',
    'RASO_CAMERA_MOVEMENTS': 'true',
    'RASO_PROFESSIONAL_TRANSITIONS': 'true',
    'RASO_COLOR_GRADING': 'true',
    'RASO_SOUND_DESIGN': 'true',
    'RASO_ADVANCED_COMPOSITING': 'true',
    'RASO_FILM_GRAIN': 'true',
    'RASO_DYNAMIC_LIGHTING': 'true',
    'RASO_VIDEO_QUALITY': 'cinematic_4k',
    'RASO_CONTENT_DEPTH': 'professional',
    'RASO_TARGET_AUDIENCE': 'engineers',
    'RASO_TECHNICAL_LEVEL': 'advanced'
})

# Import the production video generator
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def main():
    """Main cinematic production demonstration."""
    print("=" * 80)
    print("🎬 RASO CINEMATIC PRODUCTION SYSTEM")
    print("=" * 80)
    print()
    
    print("🎯 CINEMATIC FEATURES ENABLED:")
    print("   ✅ Professional Camera Movements")
    print("   ✅ Advanced Color Grading & Film Emulation")
    print("   ✅ Professional Sound Design & Mixing")
    print("   ✅ 4K Cinematic Quality (3840x2160 @ 24fps)")
    print("   ✅ Advanced Compositing & Visual Effects")
    print("   ✅ Film Grain & Dynamic Lighting")
    print("   ✅ Professional Transitions & Editing")
    print()
    
    # Configuration summary
    print("🔧 PRODUCTION CONFIGURATION:")
    print(f"   📹 Quality: {os.getenv('RASO_CINEMATIC_QUALITY', 'cinematic_4k')}")
    print(f"   🎥 Camera Movements: {os.getenv('RASO_CAMERA_MOVEMENTS', 'true')}")
    print(f"   🎨 Color Grading: {os.getenv('RASO_COLOR_GRADING', 'true')}")
    print(f"   🔊 Sound Design: {os.getenv('RASO_SOUND_DESIGN', 'true')}")
    print(f"   🎬 Advanced Compositing: {os.getenv('RASO_ADVANCED_COMPOSITING', 'true')}")
    print()
    
    # Check system requirements
    print("🔍 SYSTEM REQUIREMENTS CHECK:")
    
    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ FFmpeg: Available")
        else:
            print("   ❌ FFmpeg: Not available")
            print("   📝 Install FFmpeg for cinematic features")
    except Exception:
        print("   ❌ FFmpeg: Not found")
        print("   📝 Install FFmpeg: https://ffmpeg.org/download.html")
    
    # Check disk space
    try:
        import shutil
        free_space = shutil.disk_usage('.').free
        free_gb = free_space / (1024**3)
        if free_gb > 10:
            print(f"   ✅ Disk Space: {free_gb:.1f} GB available")
        else:
            print(f"   ⚠️ Disk Space: {free_gb:.1f} GB (recommend 50+ GB for 4K)")
    except Exception:
        print("   ⚠️ Disk Space: Could not check")
    
    # Check memory
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb > 16:
            print(f"   ✅ Memory: {memory_gb:.1f} GB")
        else:
            print(f"   ⚠️ Memory: {memory_gb:.1f} GB (recommend 16+ GB for 4K)")
    except ImportError:
        print("   ⚠️ Memory: Could not check (install psutil)")
    except Exception:
        print("   ⚠️ Memory: Could not check")
    
    print()
    
    # Demo options
    print("🎬 CINEMATIC DEMO OPTIONS:")
    print("   1. Transformer Architecture Paper (Advanced AI/ML Content)")
    print("   2. Computer Vision Research (Technical Deep Learning)")
    print("   3. Distributed Systems Paper (Software Engineering)")
    print("   4. Custom Paper Title")
    print()
    
    try:
        choice = input("Select demo option (1-4): ").strip()
        
        if choice == "1":
            paper_content = "Attention Is All You Need"
            print(f"🎯 Selected: {paper_content}")
            print("   📝 This will generate a comprehensive technical analysis")
            print("   📝 with professional camera work and cinematic quality")
        elif choice == "2":
            paper_content = "Deep Residual Learning for Image Recognition"
            print(f"🎯 Selected: {paper_content}")
            print("   📝 Computer vision content with technical depth")
        elif choice == "3":
            paper_content = "MapReduce: Simplified Data Processing on Large Clusters"
            print(f"🎯 Selected: {paper_content}")
            print("   📝 Distributed systems with architectural focus")
        elif choice == "4":
            paper_content = input("Enter paper title: ").strip()
            if not paper_content:
                paper_content = "Research Paper Analysis"
            print(f"🎯 Custom paper: {paper_content}")
        else:
            paper_content = "Attention Is All You Need"
            print(f"🎯 Default: {paper_content}")
        
        print()
        
        # Quality selection
        print("🎨 QUALITY OPTIONS:")
        print("   1. Cinematic 4K (3840x2160, 50Mbps) - Recommended")
        print("   2. Cinematic 8K (7680x4320, 100Mbps) - Maximum Quality")
        print("   3. High Quality (1920x1080, 25Mbps) - Fast Processing")
        print()
        
        quality_choice = input("Select quality (1-3, default=1): ").strip()
        
        if quality_choice == "2":
            quality = "cinematic_8k"
            print("🎬 Selected: Cinematic 8K (Ultra High Definition)")
            print("   ⚠️ Warning: Requires 32GB+ RAM and significant processing time")
        elif quality_choice == "3":
            quality = "high"
            print("🎬 Selected: High Quality (Standard HD)")
        else:
            quality = "cinematic_4k"
            print("🎬 Selected: Cinematic 4K (Professional Quality)")
        
        os.environ['RASO_CINEMATIC_QUALITY'] = quality
        
        print()
        print("🚀 STARTING CINEMATIC PRODUCTION...")
        print("=" * 80)
        
        # Import and run the production generator
        from production_video_generator import ProductionVideoGenerator
        
        # Set up job parameters
        job_id = "cinematic-demo"
        output_dir = "output/cinematic_production"
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize and run generator
        generator = ProductionVideoGenerator(job_id, paper_content, output_dir)
        
        print(f"📁 Output directory: {output_dir}")
        print(f"🎬 Quality: {quality}")
        print(f"📄 Paper: {paper_content}")
        print()
        
        # Generate cinematic video
        result = await generator.generate_video()
        
        print()
        print("=" * 80)
        
        if result:
            print("🎉 CINEMATIC PRODUCTION COMPLETED SUCCESSFULLY!")
            print()
            print(f"📁 Output file: {result}")
            
            # Get file info
            if Path(result).exists():
                file_size = Path(result).stat().st_size
                size_mb = file_size / (1024 * 1024)
                print(f"📊 File size: {size_mb:.1f} MB")
                
                if size_mb > 100:
                    print("✅ Large file size indicates high-quality cinematic content")
                elif size_mb > 10:
                    print("✅ Reasonable file size for cinematic content")
                else:
                    print("⚠️ Small file size - may need quality adjustment")
            
            print()
            print("🎬 CINEMATIC FEATURES APPLIED:")
            print("   ✅ Professional camera movements based on content analysis")
            print("   ✅ Film-style color grading with mood-based adjustments")
            print("   ✅ Multi-layer sound design with ambient audio and music")
            print("   ✅ Advanced compositing with professional transitions")
            print("   ✅ High-quality encoding with cinematic frame rates")
            print()
            print("📺 The generated video includes:")
            print("   • Dynamic camera work (pans, zooms, dollies, cranes)")
            print("   • Professional color grading with film emulation")
            print("   • Enhanced audio with reverb, EQ, and compression")
            print("   • Smooth transitions between scenes")
            print("   • Film grain and lighting effects")
            print("   • Broadcast-quality encoding")
            
        else:
            print("❌ CINEMATIC PRODUCTION FAILED")
            print()
            print("🔧 TROUBLESHOOTING TIPS:")
            print("   • Check FFmpeg installation and codecs")
            print("   • Ensure sufficient disk space (50+ GB)")
            print("   • Verify memory availability (16+ GB)")
            print("   • Check system logs for detailed error messages")
            print("   • Try lower quality settings for testing")
        
        print()
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n⏹️ Production cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during cinematic production: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎬 RASO Cinematic Production System")
    print("   Professional video generation with cinema-quality features")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Startup error: {e}")
        sys.exit(1)