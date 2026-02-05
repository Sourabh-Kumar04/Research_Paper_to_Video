#!/usr/bin/env python3
"""
RASO Video Generation Platform - Main Entry Point
Unified video pipeline with organized project structure.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path for proper imports
src_path = Path(__file__).parent / "src"
scripts_path = Path(__file__).parent / "scripts"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(scripts_path))

# Import the demo directly
from demo_unified_pipeline import UnifiedPipelineDemo

async def main():
    """Main entry point for the RASO platform."""
    print("🎬 RASO Video Generation Platform")
    print("=" * 50)
    print("📁 Project Structure: Organized")
    print("🔧 TypeScript Backend: src/backend/")
    print("🐍 Python Agents: src/agents/")
    print("📚 Documentation: docs/")
    print("📦 Output: output/")
    print("=" * 50)
    
    demo = UnifiedPipelineDemo()
    success = await demo.run_demo()
    
    if success:
        print("\n🎉 RASO Platform Demo Completed Successfully!")
        print("📁 Check the output/ directory for generated files.")
        print("📚 See docs/ for complete documentation.")
    else:
        print("\n💥 Demo failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())