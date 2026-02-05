#!/usr/bin/env python3
"""
Fix import statements in the RASO codebase.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Fix import statements in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix utils.ai_model_manager imports (it's actually in scripts.utils)
        content = re.sub(
            r'from utils\.ai_model_manager import',
            'from scripts.utils.ai_model_manager import',
            content
        )
        
        # Fix backend.services imports
        content = re.sub(
            r'from backend\.services\.(\w+) import',
            r'from config.backend.services.\1 import',
            content
        )
        
        # Fix backend.config imports
        content = re.sub(
            r'from backend\.config import',
            'from config.backend.config import',
            content
        )
        
        # Fix backend.models imports
        content = re.sub(
            r'from backend\.models import',
            'from config.backend.models import',
            content
        )
        
        # Fix specific backend.models.* imports
        content = re.sub(
            r'from backend\.models\.(\w+) import',
            r'from config.backend.models.\1 import',
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed imports in {file_path}")
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

def main():
    """Main function to fix all imports."""
    print("🔧 Fixing import statements in RASO codebase...")
    
    # Files that need fixing based on the search results
    files_to_fix = [
        "src/video/composition.py",
        "src/graph/workflow.py", 
        "src/agents/base.py",
        "src/animation/templates.py",
        "src/agents/rendering.py",
        "src/agents/logging.py",
        "src/agents/ingest.py",
        "src/audio/tts_service.py",
        "src/graph/master_workflow.py",
        "config/backend/services/llm.py",
        "src/agents/metadata.py",
        "src/agents/script_enhanced.py",
        "src/agents/understanding.py",
        "src/agents/visual_planning.py",
        "src/agents/audio.py",
        "src/agents/script_enhanced.py"
    ]
    
    for file_path_str in files_to_fix:
        file_path = Path(file_path_str)
        if file_path.exists():
            fix_imports_in_file(file_path)
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print("✅ Import fixing complete!")

if __name__ == "__main__":
    main()