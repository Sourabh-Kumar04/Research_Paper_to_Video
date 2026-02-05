"""
Asset Relationship Mapper

This module provides comprehensive asset relationship mapping capabilities,
linking audio files to video scenes, mapping generated code to visual outputs,
tracking model usage and performance per asset, and managing dependencies
for regeneration.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AssetType(Enum):
    """Types of assets in the system"""
    VIDEO = "video"
    AUDIO = "audio"
    SCRIPT = "script"
    ANIMATION = "animation"
    CODE = "code"
    IMAGE = "image"
    METADATA = "metadata"
    MODEL_OUTPUT = "model_output"

class RelationshipType(Enum):
    """Types of relationships between assets"""
    DEPENDS_ON = "depends_on"
    GENERATES = "generates"
    USES = "uses"
    DERIVED_FROM = "derived_from"
    SYNCHRONIZED_WITH = "synchronized_with"
    REFERENCES = "references"
    CONTAINS = "contains"

@dataclass
class Asset:
    """Represents an asset in the system"""
    asset_id: str
    asset_type: AssetType
    file_path: str
    created_at: str
    file_hash: str
    file_size: int
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []

@dataclass
class Relationship:
    """Represents a relationship between assets"""
    relationship_id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: RelationshipType
    created_at: str
    metadata: Dict[str, Any] = None
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ModelUsage:
    """Tracks model usage for asset generation"""
    model_name: str
    model_version: str
    usage_count: int
    total_generation_time: float
    average_generation_time: float
    success_rate: float
    last_used: str
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}

@dataclass
class DependencyChain:
    """Represents a chain of dependencies"""
    root_asset_id: str
    chain: List[str]  # List of asset IDs in dependency order
    total_depth: int
    circular_dependencies: List[List[str]] = None
    
    def __post_init__(self):
        if self.circular_dependencies is None:
            self.circular_dependencies = []

class AssetRelationshipMapper:
    """
    Manages asset relationships and dependencies
    """
    
    def __init__(self, base_path: str = "asset_relationships"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.assets_file = self.base_path / "assets.json"
        self.relationships_file = self.base_path / "relationships.json"
        self.model_usage_file = self.base_path / "model_usage.json"
        
        # Load existing data
        self.assets = self._load_assets()
        self.relationships = self._load_relationships()
        self.model_usage = self._load_model_usage()
        
        # Relationship index for fast lookups
        self._build_relationship_index()
    
    def _load_assets(self) -> Dict[str, Asset]:
        """Load assets from disk"""
        if self.assets_file.exists():
            try:
                with open(self.assets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        asset_id: Asset(
                            asset_id=asset_data['asset_id'],
                            asset_type=AssetType(asset_data['asset_type']),
                            file_path=asset_data['file_path'],
                            created_at=asset_data['created_at'],
                            file_hash=asset_data['file_hash'],
                            file_size=asset_data['file_size'],
                            metadata=asset_data.get('metadata', {}),
                            tags=asset_data.get('tags', [])
                        )
                        for asset_id, asset_data in data.items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load assets: {e}")
        return {}
    
    def _load_relationships(self) -> Dict[str, Relationship]:
        """Load relationships from disk"""
        if self.relationships_file.exists():
            try:
                with open(self.relationships_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        rel_id: Relationship(
                            relationship_id=rel_data['relationship_id'],
                            source_asset_id=rel_data['source_asset_id'],
                            target_asset_id=rel_data['target_asset_id'],
                            relationship_type=RelationshipType(rel_data['relationship_type']),
                            created_at=rel_data['created_at'],
                            metadata=rel_data.get('metadata', {}),
                            strength=rel_data.get('strength', 1.0)
                        )
                        for rel_id, rel_data in data.items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load relationships: {e}")
        return {}
    
    def _load_model_usage(self) -> Dict[str, ModelUsage]:
        """Load model usage data from disk"""
        if self.model_usage_file.exists():
            try:
                with open(self.model_usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        model_key: ModelUsage(**usage_data)
                        for model_key, usage_data in data.items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load model usage: {e}")
        return {}
    
    def _save_assets(self):
        """Save assets to disk"""
        try:
            data = {
                asset_id: {
                    'asset_id': asset.asset_id,
                    'asset_type': asset.asset_type.value,
                    'file_path': asset.file_path,
                    'created_at': asset.created_at,
                    'file_hash': asset.file_hash,
                    'file_size': asset.file_size,
                    'metadata': asset.metadata,
                    'tags': asset.tags
                }
                for asset_id, asset in self.assets.items()
            }
            with open(self.assets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save assets: {e}")
    
    def _save_relationships(self):
        """Save relationships to disk"""
        try:
            data = {
                rel_id: {
                    'relationship_id': rel.relationship_id,
                    'source_asset_id': rel.source_asset_id,
                    'target_asset_id': rel.target_asset_id,
                    'relationship_type': rel.relationship_type.value,
                    'created_at': rel.created_at,
                    'metadata': rel.metadata,
                    'strength': rel.strength
                }
                for rel_id, rel in self.relationships.items()
            }
            with open(self.relationships_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save relationships: {e}")
    
    def _save_model_usage(self):
        """Save model usage data to disk"""
        try:
            data = {
                model_key: asdict(usage)
                for model_key, usage in self.model_usage.items()
            }
            with open(self.model_usage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save model usage: {e}")
    
    def _build_relationship_index(self):
        """Build indexes for fast relationship lookups"""
        self.source_index = {}  # source_asset_id -> [relationship_ids]
        self.target_index = {}  # target_asset_id -> [relationship_ids]
        
        for rel_id, relationship in self.relationships.items():
            # Index by source
            if relationship.source_asset_id not in self.source_index:
                self.source_index[relationship.source_asset_id] = []
            self.source_index[relationship.source_asset_id].append(rel_id)
            
            # Index by target
            if relationship.target_asset_id not in self.target_index:
                self.target_index[relationship.target_asset_id] = []
            self.target_index[relationship.target_asset_id].append(rel_id)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _generate_asset_id(self, asset_type: AssetType, file_path: str) -> str:
        """Generate unique asset ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        content_hash = hashlib.md5(f"{asset_type.value}_{file_path}_{timestamp}".encode()).hexdigest()[:8]
        return f"{asset_type.value}_{timestamp}_{content_hash}"
    
    def _generate_relationship_id(self, source_id: str, target_id: str, rel_type: RelationshipType) -> str:
        """Generate unique relationship ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        content_hash = hashlib.md5(f"{source_id}_{target_id}_{rel_type.value}_{timestamp}".encode()).hexdigest()[:8]
        return f"rel_{timestamp}_{content_hash}"
    
    def register_asset(self, 
                      asset_type: AssetType,
                      file_path: str,
                      metadata: Optional[Dict[str, Any]] = None,
                      tags: Optional[List[str]] = None) -> Asset:
        """
        Register a new asset in the system
        
        Args:
            asset_type: Type of the asset
            file_path: Path to the asset file
            metadata: Additional metadata
            tags: Tags for categorization
            
        Returns:
            Asset object
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Asset file not found: {file_path}")
        
        # Generate asset ID
        asset_id = self._generate_asset_id(asset_type, str(file_path))
        
        # Calculate file properties
        file_hash = self._calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        
        # Create asset
        asset = Asset(
            asset_id=asset_id,
            asset_type=asset_type,
            file_path=str(file_path),
            created_at=datetime.now().isoformat(),
            file_hash=file_hash,
            file_size=file_size,
            metadata=metadata or {},
            tags=tags or []
        )
        
        # Store asset
        self.assets[asset_id] = asset
        self._save_assets()
        
        logger.info(f"Registered asset: {asset_id} ({asset_type.value})")
        return asset
    
    def create_relationship(self,
                          source_asset_id: str,
                          target_asset_id: str,
                          relationship_type: RelationshipType,
                          metadata: Optional[Dict[str, Any]] = None,
                          strength: float = 1.0) -> Relationship:
        """
        Create a relationship between two assets
        
        Args:
            source_asset_id: Source asset ID
            target_asset_id: Target asset ID
            relationship_type: Type of relationship
            metadata: Additional metadata
            strength: Relationship strength (0.0 to 1.0)
            
        Returns:
            Relationship object
        """
        if source_asset_id not in self.assets:
            raise ValueError(f"Source asset not found: {source_asset_id}")
        
        if target_asset_id not in self.assets:
            raise ValueError(f"Target asset not found: {target_asset_id}")
        
        # Generate relationship ID
        rel_id = self._generate_relationship_id(source_asset_id, target_asset_id, relationship_type)
        
        # Create relationship
        relationship = Relationship(
            relationship_id=rel_id,
            source_asset_id=source_asset_id,
            target_asset_id=target_asset_id,
            relationship_type=relationship_type,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {},
            strength=strength
        )
        
        # Store relationship
        self.relationships[rel_id] = relationship
        self._build_relationship_index()  # Rebuild index
        self._save_relationships()
        
        logger.info(f"Created relationship: {source_asset_id} -> {target_asset_id} ({relationship_type.value})")
        return relationship
    
    def get_asset_dependencies(self, asset_id: str) -> List[Asset]:
        """
        Get all assets that the given asset depends on
        
        Args:
            asset_id: Asset ID
            
        Returns:
            List of dependency assets
        """
        dependencies = []
        
        if asset_id in self.source_index:
            for rel_id in self.source_index[asset_id]:
                relationship = self.relationships[rel_id]
                if relationship.relationship_type == RelationshipType.DEPENDS_ON:
                    target_asset = self.assets.get(relationship.target_asset_id)
                    if target_asset:
                        dependencies.append(target_asset)
        
        return dependencies
    
    def get_asset_dependents(self, asset_id: str) -> List[Asset]:
        """
        Get all assets that depend on the given asset
        
        Args:
            asset_id: Asset ID
            
        Returns:
            List of dependent assets
        """
        dependents = []
        
        if asset_id in self.target_index:
            for rel_id in self.target_index[asset_id]:
                relationship = self.relationships[rel_id]
                if relationship.relationship_type == RelationshipType.DEPENDS_ON:
                    source_asset = self.assets.get(relationship.source_asset_id)
                    if source_asset:
                        dependents.append(source_asset)
        
        return dependents
    
    def get_dependency_chain(self, asset_id: str, max_depth: int = 10) -> DependencyChain:
        """
        Get the complete dependency chain for an asset
        
        Args:
            asset_id: Asset ID
            max_depth: Maximum depth to traverse
            
        Returns:
            DependencyChain object
        """
        visited = set()
        chain = []
        circular_deps = []
        
        def traverse(current_id: str, depth: int, path: List[str]):
            if depth > max_depth:
                return
            
            if current_id in path:
                # Circular dependency detected
                cycle_start = path.index(current_id)
                circular_deps.append(path[cycle_start:] + [current_id])
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            chain.append(current_id)
            
            # Get dependencies
            dependencies = self.get_asset_dependencies(current_id)
            for dep_asset in dependencies:
                traverse(dep_asset.asset_id, depth + 1, path + [current_id])
        
        traverse(asset_id, 0, [])
        
        return DependencyChain(
            root_asset_id=asset_id,
            chain=chain,
            total_depth=len(chain),
            circular_dependencies=circular_deps
        )
    
    def get_related_assets(self, 
                          asset_id: str,
                          relationship_types: Optional[List[RelationshipType]] = None,
                          max_distance: int = 1) -> Dict[str, List[Asset]]:
        """
        Get assets related to the given asset
        
        Args:
            asset_id: Asset ID
            relationship_types: Filter by relationship types
            max_distance: Maximum relationship distance
            
        Returns:
            Dictionary mapping relationship types to lists of assets
        """
        related = {}
        visited = set()
        
        def traverse(current_id: str, distance: int):
            if distance > max_distance or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Get outgoing relationships
            if current_id in self.source_index:
                for rel_id in self.source_index[current_id]:
                    relationship = self.relationships[rel_id]
                    
                    if relationship_types and relationship.relationship_type not in relationship_types:
                        continue
                    
                    rel_type = relationship.relationship_type.value
                    if rel_type not in related:
                        related[rel_type] = []
                    
                    target_asset = self.assets.get(relationship.target_asset_id)
                    if target_asset and target_asset not in related[rel_type]:
                        related[rel_type].append(target_asset)
                    
                    if distance < max_distance:
                        traverse(relationship.target_asset_id, distance + 1)
            
            # Get incoming relationships
            if current_id in self.target_index:
                for rel_id in self.target_index[current_id]:
                    relationship = self.relationships[rel_id]
                    
                    if relationship_types and relationship.relationship_type not in relationship_types:
                        continue
                    
                    rel_type = f"inverse_{relationship.relationship_type.value}"
                    if rel_type not in related:
                        related[rel_type] = []
                    
                    source_asset = self.assets.get(relationship.source_asset_id)
                    if source_asset and source_asset not in related[rel_type]:
                        related[rel_type].append(source_asset)
                    
                    if distance < max_distance:
                        traverse(relationship.source_asset_id, distance + 1)
        
        traverse(asset_id, 0)
        return related
    
    def track_model_usage(self,
                         model_name: str,
                         model_version: str,
                         generation_time: float,
                         success: bool,
                         performance_metrics: Optional[Dict[str, float]] = None):
        """
        Track model usage statistics
        
        Args:
            model_name: Name of the model
            model_version: Version of the model
            generation_time: Time taken for generation
            success: Whether generation was successful
            performance_metrics: Additional performance metrics
        """
        model_key = f"{model_name}_{model_version}"
        
        if model_key not in self.model_usage:
            self.model_usage[model_key] = ModelUsage(
                model_name=model_name,
                model_version=model_version,
                usage_count=0,
                total_generation_time=0.0,
                average_generation_time=0.0,
                success_rate=0.0,
                last_used=datetime.now().isoformat(),
                performance_metrics={}
            )
        
        usage = self.model_usage[model_key]
        usage.usage_count += 1
        usage.total_generation_time += generation_time
        usage.average_generation_time = usage.total_generation_time / usage.usage_count
        usage.last_used = datetime.now().isoformat()
        
        # Update success rate
        if success:
            current_successes = usage.success_rate * (usage.usage_count - 1)
            usage.success_rate = (current_successes + 1) / usage.usage_count
        else:
            current_successes = usage.success_rate * (usage.usage_count - 1)
            usage.success_rate = current_successes / usage.usage_count
        
        # Update performance metrics
        if performance_metrics:
            for metric, value in performance_metrics.items():
                if metric not in usage.performance_metrics:
                    usage.performance_metrics[metric] = value
                else:
                    # Running average
                    current_avg = usage.performance_metrics[metric]
                    usage.performance_metrics[metric] = (current_avg * (usage.usage_count - 1) + value) / usage.usage_count
        
        self._save_model_usage()
    
    def get_regeneration_plan(self, asset_id: str) -> List[str]:
        """
        Get the regeneration plan for an asset (assets that need to be regenerated)
        
        Args:
            asset_id: Asset ID that changed
            
        Returns:
            List of asset IDs that need regeneration (in dependency order)
        """
        regeneration_plan = []
        visited = set()
        
        def collect_dependents(current_id: str):
            if current_id in visited:
                return
            
            visited.add(current_id)
            dependents = self.get_asset_dependents(current_id)
            
            for dependent in dependents:
                collect_dependents(dependent.asset_id)
                if dependent.asset_id not in regeneration_plan:
                    regeneration_plan.append(dependent.asset_id)
        
        collect_dependents(asset_id)
        return regeneration_plan
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get relationship mapping statistics
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_assets': len(self.assets),
            'total_relationships': len(self.relationships),
            'assets_by_type': {},
            'relationships_by_type': {},
            'model_usage_stats': {},
            'dependency_depth_stats': {},
            'circular_dependencies': 0
        }
        
        # Count assets by type
        for asset in self.assets.values():
            asset_type = asset.asset_type.value
            stats['assets_by_type'][asset_type] = stats['assets_by_type'].get(asset_type, 0) + 1
        
        # Count relationships by type
        for relationship in self.relationships.values():
            rel_type = relationship.relationship_type.value
            stats['relationships_by_type'][rel_type] = stats['relationships_by_type'].get(rel_type, 0) + 1
        
        # Model usage statistics
        for model_key, usage in self.model_usage.items():
            stats['model_usage_stats'][model_key] = {
                'usage_count': usage.usage_count,
                'average_generation_time': usage.average_generation_time,
                'success_rate': usage.success_rate
            }
        
        # Dependency depth analysis
        depth_counts = {}
        circular_count = 0
        
        for asset_id in self.assets.keys():
            chain = self.get_dependency_chain(asset_id, max_depth=5)
            depth = chain.total_depth
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
            
            if chain.circular_dependencies:
                circular_count += len(chain.circular_dependencies)
        
        stats['dependency_depth_stats'] = depth_counts
        stats['circular_dependencies'] = circular_count
        
        return stats

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    mapper = AssetRelationshipMapper()
    
    # Create test files
    test_script = Path("test_script.py")
    test_script.write_text("print('Hello, World!')")
    
    test_audio = Path("test_audio.wav")
    test_audio.write_bytes(b"fake audio data")
    
    try:
        # Register assets
        script_asset = mapper.register_asset(
            AssetType.SCRIPT,
            str(test_script),
            metadata={"purpose": "test script"},
            tags=["test", "python"]
        )
        
        audio_asset = mapper.register_asset(
            AssetType.AUDIO,
            str(test_audio),
            metadata={"duration": 5.0},
            tags=["test", "narration"]
        )
        
        # Create relationship
        relationship = mapper.create_relationship(
            audio_asset.asset_id,
            script_asset.asset_id,
            RelationshipType.SYNCHRONIZED_WITH,
            metadata={"sync_offset": 0.0}
        )
        
        print(f"Created relationship: {relationship.relationship_id}")
        
        # Get related assets
        related = mapper.get_related_assets(script_asset.asset_id)
        print(f"Related assets: {related}")
        
        # Track model usage
        mapper.track_model_usage(
            "test-tts-model",
            "1.0",
            2.5,
            True,
            {"quality_score": 0.95}
        )
        
        # Get statistics
        stats = mapper.get_statistics()
        print(f"Statistics: {stats}")
        
    finally:
        # Cleanup
        if test_script.exists():
            test_script.unlink()
        if test_audio.exists():
            test_audio.unlink()