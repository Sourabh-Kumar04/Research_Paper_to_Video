#!/usr/bin/env python3
"""
RASO Video Generation Platform - Main Entry Point
Unified video pipeline with organized project structure.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root and scripts to Python path
project_root = Path(__file__).parent.parent.parent.parent
scripts_path = project_root / "scripts"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(scripts_path))

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