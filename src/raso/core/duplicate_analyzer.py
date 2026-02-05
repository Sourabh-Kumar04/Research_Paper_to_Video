#!/usr/bin/env python3
"""
Duplicate File Detection and Analysis for RASO Cleanup
Identifies and analyzes duplicate files, especially in src/agents/ directory.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from cleanup_infrastructure import FileAnalyzer, FileInfo

logger = logging.getLogger(__name__)


@dataclass
class DuplicateAnalysis:
    """Analysis results for duplicate files."""
    total_duplicates: int
    duplicate_groups: Dict[str, List[str]]
    size_savings: int
    recommendations: List[str]


class DuplicateAnalyzer:
    """Advanced duplicate file detection and analysis."""
    
    def __init__(self, root_path: Path):
        """Initialize duplicate analyzer."""
        self.root_path = Path(root_path)
        self.analyzer = FileAnalyzer(root_path)
    
    def analyze_duplicates(self) -> DuplicateAnalysis:
        """Perform comprehensive duplicate analysis."""
        logger.info("Starting duplicate file analysis")
        
        # Get file inventory
        inventory = self.analyzer.scan_directory()
        
        # Analyze duplicate groups
        total_duplicates = 0
        duplicate_groups = {}
        size_savings = 0
        recommendations = []
        
        for hash_val, files in inventory.duplicate_groups.items():
            if len(files) > 1:
                # Convert to file paths for easier handling
                file_paths = [str(f.path) for f in files]
                duplicate_groups[hash_val] = file_paths
                
                # Calculate potential size savings (keep one, remove others)
                file_size = files[0].size
                duplicates_count = len(files) - 1
                total_duplicates += duplicates_count
                size_savings += file_size * duplicates_count
                
                # Generate recommendations
                recommendation = self._generate_recommendation(files)
                if recommendation:
                    recommendations.append(recommendation)
        
        analysis = DuplicateAnalysis(
            total_duplicates=total_duplicates,
            duplicate_groups=duplicate_groups,
            size_savings=size_savings,
            recommendations=recommendations
        )
        
        logger.info(f"Duplicate analysis complete: {total_duplicates} duplicates found, "
                   f"{size_savings} bytes potential savings")
        
        return analysis
    
    def _generate_recommendation(self, duplicate_files: List[FileInfo]) -> str:
        """Generate recommendation for handling duplicate files."""
        paths = [str(f.path) for f in duplicate_files]
        
        # Special handling for src/agents/ duplicates
        agents_files = [p for p in paths if 'src/agents/' in p]
        if len(agents_files) > 1:
            # Recommend keeping the most recent or main version
            main_file = self._select_primary_agent_file(agents_files)
            others = [f for f in agents_files if f != main_file]
            return f"AGENTS: Keep '{main_file}', remove duplicates: {others}"
        
        # Handle backup files
        backup_files = [p for p in paths if '.backup' in p or '_backup' in p]
        if backup_files:
            non_backup = [p for p in paths if p not in backup_files]
            if non_backup:
                return f"BACKUP: Keep '{non_backup[0]}', remove backups: {backup_files}"
        
        # Handle test files
        test_files = [p for p in paths if 'test_' in Path(p).name]
        if len(test_files) > 1:
            # Keep test in tests/ directory, remove from root
            tests_dir_files = [p for p in test_files if 'tests/' in p]
            root_test_files = [p for p in test_files if 'tests/' not in p]
            if tests_dir_files and root_test_files:
                return f"TESTS: Keep '{tests_dir_files[0]}', remove from root: {root_test_files}"
        
        # Generic recommendation
        primary = paths[0]  # Keep first one by default
        others = paths[1:]
        return f"GENERIC: Keep '{primary}', remove duplicates: {others}"
    
    def _select_primary_agent_file(self, agent_files: List[str]) -> str:
        """Select the primary agent file to keep from duplicates."""
        # Priority order for agent files
        priorities = [
            lambda f: not ('backup' in f or '_backup' in f),  # Non-backup files first
            lambda f: not f.endswith('_old.py'),  # Non-old files
            lambda f: not f.startswith('simple_'),  # Non-simple versions
            lambda f: len(Path(f).name),  # Shorter names (often more generic)
        ]
        
        # Sort by priorities
        for priority_func in priorities:
            candidates = [f for f in agent_files if priority_func(f)]
            if len(candidates) == 1:
                return candidates[0]
            elif len(candidates) > 1:
                agent_files = candidates
        
        # If still multiple candidates, return the first one
        return agent_files[0]
    
    def get_agents_consolidation_plan(self) -> Dict[str, List[str]]:
        """Get specific consolidation plan for src/agents/ directory."""
        logger.info("Analyzing src/agents/ directory for consolidation")
        
        agents_path = self.root_path / "src" / "agents"
        if not agents_path.exists():
            logger.warning("src/agents/ directory not found")
            return {}
        
        # Get all Python files in agents directory
        agent_files = list(agents_path.glob("*.py"))
        
        # Group by functionality
        consolidation_groups = {
            "animation_generators": [],
            "video_composers": [],
            "audio_generators": [],
            "script_generators": [],
            "backup_files": [],
            "simple_versions": []
        }
        
        for file_path in agent_files:
            filename = file_path.name.lower()
            
            # Categorize files
            if 'backup' in filename or filename.endswith('_backup.py'):
                consolidation_groups["backup_files"].append(str(file_path.relative_to(self.root_path)))
            elif 'simple' in filename:
                consolidation_groups["simple_versions"].append(str(file_path.relative_to(self.root_path)))
            elif 'animation' in filename or 'manim' in filename:
                consolidation_groups["animation_generators"].append(str(file_path.relative_to(self.root_path)))
            elif 'composer' in filename or 'composition' in filename:
                consolidation_groups["video_composers"].append(str(file_path.relative_to(self.root_path)))
            elif 'audio' in filename or 'voice' in filename or 'tts' in filename:
                consolidation_groups["audio_generators"].append(str(file_path.relative_to(self.root_path)))
            elif 'script' in filename:
                consolidation_groups["script_generators"].append(str(file_path.relative_to(self.root_path)))
        
        # Remove empty groups
        consolidation_groups = {k: v for k, v in consolidation_groups.items() if v}
        
        logger.info(f"Agents consolidation plan: {len(consolidation_groups)} groups identified")
        return consolidation_groups


def main():
    """Main function for testing duplicate analysis."""
    root_path = Path(".")
    
    # Initialize analyzer
    duplicate_analyzer = DuplicateAnalyzer(root_path)
    
    # Analyze duplicates
    analysis = duplicate_analyzer.analyze_duplicates()
    
    # Save analysis results
    analysis_path = Path("duplicate_analysis.json")
    with open(analysis_path, 'w') as f:
        json.dump({
            'total_duplicates': analysis.total_duplicates,
            'duplicate_groups': analysis.duplicate_groups,
            'size_savings': analysis.size_savings,
            'recommendations': analysis.recommendations
        }, f, indent=2)
    
    # Get agents consolidation plan
    consolidation_plan = duplicate_analyzer.get_agents_consolidation_plan()
    
    # Save consolidation plan
    consolidation_path = Path("agents_consolidation_plan.json")
    with open(consolidation_path, 'w') as f:
        json.dump(consolidation_plan, f, indent=2)
    
    print(f"Duplicate analysis saved to {analysis_path}")
    print(f"Agents consolidation plan saved to {consolidation_path}")
    print(f"\nDuplicate Analysis Summary:")
    print(f"  - {analysis.total_duplicates} duplicate files found")
    print(f"  - {len(analysis.duplicate_groups)} duplicate groups")
    print(f"  - {analysis.size_savings:,} bytes potential savings")
    print(f"  - {len(analysis.recommendations)} recommendations generated")
    
    print(f"\nAgents Consolidation Summary:")
    for group, files in consolidation_plan.items():
        print(f"  - {group}: {len(files)} files")


if __name__ == "__main__":
    main()