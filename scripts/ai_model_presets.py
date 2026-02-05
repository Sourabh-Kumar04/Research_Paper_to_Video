"""
AI Model Preset Configurations for RASO Platform

This module provides hardware-optimized model preset configurations,
specifically tuned for different system capabilities including 16GB RAM systems.
"""

import json
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .ai_model_manager import ai_model_manager, ModelInfo, ModelType, ModelPreset

logger = logging.getLogger(__name__)


class HardwareProfile(Enum):
    """Hardware profile categories."""
    MINIMAL = "minimal"      # 8GB RAM, 2-4 cores, no GPU
    STANDARD = "standard"    # 16GB RAM, 4-8 cores, optional GPU
    ENHANCED = "enhanced"    # 32GB RAM, 8+ cores, GPU recommended
    WORKSTATION = "workstation"  # 64GB+ RAM, 16+ cores, high-end GPU


@dataclass
class ModelPresetConfig:
    """Configuration for a model preset."""
    name: str
    display_name: str
    description: str
    hardware_profile: HardwareProfile
    min_ram_gb: int
    recommended_ram_gb: int
    models: Dict[str, str]  # task_type -> model_id
    quantization: str
    max_concurrent_models: int
    memory_safety_margin: float  # Percentage of RAM to keep free
    performance_priority: str  # speed, quality, balanced
    warnings: List[str]
    optimizations: List[str]


class AIModelPresets:
    """Manages AI model preset configurations optimized for different hardware."""
    
    def __init__(self):
        self.presets = self._create_preset_configurations()
        self.current_hardware = self._detect_hardware_profile()
        
    def _detect_hardware_profile(self) -> HardwareProfile:
        """Detect current hardware profile."""
        try:
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            
            if memory_gb < 12:
                return HardwareProfile.MINIMAL
            elif memory_gb < 24:
                return HardwareProfile.STANDARD
            elif memory_gb < 48:
                return HardwareProfile.ENHANCED
            else:
                return HardwareProfile.WORKSTATION
                
        except Exception as e:
            logger.warning(f"Failed to detect hardware profile: {e}")
            return HardwareProfile.STANDARD  # Safe default
    
    def _create_preset_configurations(self) -> Dict[str, ModelPresetConfig]:
        """Create all preset configurations."""
        presets = {}
        
        # FAST MODE - Optimized for 16GB RAM (RECOMMENDED)
        presets["fast"] = ModelPresetConfig(
            name="fast",
            display_name="🚀 Fast Mode",
            description="Lightweight models optimized for 16GB RAM systems with fast response times",
            hardware_profile=HardwareProfile.STANDARD,
            min_ram_gb=8,
            recommended_ram_gb=16,
            models={
                "coding": "codeqwen:7b-chat-q4_0",
                "reasoning": "qwen2.5:7b-instruct-q4_0",
                "lightweight": "llama3.2:3b-instruct-q4_0",
                "vision_language": "moondream:1.8b-v2-q4_0"
            },
            quantization="q4_0",
            max_concurrent_models=1,  # Only one model loaded at a time
            memory_safety_margin=0.3,  # Keep 30% RAM free
            performance_priority="speed",
            warnings=[
                "Only one model loaded at a time to conserve memory",
                "Quantized models may have slightly reduced quality"
            ],
            optimizations=[
                "Automatic model unloading when switching tasks",
                "Optimized for fast startup and response times",
                "Memory-efficient quantization (q4_0)",
                "Sequential processing to avoid memory conflicts"
            ]
        )
        
        # BALANCED MODE - For 16-32GB RAM (Use with caution on 16GB)
        presets["balanced"] = ModelPresetConfig(
            name="balanced",
            display_name="⚖️ Balanced Mode",
            description="Mid-tier models balancing quality and performance for 16-32GB systems",
            hardware_profile=HardwareProfile.STANDARD,
            min_ram_gb=16,
            recommended_ram_gb=24,
            models={
                "coding": "codestral:22b-v0.1-q4_0",
                "reasoning": "qwen2.5:14b-instruct-q4_0",
                "lightweight": "qwen2.5:7b-instruct-q4_0",
                "vision_language": "qwen2-vl:7b-instruct-q4_0"
            },
            quantization="q4_0",
            max_concurrent_models=1,  # Still conservative for 16GB
            memory_safety_margin=0.25,  # Keep 25% RAM free
            performance_priority="balanced",
            warnings=[
                "May cause memory pressure on 16GB systems",
                "Monitor system performance during use",
                "Consider FAST mode if experiencing issues"
            ],
            optimizations=[
                "Better quality than FAST mode",
                "Intelligent model switching based on task complexity",
                "Optimized quantization for quality/speed balance"
            ]
        )
        
        # QUALITY MODE - For 32GB+ RAM (NOT recommended for 16GB)
        presets["quality"] = ModelPresetConfig(
            name="quality",
            display_name="💎 Quality Mode",
            description="Large models for highest quality output on 32GB+ systems",
            hardware_profile=HardwareProfile.ENHANCED,
            min_ram_gb=32,
            recommended_ram_gb=48,
            models={
                "coding": "qwen2.5-coder:32b-instruct-q4_0",
                "reasoning": "deepseek-v3:latest-q4_0",
                "lightweight": "codestral:22b-v0.1-q4_0",
                "vision_language": "llava-next:34b-q4_0"
            },
            quantization="q4_0",
            max_concurrent_models=2,  # Can handle multiple models
            memory_safety_margin=0.2,  # Keep 20% RAM free
            performance_priority="quality",
            warnings=[
                "NOT RECOMMENDED for 16GB systems",
                "Requires 32GB+ RAM for stable operation",
                "May be slow on systems without GPU acceleration"
            ],
            optimizations=[
                "Highest quality output available",
                "Advanced model ensemble capabilities",
                "GPU acceleration when available"
            ]
        )
        
        # CUSTOM MODE - User-defined configurations
        presets["custom"] = ModelPresetConfig(
            name="custom",
            display_name="🔧 Custom Mode",
            description="User-defined model combinations with manual configuration",
            hardware_profile=HardwareProfile.STANDARD,  # Default assumption
            min_ram_gb=8,
            recommended_ram_gb=16,
            models={
                "coding": "codeqwen:7b-chat-q4_0",  # Safe defaults
                "reasoning": "qwen2.5:7b-instruct-q4_0",
                "lightweight": "llama3.2:3b-instruct-q4_0",
                "vision_language": "moondream:1.8b-v2-q4_0"
            },
            quantization="q4_0",
            max_concurrent_models=1,
            memory_safety_margin=0.3,
            performance_priority="balanced",
            warnings=[
                "Manual configuration required",
                "User responsible for memory management",
                "May require system monitoring"
            ],
            optimizations=[
                "Fully customizable model selection",
                "Advanced configuration options",
                "Expert-level control"
            ]
        )
        
        # ULTRA-LIGHT MODE - For 8GB RAM systems
        presets["ultra_light"] = ModelPresetConfig(
            name="ultra_light",
            display_name="🪶 Ultra-Light Mode",
            description="Minimal models for 8GB RAM systems and resource-constrained environments",
            hardware_profile=HardwareProfile.MINIMAL,
            min_ram_gb=4,
            recommended_ram_gb=8,
            models={
                "coding": "llama3.2:3b-instruct-q4_0",
                "reasoning": "llama3.2:3b-instruct-q4_0",
                "lightweight": "llama3.2:3b-instruct-q4_0",
                "vision_language": "moondream:1.8b-v2-q4_0"
            },
            quantization="q4_0",
            max_concurrent_models=1,
            memory_safety_margin=0.4,  # Keep 40% RAM free
            performance_priority="speed",
            warnings=[
                "Reduced model capabilities",
                "Limited to basic tasks",
                "May require multiple attempts for complex requests"
            ],
            optimizations=[
                "Extremely low memory usage",
                "Fast response times",
                "Suitable for basic automation tasks"
            ]
        )
        
        # WORKSTATION MODE - For 64GB+ RAM systems
        presets["workstation"] = ModelPresetConfig(
            name="workstation",
            display_name="🏭 Workstation Mode",
            description="High-end models for professional workstations with 64GB+ RAM",
            hardware_profile=HardwareProfile.WORKSTATION,
            min_ram_gb=64,
            recommended_ram_gb=128,
            models={
                "coding": "qwen2.5-coder:32b-instruct-q5_1",  # Higher quality quantization
                "reasoning": "mistral-large:123b-instruct-2407-q4_0",
                "lightweight": "qwen2.5-coder:32b-instruct-q4_0",
                "vision_language": "llava-next:34b-q5_1"
            },
            quantization="q5_1",  # Higher quality quantization
            max_concurrent_models=4,  # Multiple models simultaneously
            memory_safety_margin=0.15,  # Keep 15% RAM free
            performance_priority="quality",
            warnings=[
                "Requires high-end hardware",
                "GPU acceleration strongly recommended",
                "May have longer startup times"
            ],
            optimizations=[
                "Maximum quality output",
                "Parallel model processing",
                "Advanced ensemble techniques",
                "Professional-grade performance"
            ]
        )
        
        return presets
    
    def get_recommended_preset(self, hardware_profile: Optional[HardwareProfile] = None) -> str:
        """Get recommended preset for current or specified hardware."""
        if hardware_profile is None:
            hardware_profile = self.current_hardware
        
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Hardware-based recommendations
        if hardware_profile == HardwareProfile.MINIMAL or memory_gb < 12:
            return "ultra_light"
        elif hardware_profile == HardwareProfile.STANDARD or memory_gb < 24:
            return "fast"  # RECOMMENDED for 16GB systems
        elif hardware_profile == HardwareProfile.ENHANCED or memory_gb < 48:
            return "balanced"
        else:
            return "workstation"
    
    def get_preset_config(self, preset_name: str) -> Optional[ModelPresetConfig]:
        """Get configuration for a specific preset."""
        return self.presets.get(preset_name)
    
    def validate_preset_compatibility(self, preset_name: str) -> Dict[str, Any]:
        """Validate if a preset is compatible with current hardware."""
        preset = self.presets.get(preset_name)
        if not preset:
            return {"compatible": False, "reason": "Preset not found"}
        
        memory_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()
        
        # Memory check
        if memory_gb < preset.min_ram_gb:
            return {
                "compatible": False,
                "reason": f"Insufficient RAM: {memory_gb:.1f}GB available, {preset.min_ram_gb}GB required",
                "severity": "error"
            }
        
        # Warning for borderline cases
        if memory_gb < preset.recommended_ram_gb:
            return {
                "compatible": True,
                "reason": f"Below recommended RAM: {memory_gb:.1f}GB available, {preset.recommended_ram_gb}GB recommended",
                "severity": "warning"
            }
        
        return {
            "compatible": True,
            "reason": "Fully compatible",
            "severity": "success"
        }
    
    def get_memory_optimized_config(self, available_memory_gb: float) -> ModelPresetConfig:
        """Get memory-optimized configuration for specific RAM amount."""
        if available_memory_gb < 8:
            base_preset = self.presets["ultra_light"]
        elif available_memory_gb < 16:
            base_preset = self.presets["ultra_light"]
        elif available_memory_gb < 24:
            base_preset = self.presets["fast"]
        elif available_memory_gb < 48:
            base_preset = self.presets["balanced"]
        else:
            base_preset = self.presets["quality"]
        
        # Create optimized version
        optimized = ModelPresetConfig(
            name=f"optimized_{available_memory_gb:.0f}gb",
            display_name=f"🎯 Optimized for {available_memory_gb:.0f}GB",
            description=f"Custom configuration optimized for {available_memory_gb:.1f}GB RAM",
            hardware_profile=base_preset.hardware_profile,
            min_ram_gb=min(base_preset.min_ram_gb, available_memory_gb * 0.5),
            recommended_ram_gb=available_memory_gb,
            models=base_preset.models.copy(),
            quantization=base_preset.quantization,
            max_concurrent_models=base_preset.max_concurrent_models,
            memory_safety_margin=max(0.2, base_preset.memory_safety_margin),
            performance_priority=base_preset.performance_priority,
            warnings=base_preset.warnings + [f"Optimized for {available_memory_gb:.1f}GB RAM"],
            optimizations=base_preset.optimizations + ["Hardware-specific optimization"]
        )
        
        # Adjust for very low memory
        if available_memory_gb <= 16:
            optimized.max_concurrent_models = 1
            optimized.memory_safety_margin = 0.35  # More conservative
            optimized.quantization = "q4_0"  # Ensure efficient quantization
        
        return optimized
    
    def get_task_optimized_preset(self, primary_task: str) -> ModelPresetConfig:
        """Get preset optimized for a specific primary task."""
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Start with appropriate base preset
        if memory_gb <= 16:
            base_preset = self.presets["fast"]
        elif memory_gb <= 32:
            base_preset = self.presets["balanced"]
        else:
            base_preset = self.presets["quality"]
        
        # Create task-optimized version
        optimized = ModelPresetConfig(
            name=f"task_{primary_task}",
            display_name=f"🎯 {primary_task.title()} Optimized",
            description=f"Optimized configuration for {primary_task} tasks",
            hardware_profile=base_preset.hardware_profile,
            min_ram_gb=base_preset.min_ram_gb,
            recommended_ram_gb=base_preset.recommended_ram_gb,
            models=base_preset.models.copy(),
            quantization=base_preset.quantization,
            max_concurrent_models=base_preset.max_concurrent_models,
            memory_safety_margin=base_preset.memory_safety_margin,
            performance_priority=base_preset.performance_priority,
            warnings=base_preset.warnings.copy(),
            optimizations=base_preset.optimizations + [f"Optimized for {primary_task} tasks"]
        )
        
        # Task-specific optimizations
        if primary_task in ["coding", "manim", "python"]:
            # Prioritize coding models
            if memory_gb >= 24:
                optimized.models["coding"] = "qwen2.5-coder:32b-instruct-q4_0"
            elif memory_gb >= 16:
                optimized.models["coding"] = "codestral:22b-v0.1-q4_0"
            
            optimized.performance_priority = "quality"
            optimized.optimizations.append("Enhanced coding model selection")
            
        elif primary_task in ["content", "educational", "writing"]:
            # Prioritize reasoning models
            if memory_gb >= 32:
                optimized.models["reasoning"] = "deepseek-v3:latest-q4_0"
            elif memory_gb >= 20:
                optimized.models["reasoning"] = "qwen2.5:14b-instruct-q4_0"
            
            optimized.performance_priority = "quality"
            optimized.optimizations.append("Enhanced content generation models")
            
        elif primary_task in ["vision", "image", "diagram"]:
            # Prioritize vision-language models
            if memory_gb >= 24:
                optimized.models["vision_language"] = "llava-next:34b-q4_0"
            else:
                optimized.models["vision_language"] = "qwen2-vl:7b-instruct-q4_0"
            
            optimized.optimizations.append("Enhanced vision-language capabilities")
        
        return optimized
    
    def get_all_presets_info(self) -> List[Dict[str, Any]]:
        """Get information about all available presets."""
        presets_info = []
        
        for preset_name, preset_config in self.presets.items():
            compatibility = self.validate_preset_compatibility(preset_name)
            
            presets_info.append({
                "name": preset_name,
                "display_name": preset_config.display_name,
                "description": preset_config.description,
                "hardware_profile": preset_config.hardware_profile.value,
                "min_ram_gb": preset_config.min_ram_gb,
                "recommended_ram_gb": preset_config.recommended_ram_gb,
                "performance_priority": preset_config.performance_priority,
                "max_concurrent_models": preset_config.max_concurrent_models,
                "compatibility": compatibility,
                "warnings": preset_config.warnings,
                "optimizations": preset_config.optimizations,
                "models": preset_config.models
            })
        
        # Sort by compatibility and recommended status
        def sort_key(preset):
            if not preset["compatibility"]["compatible"]:
                return 2  # Incompatible last
            elif preset["name"] == self.get_recommended_preset():
                return 0  # Recommended first
            else:
                return 1  # Compatible but not recommended
        
        presets_info.sort(key=sort_key)
        return presets_info
    
    def create_custom_preset(
        self,
        name: str,
        models: Dict[str, str],
        performance_priority: str = "balanced",
        memory_safety_margin: float = 0.3
    ) -> ModelPresetConfig:
        """Create a custom preset configuration."""
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Determine appropriate hardware profile
        if memory_gb < 12:
            hardware_profile = HardwareProfile.MINIMAL
        elif memory_gb < 24:
            hardware_profile = HardwareProfile.STANDARD
        elif memory_gb < 48:
            hardware_profile = HardwareProfile.ENHANCED
        else:
            hardware_profile = HardwareProfile.WORKSTATION
        
        custom_preset = ModelPresetConfig(
            name=name,
            display_name=f"🔧 {name.title()}",
            description=f"Custom preset: {name}",
            hardware_profile=hardware_profile,
            min_ram_gb=8,  # Conservative minimum
            recommended_ram_gb=memory_gb,
            models=models,
            quantization="q4_0",  # Safe default
            max_concurrent_models=1 if memory_gb <= 16 else 2,
            memory_safety_margin=memory_safety_margin,
            performance_priority=performance_priority,
            warnings=["Custom configuration - monitor system performance"],
            optimizations=["User-defined model selection"]
        )
        
        # Add to presets
        self.presets[name] = custom_preset
        
        return custom_preset
    
    def export_preset_config(self, preset_name: str, file_path: Optional[Path] = None) -> bool:
        """Export preset configuration to JSON file."""
        preset = self.presets.get(preset_name)
        if not preset:
            return False
        
        if file_path is None:
            file_path = Path(f"config/preset_{preset_name}.json")
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(asdict(preset), f, indent=2, default=str)
            
            logger.info(f"Exported preset '{preset_name}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export preset: {e}")
            return False
    
    def import_preset_config(self, file_path: Path) -> Optional[str]:
        """Import preset configuration from JSON file."""
        try:
            with open(file_path, 'r') as f:
                preset_data = json.load(f)
            
            # Convert hardware_profile back to enum
            if isinstance(preset_data.get('hardware_profile'), str):
                preset_data['hardware_profile'] = HardwareProfile(preset_data['hardware_profile'])
            
            preset = ModelPresetConfig(**preset_data)
            self.presets[preset.name] = preset
            
            logger.info(f"Imported preset '{preset.name}' from {file_path}")
            return preset.name
            
        except Exception as e:
            logger.error(f"Failed to import preset: {e}")
            return None


# Global instance for easy access
ai_model_presets = AIModelPresets()