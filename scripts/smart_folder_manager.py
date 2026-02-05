"""
Smart Folder Naming and Organization Manager

This module provides intelligent folder naming and organization capabilities
for research papers and generated content, with conflict resolution and
custom naming templates.
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import unicodedata
import logging

logger = logging.getLogger(__name__)

@dataclass
class PaperMetadata:
    """Metadata for research papers"""
    title: str
    authors: List[str]
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

@dataclass
class FolderNamingConfig:
    """Configuration for folder naming templates"""
    template: str = "{year}/{first_author}_{sanitized_title}"
    max_title_length: int = 50
    max_author_length: int = 30
    conflict_resolution: str = "append_number"  # "append_number", "append_timestamp", "manual"
    custom_templates: Dict[str, str] = None
    
    def __post_init__(self):
        if self.custom_templates is None:
            self.custom_templates = {}

class SmartFolderManager:
    """
    Manages intelligent folder naming and organization for research papers
    """
    
    def __init__(self, base_path: str = "papers", config: Optional[FolderNamingConfig] = None):
        self.base_path = Path(base_path)
        self.config = config or FolderNamingConfig()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing folder mappings
        self.mapping_file = self.base_path / "folder_mappings.json"
        self.folder_mappings = self._load_folder_mappings()
        
    def _load_folder_mappings(self) -> Dict[str, Dict]:
        """Load existing folder mappings from disk"""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load folder mappings: {e}")
        return {}
    
    def _save_folder_mappings(self):
        """Save folder mappings to disk"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.folder_mappings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save folder mappings: {e}")
    
    def sanitize_filename(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text for use in filenames and folder names
        
        Args:
            text: Text to sanitize
            max_length: Maximum length (optional)
            
        Returns:
            Sanitized text safe for filesystem use
        """
        if not text:
            return "untitled"
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove or replace problematic characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)  # Remove invalid filename chars
        text = re.sub(r'[^\w\s\-_.]', '', text)   # Keep only alphanumeric, spaces, hyphens, underscores, dots
        text = re.sub(r'\s+', '_', text.strip())  # Replace spaces with underscores
        text = re.sub(r'_+', '_', text)           # Collapse multiple underscores
        text = text.strip('_.')                   # Remove leading/trailing underscores and dots
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length].rstrip('_.')
        
        return text or "untitled"
    
    def extract_first_author(self, authors: List[str]) -> str:
        """
        Extract and sanitize the first author's last name
        
        Args:
            authors: List of author names
            
        Returns:
            Sanitized first author's last name
        """
        if not authors:
            return "Unknown_Author"
        
        first_author = authors[0].strip()
        
        # Try to extract last name (assume "First Last" or "Last, First" format)
        if ',' in first_author:
            # "Last, First" format
            last_name = first_author.split(',')[0].strip()
        else:
            # "First Last" format - take the last word
            parts = first_author.split()
            last_name = parts[-1] if parts else first_author
        
        return self.sanitize_filename(last_name, self.config.max_author_length)
    
    def generate_folder_name(self, metadata: PaperMetadata, template: Optional[str] = None) -> str:
        """
        Generate folder name based on paper metadata and template
        
        Args:
            metadata: Paper metadata
            template: Custom template (optional, uses config default)
            
        Returns:
            Generated folder name
        """
        template = template or self.config.template
        
        # Prepare template variables
        variables = {
            'year': metadata.year or datetime.now().year,
            'first_author': self.extract_first_author(metadata.authors),
            'sanitized_title': self.sanitize_filename(metadata.title, self.config.max_title_length),
            'venue': self.sanitize_filename(metadata.venue or "unknown_venue"),
            'doi_hash': self.sanitize_filename(metadata.doi or "")[:10] if metadata.doi else "",
        }
        
        try:
            folder_name = template.format(**variables)
            return self.sanitize_filename(folder_name)
        except KeyError as e:
            logger.warning(f"Template variable {e} not found, using default template")
            return self.generate_folder_name(metadata, self.config.template)
    
    def resolve_conflicts(self, folder_path: Path, metadata: PaperMetadata) -> Path:
        """
        Resolve folder name conflicts
        
        Args:
            folder_path: Proposed folder path
            metadata: Paper metadata
            
        Returns:
            Resolved folder path
        """
        if not folder_path.exists():
            return folder_path
        
        if self.config.conflict_resolution == "append_number":
            counter = 1
            base_path = folder_path
            while folder_path.exists():
                folder_path = base_path.parent / f"{base_path.name}_{counter:02d}"
                counter += 1
                
        elif self.config.conflict_resolution == "append_timestamp":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_path = folder_path.parent / f"{folder_path.name}_{timestamp}"
            
        elif self.config.conflict_resolution == "manual":
            # For manual resolution, return the conflicting path and let caller handle
            logger.warning(f"Folder conflict detected: {folder_path}")
            return folder_path
        
        return folder_path
    
    def create_paper_folder(self, metadata: PaperMetadata, template: Optional[str] = None) -> Tuple[Path, bool]:
        """
        Create folder for a research paper
        
        Args:
            metadata: Paper metadata
            template: Custom template (optional)
            
        Returns:
            Tuple of (folder_path, was_created)
        """
        folder_name = self.generate_folder_name(metadata, template)
        folder_path = self.base_path / folder_name
        
        # Resolve conflicts
        resolved_path = self.resolve_conflicts(folder_path, metadata)
        
        # Create folder structure
        was_created = False
        if not resolved_path.exists():
            resolved_path.mkdir(parents=True, exist_ok=True)
            was_created = True
            
            # Create standard subdirectories
            subdirs = [
                "videos/final",
                "videos/scenes", 
                "videos/drafts",
                "audio/narration",
                "audio/music",
                "audio/effects",
                "visuals/animations",
                "visuals/slides",
                "visuals/diagrams",
                "code/manim",
                "code/motion_canvas",
                "code/remotion",
                "metadata"
            ]
            
            for subdir in subdirs:
                (resolved_path / subdir).mkdir(parents=True, exist_ok=True)
            
            # Save metadata
            metadata_file = resolved_path / "metadata" / "paper_info.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)
        
        # Update folder mappings
        paper_id = self._generate_paper_id(metadata)
        self.folder_mappings[paper_id] = {
            'folder_path': str(resolved_path.relative_to(self.base_path)),
            'metadata': asdict(metadata),
            'created_at': datetime.now().isoformat(),
            'template_used': template or self.config.template
        }
        self._save_folder_mappings()
        
        logger.info(f"Paper folder {'created' if was_created else 'exists'}: {resolved_path}")
        return resolved_path, was_created
    
    def _generate_paper_id(self, metadata: PaperMetadata) -> str:
        """Generate unique paper ID from metadata"""
        if metadata.doi:
            return f"doi_{self.sanitize_filename(metadata.doi)}"
        
        # Use title + first author as fallback
        title_part = self.sanitize_filename(metadata.title)[:20]
        author_part = self.extract_first_author(metadata.authors)[:10]
        return f"{author_part}_{title_part}"
    
    def find_paper_folder(self, metadata: PaperMetadata) -> Optional[Path]:
        """
        Find existing folder for a paper
        
        Args:
            metadata: Paper metadata
            
        Returns:
            Path to existing folder or None
        """
        paper_id = self._generate_paper_id(metadata)
        
        if paper_id in self.folder_mappings:
            folder_path = self.base_path / self.folder_mappings[paper_id]['folder_path']
            if folder_path.exists():
                return folder_path
        
        # Fallback: search by generated folder name
        folder_name = self.generate_folder_name(metadata)
        potential_path = self.base_path / folder_name
        if potential_path.exists():
            return potential_path
        
        return None
    
    def list_paper_folders(self) -> List[Dict]:
        """
        List all paper folders with metadata
        
        Returns:
            List of folder information dictionaries
        """
        folders = []
        for paper_id, info in self.folder_mappings.items():
            folder_path = self.base_path / info['folder_path']
            if folder_path.exists():
                folders.append({
                    'paper_id': paper_id,
                    'folder_path': folder_path,
                    'metadata': info['metadata'],
                    'created_at': info['created_at'],
                    'template_used': info.get('template_used', 'default')
                })
        
        return sorted(folders, key=lambda x: x['created_at'], reverse=True)
    
    def update_naming_template(self, template_name: str, template: str):
        """
        Add or update a custom naming template
        
        Args:
            template_name: Name for the template
            template: Template string with variables
        """
        self.config.custom_templates[template_name] = template
        logger.info(f"Updated template '{template_name}': {template}")
    
    def get_folder_stats(self) -> Dict:
        """
        Get statistics about folder organization
        
        Returns:
            Dictionary with folder statistics
        """
        stats = {
            'total_papers': len(self.folder_mappings),
            'folders_by_year': {},
            'folders_by_author': {},
            'total_size_mb': 0,
            'templates_used': {}
        }
        
        for info in self.folder_mappings.values():
            # Count by year
            year = info['metadata'].get('year', 'unknown')
            stats['folders_by_year'][year] = stats['folders_by_year'].get(year, 0) + 1
            
            # Count by first author
            authors = info['metadata'].get('authors', [])
            if authors:
                first_author = self.extract_first_author(authors)
                stats['folders_by_author'][first_author] = stats['folders_by_author'].get(first_author, 0) + 1
            
            # Count template usage
            template = info.get('template_used', 'default')
            stats['templates_used'][template] = stats['templates_used'].get(template, 0) + 1
            
            # Calculate folder size
            folder_path = self.base_path / info['folder_path']
            if folder_path.exists():
                try:
                    size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
                    stats['total_size_mb'] += size / (1024 * 1024)
                except Exception as e:
                    logger.warning(f"Failed to calculate size for {folder_path}: {e}")
        
        return stats

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    manager = SmartFolderManager()
    
    # Test paper metadata
    paper = PaperMetadata(
        title="Attention Is All You Need: Transformers for Natural Language Processing",
        authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        year=2017,
        doi="10.48550/arXiv.1706.03762",
        venue="NIPS",
        keywords=["transformers", "attention", "nlp"]
    )
    
    # Create folder
    folder_path, created = manager.create_paper_folder(paper)
    print(f"Folder: {folder_path}, Created: {created}")
    
    # Get stats
    stats = manager.get_folder_stats()
    print(f"Stats: {stats}")