#!/usr/bin/env python3
"""
Structure Reorganizer for RASO Codebase
Implements Python src-layout structure and organizes files according to industry standards.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import ast
import re

logger = logging.getLogger(__name__)


@dataclass
class StructureResult:
    """Results of structure reorganization operations."""
    directories_created: int
    files_moved: int
    imports_updated: int
    errors: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'directories_created': self.directories_created,
            'files_moved': self.files_moved,
            'imports_updated': self.imports_updated,
            'errors': self.errors
        }


@dataclass
class FileMapping:
    """Mapping of source to destination file paths."""
    source: Path
    destination: Path
    category: str
    
    def __str__(self) -> str:
        return f"{self.source} -> {self.destination} ({self.category})"


class StructureReorganizer:
    """Reorganizes project structure to follow Python src-layout standards."""
    
    def __init__(self, root_path: Path, dry_run: bool = False):
        """Initialize structure reorganizer."""
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        
        # Target structure following src-layout
        self.target_structure = {
            'src/raso/core/': 'Core business logic and main functionality',
            'src/raso/agents/': 'Cleaned and organized agent implementations',
            'src/raso/services/': 'External service integrations (LLM, TTS, etc.)',
            'src/raso/utils/': 'Utility functions and helpers',
            'src/raso/config/': 'Configuration management',
            'tests/unit/': 'Unit tests',
            'tests/integration/': 'Integration tests',
            'tests/property/': 'Property-based tests',
            'docs/api/': 'API documentation',
            'docs/deployment/': 'Deployment guides',
            'docs/development/': 'Development documentation',
            'scripts/': 'Production scripts and utilities'
        }
        
    def create_src_layout(self) -> StructureResult:
        """Create the new src-layout directory structure."""
        logger.info("Creating src-layout directory structure")
        
        directories_created = 0
        errors = []
        
        # Create target directories
        for dir_path, description in self.target_structure.items():
            try:
                full_path = self.root_path / dir_path
                
                if self.dry_run:
                    logger.info(f"DRY RUN: Would create directory {dir_path}")
                    directories_created += 1
                else:
                    full_path.mkdir(parents=True, exist_ok=True)
                    
                    # Create __init__.py for Python packages
                    if 'src/raso' in dir_path and dir_path.endswith('/'):
                        init_file = full_path / '__init__.py'
                        if not init_file.exists():
                            init_file.write_text(f'"""{description}"""\n')
                    
                    directories_created += 1
                    logger.debug(f"Created directory: {dir_path}")
                    
            except Exception as e:
                error_msg = f"Failed to create directory {dir_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Create root package __init__.py
        try:
            if not self.dry_run:
                root_init = self.root_path / 'src' / 'raso' / '__init__.py'
                if not root_init.exists():
                    root_init.write_text('"""RASO - Research paper Automated Simulation & Orchestration Platform"""\n\n__version__ = "1.0.0"\n')
                    logger.info("Created root package __init__.py")
        except Exception as e:
            error_msg = f"Failed to create root __init__.py: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        result = StructureResult(
            directories_created=directories_created,
            files_moved=0,
            imports_updated=0,
            errors=errors
        )
        
        logger.info(f"Structure creation complete: {directories_created} directories created")
        return result
    
    def analyze_current_structure(self) -> Dict[str, List[Path]]:
        """Analyze current file organization and categorize files."""
        logger.info("Analyzing current project structure")
        
        categories = {
            'agents': [],
            'services': [],
            'utils': [],
            'config': [],
            'tests': [],
            'docs': [],
            'scripts': [],
            'core': []
        }
        
        # Analyze src/ directory
        src_path = self.root_path / 'src'
        if src_path.exists():
            for file_path in src_path.rglob('*.py'):
                relative_path = file_path.relative_to(src_path)
                category = self._categorize_source_file(file_path, relative_path)
                categories[category].append(file_path)
        
        # Analyze root-level Python files
        for file_path in self.root_path.glob('*.py'):
            if file_path.name not in ['setup.py', 'conftest.py']:
                category = self._categorize_source_file(file_path, file_path.name)
                categories[category].append(file_path)
        
        # Analyze tests
        tests_path = self.root_path / 'tests'
        if tests_path.exists():
            for file_path in tests_path.rglob('*.py'):
                categories['tests'].append(file_path)
        
        # Analyze docs
        docs_path = self.root_path / 'docs'
        if docs_path.exists():
            for file_path in docs_path.rglob('*.md'):
                categories['docs'].append(file_path)
        
        # Analyze scripts
        scripts_path = self.root_path / 'scripts'
        if scripts_path.exists():
            for file_path in scripts_path.rglob('*.py'):
                categories['scripts'].append(file_path)
        
        logger.info(f"File analysis complete: {sum(len(files) for files in categories.values())} files categorized")
        return categories
    
    def _categorize_source_file(self, file_path: Path, relative_path: Path) -> str:
        """Categorize a source file based on its path and content."""
        path_str = str(relative_path).lower()
        filename = file_path.name.lower()
        
        # Agent files
        if 'agent' in path_str or filename.endswith('_agent.py'):
            return 'agents'
        
        # Service integrations
        if any(service in path_str for service in ['llm', 'tts', 'gemini', 'openai', 'anthropic', 'audio', 'voice']):
            return 'services'
        
        # Configuration
        if any(config in path_str for config in ['config', 'settings', 'env']):
            return 'config'
        
        # Utilities
        if any(util in path_str for util in ['util', 'helper', 'tool', 'common']):
            return 'utils'
        
        # Core functionality (main business logic)
        if any(core in path_str for core in ['graph', 'workflow', 'pipeline', 'orchestrat', 'main']):
            return 'core'
        
        # Default to core for unclassified files
        return 'core'
    
    def generate_file_mappings(self) -> List[FileMapping]:
        """Generate mappings from current files to new structure."""
        logger.info("Generating file mappings for reorganization")
        
        categories = self.analyze_current_structure()
        mappings = []
        
        # Map source files to new structure
        for category, files in categories.items():
            if category == 'tests':
                # Organize tests by type
                for file_path in files:
                    if 'property' in file_path.name or 'pbt' in file_path.name:
                        dest = self.root_path / 'tests' / 'property' / file_path.name
                    elif 'integration' in file_path.name or 'e2e' in file_path.name:
                        dest = self.root_path / 'tests' / 'integration' / file_path.name
                    else:
                        dest = self.root_path / 'tests' / 'unit' / file_path.name
                    
                    mappings.append(FileMapping(file_path, dest, 'test'))
                    
            elif category == 'docs':
                # Organize documentation
                for file_path in files:
                    if 'api' in file_path.name.lower():
                        dest = self.root_path / 'docs' / 'api' / file_path.name
                    elif any(deploy in file_path.name.lower() for deploy in ['deploy', 'setup', 'install']):
                        dest = self.root_path / 'docs' / 'deployment' / file_path.name
                    else:
                        dest = self.root_path / 'docs' / 'development' / file_path.name
                    
                    mappings.append(FileMapping(file_path, dest, 'documentation'))
                    
            elif category == 'scripts':
                # Keep scripts in scripts/ directory
                for file_path in files:
                    dest = self.root_path / 'scripts' / file_path.name
                    mappings.append(FileMapping(file_path, dest, 'script'))
                    
            else:
                # Source files go to src/raso/{category}/
                for file_path in files:
                    dest = self.root_path / 'src' / 'raso' / category / file_path.name
                    mappings.append(FileMapping(file_path, dest, category))
        
        logger.info(f"Generated {len(mappings)} file mappings")
        return mappings
    
    def move_files(self, mappings: List[FileMapping]) -> StructureResult:
        """Move files according to the generated mappings."""
        logger.info(f"Moving {len(mappings)} files to new structure")
        
        files_moved = 0
        errors = []
        
        for mapping in mappings:
            try:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would move {mapping}")
                    files_moved += 1
                else:
                    # Create destination directory
                    mapping.destination.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(str(mapping.source), str(mapping.destination))
                    files_moved += 1
                    logger.debug(f"Moved: {mapping}")
                    
            except Exception as e:
                error_msg = f"Failed to move {mapping.source} to {mapping.destination}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = StructureResult(
            directories_created=0,
            files_moved=files_moved,
            imports_updated=0,
            errors=errors
        )
        
        logger.info(f"File movement complete: {files_moved} files moved")
        return result
    
    def update_imports(self, mappings: List[FileMapping]) -> int:
        """Update import statements to match new structure."""
        logger.info("Updating import statements")
        
        imports_updated = 0
        
        # Create mapping of old paths to new module paths
        path_mapping = {}
        for mapping in mappings:
            if mapping.destination.suffix == '.py':
                # Convert file path to module path
                rel_path = mapping.destination.relative_to(self.root_path)
                if str(rel_path).startswith('src/'):
                    # Remove src/ prefix and .py suffix, replace / with .
                    module_path = str(rel_path)[4:-3].replace('/', '.')
                    old_module = mapping.source.stem
                    path_mapping[old_module] = module_path
        
        # Update imports in all Python files
        for mapping in mappings:
            if mapping.destination.suffix == '.py':
                try:
                    imports_updated += self._update_file_imports(mapping.destination, path_mapping)
                except Exception as e:
                    logger.error(f"Failed to update imports in {mapping.destination}: {e}")
        
        logger.info(f"Import updates complete: {imports_updated} imports updated")
        return imports_updated
    
    def _update_file_imports(self, file_path: Path, path_mapping: Dict[str, str]) -> int:
        """Update imports in a single file."""
        if self.dry_run:
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            updates = 0
            
            # Update import statements
            for old_module, new_module in path_mapping.items():
                # Handle different import patterns
                patterns = [
                    (rf'from {re.escape(old_module)} import', f'from {new_module} import'),
                    (rf'import {re.escape(old_module)}', f'import {new_module}'),
                    (rf'from \.{re.escape(old_module)} import', f'from .{new_module.split(".")[-1]} import'),
                ]
                
                for pattern, replacement in patterns:
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        content = new_content
                        updates += 1
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.debug(f"Updated {updates} imports in {file_path}")
            
            return updates
            
        except Exception as e:
            logger.error(f"Error updating imports in {file_path}: {e}")
            return 0
    
    def reorganize_project(self) -> StructureResult:
        """Execute complete project reorganization."""
        logger.info("Starting complete project reorganization")
        
        # Step 1: Create new structure
        structure_result = self.create_src_layout()
        
        # Step 2: Generate file mappings
        mappings = self.generate_file_mappings()
        
        # Step 3: Move files
        move_result = self.move_files(mappings)
        
        # Step 4: Update imports
        imports_updated = self.update_imports(mappings)
        
        # Combine results
        final_result = StructureResult(
            directories_created=structure_result.directories_created,
            files_moved=move_result.files_moved,
            imports_updated=imports_updated,
            errors=structure_result.errors + move_result.errors
        )
        
        logger.info(f"Project reorganization complete: {final_result.directories_created} dirs created, "
                   f"{final_result.files_moved} files moved, {final_result.imports_updated} imports updated")
        
        return final_result


def main():
    """Main function for testing structure reorganizer."""
    root_path = Path(".")
    
    # Initialize reorganizer in dry run mode
    reorganizer = StructureReorganizer(root_path, dry_run=True)
    
    print("🏗️ RASO Structure Reorganizer")
    print("=" * 50)
    
    # Analyze current structure
    print("\n📊 Analyzing current structure...")
    categories = reorganizer.analyze_current_structure()
    
    for category, files in categories.items():
        if files:
            print(f"  • {category}: {len(files)} files")
    
    # Generate mappings
    print(f"\n📋 Generating file mappings...")
    mappings = reorganizer.generate_file_mappings()
    
    print(f"  • Generated {len(mappings)} file mappings")
    
    # Show sample mappings
    print(f"\n📝 Sample mappings:")
    for mapping in mappings[:5]:
        print(f"  • {mapping}")
    
    # Test reorganization (dry run)
    print(f"\n🚀 Testing reorganization (dry run)...")
    result = reorganizer.reorganize_project()
    
    print(f"  ✅ Would create {result.directories_created} directories")
    print(f"  ✅ Would move {result.files_moved} files")
    print(f"  ✅ Would update {result.imports_updated} imports")
    
    if result.errors:
        print(f"  ⚠️ {len(result.errors)} errors would occur:")
        for error in result.errors[:3]:
            print(f"    • {error}")


if __name__ == "__main__":
    main()