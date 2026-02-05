"""
AI Model Manager for RASO Platform

This module manages AI model integration, selection, and optimization for
enhanced video content generation using the latest open-source models.
"""

import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import psutil
import logging

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """AI model types for different tasks."""
    CODING = "coding"  # For Manim/Python code generation
    REASONING = "reasoning"  # For content understanding and analysis
    VISION_LANGUAGE = "vision_language"  # For visual content analysis
    LIGHTWEIGHT = "lightweight"  # For resource-constrained environments


class ModelPreset(Enum):
    """Model performance presets optimized for different hardware."""
    FAST = "fast"  # Lightweight models for 16GB RAM (RECOMMENDED)
    BALANCED = "balanced"  # Mid-tier models (use with caution on 16GB)
    QUALITY = "quality"  # Large models (not recommended for 16GB)
    CUSTOM = "custom"  # User-defined model combinations


@dataclass
class ModelInfo:
    """Information about an AI model."""
    name: str
    model_id: str
    model_type: ModelType
    size_gb: float
    min_ram_gb: int
    parameters: str
    description: str
    recommended_for: List[str]
    ollama_compatible: bool = True
    quantized_versions: Optional[List[str]] = None
    performance_score: float = 0.0  # 0-1, higher is better


@dataclass
class ModelConfig:
    """Configuration for AI model usage."""
    model_info: ModelInfo
    temperature: float = 0.3
    max_tokens: int = 2048
    context_length: int = 4096
    quantization: Optional[str] = None
    gpu_layers: int = 0
    cpu_threads: int = 4


class AIModelManager:
    """Manages AI model selection, loading, and optimization."""
    
    def __init__(self):
        self.available_models = self._initialize_model_catalog()
        self.loaded_models = {}
        self.current_preset = ModelPreset.FAST
        self.system_info = self._get_system_info()
        self.ollama_available = False
        
    def _initialize_model_catalog(self) -> Dict[str, ModelInfo]:
        """Initialize catalog of available AI models."""
        models = {
            # Lightweight Models (RECOMMENDED for 16GB RAM)
            "qwen2.5-7b": ModelInfo(
                name="Qwen2.5-7B-Instruct",
                model_id="qwen2.5:7b-instruct",
                model_type=ModelType.REASONING,
                size_gb=4.1,
                min_ram_gb=6,
                parameters="7B",
                description="Excellent reasoning model optimized for 16GB systems",
                recommended_for=["content analysis", "script generation", "educational content"],
                quantized_versions=["q4_0", "q4_1", "q5_0", "q5_1", "q8_0"]
            ),
            
            "codeqwen1.5-7b": ModelInfo(
                name="CodeQwen1.5-7B-Chat",
                model_id="codeqwen:7b-chat",
                model_type=ModelType.CODING,
                size_gb=4.0,
                min_ram_gb=6,
                parameters="7B",
                description="Specialized coding model for Python/Manim generation",
                recommended_for=["manim code", "python scripts", "code validation"],
                quantized_versions=["q4_0", "q4_1", "q5_0", "q5_1", "q8_0"]
            ),
            
            "llama3.2-3b": ModelInfo(
                name="Llama-3.2-3B-Instruct",
                model_id="llama3.2:3b-instruct",
                model_type=ModelType.LIGHTWEIGHT,
                size_gb=2.0,
                min_ram_gb=4,
                parameters="3B",
                description="Ultra-lightweight model for basic tasks",
                recommended_for=["simple text generation", "basic reasoning"],
                quantized_versions=["q4_0", "q4_1", "q5_0", "q5_1", "q8_0"]
            ),
            
            # Mid-tier Models (Use with caution on 16GB)
            "qwen2.5-14b": ModelInfo(
                name="Qwen2.5-14B-Instruct",
                model_id="qwen2.5:14b-instruct",
                model_type=ModelType.REASONING,
                size_gb=8.2,
                min_ram_gb=12,
                parameters="14B",
                description="Higher quality reasoning (requires careful memory management)",
                recommended_for=["complex analysis", "advanced reasoning"],
                quantized_versions=["q4_0", "q4_1", "q5_0"]
            ),
            
            # Advanced Coding Models (Latest Generation)
            "qwen2.5-coder-32b": ModelInfo(
                name="Qwen2.5-Coder-32B-Instruct",
                model_id="qwen2.5-coder:32b-instruct-q4_0",  # Quantized for 16GB compatibility
                model_type=ModelType.CODING,
                size_gb=18.0,  # Quantized size
                min_ram_gb=20,
                parameters="32B",
                description="State-of-the-art coding model for complex Python/Manim generation",
                recommended_for=["advanced manim code", "complex algorithms", "system architecture", "code optimization"],
                quantized_versions=["q4_0", "q4_1"]
            ),
            
            "deepseek-coder-v2-instruct": ModelInfo(
                name="DeepSeek-Coder-V2-Instruct",
                model_id="deepseek-coder:33b-instruct-q4_0",  # Latest V2 model
                model_type=ModelType.CODING,
                size_gb=19.0,  # Quantized size
                min_ram_gb=22,
                parameters="33B",
                description="Advanced coding model with superior logic and animation generation",
                recommended_for=["complex animation logic", "mathematical visualizations", "advanced algorithms"],
                quantized_versions=["q4_0", "q4_1"]
            ),
            
            "codestral-22b": ModelInfo(
                name="Codestral-22B-v0.1",
                model_id="codestral:22b-v0.1-q4_0",  # Mistral's coding model
                model_type=ModelType.CODING,
                size_gb=13.0,  # Quantized size
                min_ram_gb=16,
                parameters="22B",
                description="Mistral's specialized coding model with excellent Python support",
                recommended_for=["python development", "manim scripting", "code completion"],
                quantized_versions=["q4_0", "q4_1", "q5_0"]
            ),
            
            # Advanced Reasoning Models (Latest Generation)
            "deepseek-v3": ModelInfo(
                name="DeepSeek-V3",
                model_id="deepseek-v3:latest-q4_0",  # Latest DeepSeek model
                model_type=ModelType.REASONING,
                size_gb=45.0,  # Quantized size (NOT recommended for 16GB)
                min_ram_gb=50,
                parameters="671B MoE",
                description="Cutting-edge reasoning model (NOT for 16GB systems)",
                recommended_for=["complex reasoning", "advanced analysis", "research-level content"],
                quantized_versions=["q4_0"]
            ),
            
            "llama3.3-70b": ModelInfo(
                name="Llama-3.3-70B-Instruct",
                model_id="llama3.3:70b-instruct-q4_0",  # Force quantized version
                model_type=ModelType.REASONING,
                size_gb=40.0,  # Quantized size
                min_ram_gb=48,
                parameters="70B",
                description="High-quality reasoning (NOT recommended for 16GB systems)",
                recommended_for=["premium content generation", "complex educational content"],
                quantized_versions=["q4_0"]
            ),
            
            "mistral-large-2": ModelInfo(
                name="Mistral-Large-2",
                model_id="mistral-large:123b-instruct-2407-q4_0",  # Latest Mistral Large
                model_type=ModelType.REASONING,
                size_gb=70.0,  # Quantized size (NOT for 16GB)
                min_ram_gb=80,
                parameters="123B",
                description="Mistral's largest model with multilingual support (NOT for 16GB)",
                recommended_for=["multilingual content", "advanced reasoning", "professional content"],
                quantized_versions=["q4_0"]
            ),
            
            # Vision-Language Models (Latest Generation)
            "qwen2-vl-7b": ModelInfo(
                name="Qwen2-VL-7B-Instruct",
                model_id="qwen2-vl:7b-instruct",
                model_type=ModelType.VISION_LANGUAGE,
                size_gb=4.5,
                min_ram_gb=7,
                parameters="7B",
                description="Advanced vision-language model for diagram analysis",
                recommended_for=["image analysis", "diagram understanding", "visual content", "chart interpretation"],
                quantized_versions=["q4_0", "q4_1", "q5_0"]
            ),
            
            "llava-next-34b": ModelInfo(
                name="LLaVA-NeXT-34B",
                model_id="llava-next:34b-q4_0",  # Advanced LLaVA model
                model_type=ModelType.VISION_LANGUAGE,
                size_gb=20.0,  # Quantized size
                min_ram_gb=24,
                parameters="34B",
                description="State-of-the-art vision-language model (use with caution on 16GB)",
                recommended_for=["advanced visual analysis", "complex diagram understanding", "visual reasoning"],
                quantized_versions=["q4_0", "q4_1"]
            ),
            
            "moondream2": ModelInfo(
                name="Moondream2",
                model_id="moondream:1.8b-v2-fp16",  # Lightweight vision model
                model_type=ModelType.VISION_LANGUAGE,
                size_gb=3.5,
                min_ram_gb=5,
                parameters="1.8B",
                description="Lightweight vision-language model for basic visual tasks",
                recommended_for=["basic image analysis", "simple visual understanding", "resource-efficient vision"],
                quantized_versions=["q4_0", "q5_0", "q8_0"]
            ),
        }
        
        return models
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system hardware information."""
        try:
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            
            # Try to detect GPU
            gpu_info = self._detect_gpu()
            
            return {
                "memory_gb": memory_gb,
                "cpu_count": cpu_count,
                "gpu_info": gpu_info,
                "recommended_preset": self._recommend_preset(memory_gb)
            }
        except Exception as e:
            logger.warning(f"Failed to get system info: {e}")
            return {
                "memory_gb": 16.0,  # Default assumption
                "cpu_count": 4,
                "gpu_info": None,
                "recommended_preset": ModelPreset.FAST
            }
    
    def _detect_gpu(self) -> Optional[Dict[str, Any]]:
        """Detect available GPU information."""
        try:
            # Try nvidia-smi first
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(', ')
                    if len(parts) >= 2:
                        return {
                            "type": "nvidia",
                            "name": parts[0],
                            "memory_mb": int(parts[1]),
                            "available": True
                        }
            
            # Try AMD ROCm
            result = subprocess.run(
                ["rocm-smi", "--showproductname"], 
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "type": "amd",
                    "name": "AMD GPU",
                    "available": True
                }
            
            return None
            
        except Exception:
            return None
    
    def _recommend_preset(self, memory_gb: float) -> ModelPreset:
        """Recommend model preset based on available memory."""
        if memory_gb < 8:
            return ModelPreset.FAST
        elif memory_gb < 16:
            return ModelPreset.FAST
        elif memory_gb < 32:
            return ModelPreset.BALANCED
        else:
            return ModelPreset.QUALITY
    
    async def initialize_ollama(self) -> bool:
        """Initialize Ollama service."""
        try:
            # Check if Ollama is installed
            result = await asyncio.create_subprocess_exec(
                "ollama", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.info(f"Ollama available: {stdout.decode().strip()}")
                self.ollama_available = True
                
                # Start Ollama service if not running
                await self._ensure_ollama_running()
                return True
            else:
                logger.warning("Ollama not found. Please install Ollama for AI model support.")
                return False
                
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama: {e}")
            return False
    
    async def _ensure_ollama_running(self) -> None:
        """Ensure Ollama service is running."""
        try:
            # Try to list models to check if service is running
            result = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await result.communicate()
            
            if result.returncode != 0:
                logger.info("Starting Ollama service...")
                # Start Ollama service in background
                await asyncio.create_subprocess_exec(
                    "ollama", "serve",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                
                # Wait a moment for service to start
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.warning(f"Failed to ensure Ollama is running: {e}")
    
    def get_preset_models(self, preset: ModelPreset) -> Dict[ModelType, ModelInfo]:
        """Get recommended models for a preset."""
        memory_gb = self.system_info["memory_gb"]
        
        if preset == ModelPreset.FAST:
            # Optimized for 16GB RAM systems (RECOMMENDED)
            # Use only one model at a time to stay within memory limits
            models = {
                ModelType.CODING: self.available_models["codeqwen1.5-7b"],
                ModelType.REASONING: self.available_models["qwen2.5-7b"],
                ModelType.LIGHTWEIGHT: self.available_models["llama3.2-3b"],
                ModelType.VISION_LANGUAGE: self.available_models["moondream2"]  # Lightweight vision model
            }
            
            # For very low memory systems, use only lightweight models
            if memory_gb < 8:
                lightweight_model = self.available_models["llama3.2-3b"]
                return {
                    ModelType.CODING: lightweight_model,
                    ModelType.REASONING: lightweight_model,
                    ModelType.LIGHTWEIGHT: lightweight_model,
                    ModelType.VISION_LANGUAGE: self.available_models["moondream2"]
                }
            
            return models
        
        elif preset == ModelPreset.BALANCED:
            # For systems with 16-32GB RAM (use with caution on 16GB)
            models = {
                ModelType.CODING: self.available_models["codestral-22b"],  # Better than deepseek-6.7b
                ModelType.REASONING: self.available_models["qwen2.5-14b"],
                ModelType.LIGHTWEIGHT: self.available_models["qwen2.5-7b"],
                ModelType.VISION_LANGUAGE: self.available_models["qwen2-vl-7b"]
            }
            
            # Add memory warning for 16GB systems and fallback to FAST
            if memory_gb <= 16:
                logger.warning("BALANCED preset may cause memory issues on 16GB systems. Using FAST preset models.")
                return self.get_preset_models(ModelPreset.FAST)
            
            return models
        
        elif preset == ModelPreset.QUALITY:
            # For systems with 32GB+ RAM (NOT recommended for 16GB)
            if memory_gb <= 24:
                logger.error("QUALITY preset NOT recommended for systems with ≤24GB RAM. Using FAST preset instead.")
                return self.get_preset_models(ModelPreset.FAST)
            
            return {
                ModelType.CODING: self.available_models["qwen2.5-coder-32b"],  # Latest coding model
                ModelType.REASONING: self.available_models["deepseek-v3"],  # Latest reasoning model
                ModelType.LIGHTWEIGHT: self.available_models["codestral-22b"],  # High-quality lightweight
                ModelType.VISION_LANGUAGE: self.available_models["llava-next-34b"]  # Advanced vision model
            }
        
        else:  # CUSTOM
            # Return default FAST models for custom (user will override)
            return self.get_preset_models(ModelPreset.FAST)
    
    async def ensure_model_available(self, model_info: ModelInfo) -> bool:
        """Ensure a model is available in Ollama."""
        if not self.ollama_available:
            logger.error("Ollama not available. Cannot load models.")
            return False
        
        try:
            # Check if model is already available
            result = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                available_models = stdout.decode()
                if model_info.model_id in available_models:
                    logger.info(f"Model {model_info.name} already available")
                    return True
            
            # Model not available, need to pull it
            logger.info(f"Downloading model {model_info.name} ({model_info.size_gb:.1f}GB)...")
            
            # Check available disk space
            if not self._check_disk_space(model_info.size_gb):
                logger.error(f"Insufficient disk space for model {model_info.name}")
                return False
            
            # Pull the model
            pull_process = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_info.model_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await pull_process.communicate()
            
            if pull_process.returncode == 0:
                logger.info(f"Successfully downloaded model {model_info.name}")
                return True
            else:
                logger.error(f"Failed to download model {model_info.name}: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring model availability: {e}")
            return False
    
    def _check_disk_space(self, required_gb: float) -> bool:
        """Check if there's enough disk space for a model."""
        try:
            # Check space in home directory (where Ollama stores models)
            home_path = Path.home()
            stat = home_path.stat()
            
            # Get available space (this is a simplified check)
            import shutil
            free_bytes = shutil.disk_usage(home_path).free
            free_gb = free_bytes / (1024**3)
            
            # Require 2x the model size for safety
            required_space = required_gb * 2
            
            if free_gb < required_space:
                logger.warning(f"Low disk space: {free_gb:.1f}GB available, {required_space:.1f}GB required")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            return True  # Assume OK if we can't check
    
    async def generate_with_model(
        self,
        model_info: ModelInfo,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        use_gpu: bool = True
    ) -> Optional[str]:
        """Generate content using a specific model with GPU acceleration support."""
        if not await self.ensure_model_available(model_info):
            return None
        
        try:
            # Create Ollama API request
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                options = {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 4096
                }
                
                # Add GPU acceleration if available
                if use_gpu and hasattr(model_info, 'default_gpu_layers'):
                    options["num_gpu"] = model_info.default_gpu_layers
                
                # Add CPU thread optimization
                cpu_count = self.system_info.get("cpu_count", 4)
                options["num_thread"] = min(cpu_count, 8)  # Cap at 8 threads
                
                payload = {
                    "model": model_info.model_id,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                }
                
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error generating with model {model_info.name}: {e}")
            return None
    
    def get_model_for_task(self, task_type: str) -> Optional[ModelInfo]:
        """Get the best model for a specific task."""
        preset_models = self.get_preset_models(self.current_preset)
        
        task_mapping = {
            "manim_code": ModelType.CODING,
            "python_code": ModelType.CODING,
            "code_generation": ModelType.CODING,
            "coding": ModelType.CODING,
            "script_generation": ModelType.REASONING,
            "content_analysis": ModelType.REASONING,
            "educational_content": ModelType.REASONING,
            "reasoning": ModelType.REASONING,
            "image_analysis": ModelType.VISION_LANGUAGE,
            "diagram_understanding": ModelType.VISION_LANGUAGE,
            "vision_language": ModelType.VISION_LANGUAGE,
            "simple_tasks": ModelType.LIGHTWEIGHT,
            "lightweight": ModelType.LIGHTWEIGHT
        }
        
        model_type = task_mapping.get(task_type, ModelType.REASONING)
        selected_model = preset_models.get(model_type)
        
        # Memory compatibility check
        if selected_model:
            memory_gb = self.system_info.get("memory_gb", 16)
            if selected_model.min_ram_gb > memory_gb:
                # Try to find a compatible alternative
                logger.warning(f"Selected model {selected_model.name} requires {selected_model.min_ram_gb}GB "
                             f"but only {memory_gb}GB available. Looking for alternatives...")
                
                # Try lightweight model first
                lightweight_model = preset_models.get(ModelType.LIGHTWEIGHT)
                if lightweight_model and lightweight_model.min_ram_gb <= memory_gb:
                    logger.info(f"Using lightweight model {lightweight_model.name} instead")
                    return lightweight_model
                
                # Try all available models to find compatible one
                for model_info in self.available_models.values():
                    if (model_info.min_ram_gb <= memory_gb and 
                        (model_info.model_type == model_type or model_info.model_type == ModelType.REASONING)):
                        logger.info(f"Using compatible model {model_info.name} instead")
                        return model_info
                
                # If no compatible model found, return None
                logger.error(f"No compatible model found for {memory_gb}GB memory constraint")
                return None
        
        return selected_model
    
    def set_preset(self, preset: ModelPreset) -> None:
        """Set the current model preset."""
        old_preset = self.current_preset
        self.current_preset = preset
        
        logger.info(f"Model preset changed from {old_preset.value} to {preset.value}")
        
        # Log memory warning for inappropriate presets
        memory_gb = self.system_info["memory_gb"]
        if preset == ModelPreset.QUALITY and memory_gb <= 16:
            logger.warning("⚠️  QUALITY preset not recommended for 16GB systems!")
        elif preset == ModelPreset.BALANCED and memory_gb <= 16:
            logger.warning("⚠️  BALANCED preset may cause memory issues on 16GB systems.")
    
    async def setup_gpu_acceleration(self) -> bool:
        """Set up GPU acceleration for AI models."""
        try:
            gpu_info = self.system_info.get("gpu_info")
            
            if not gpu_info:
                logger.info("No GPU detected. Using CPU-only inference.")
                return False
            
            if gpu_info["type"] == "nvidia":
                logger.info(f"NVIDIA GPU detected: {gpu_info['name']}")
                
                # Check CUDA availability
                try:
                    result = await asyncio.create_subprocess_exec(
                        "nvidia-smi",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await result.communicate()
                    
                    if result.returncode == 0:
                        logger.info("CUDA available for GPU acceleration")
                        
                        # Set GPU layers for models
                        memory_mb = gpu_info.get("memory_mb", 0)
                        if memory_mb >= 8000:  # 8GB+ GPU
                            self._set_default_gpu_layers(35)  # Most layers on GPU
                        elif memory_mb >= 4000:  # 4GB+ GPU
                            self._set_default_gpu_layers(20)  # Some layers on GPU
                        else:
                            self._set_default_gpu_layers(10)  # Few layers on GPU
                        
                        return True
                    
                except Exception as e:
                    logger.warning(f"CUDA check failed: {e}")
            
            elif gpu_info["type"] == "amd":
                logger.info("AMD GPU detected. ROCm support may be available.")
                # AMD GPU support is more limited in Ollama
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to set up GPU acceleration: {e}")
            return False
    
    def _set_default_gpu_layers(self, layers: int) -> None:
        """Set default GPU layers for models."""
        for model_info in self.available_models.values():
            if not hasattr(model_info, 'default_gpu_layers'):
                model_info.default_gpu_layers = layers
        
        logger.info(f"Set default GPU layers to {layers}")
    
    async def check_model_updates(self) -> Dict[str, Any]:
        """Check for model updates."""
        if not self.ollama_available:
            return {"status": "ollama_not_available"}
        
        try:
            # Get list of currently installed models
            result = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                return {"status": "error", "message": stderr.decode()}
            
            installed_models = []
            lines = stdout.decode().strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        model_name = parts[0]
                        model_id = parts[1] if len(parts) > 1 else ""
                        size = parts[2] if len(parts) > 2 else ""
                        modified = " ".join(parts[3:]) if len(parts) > 3 else ""
                        
                        installed_models.append({
                            "name": model_name,
                            "id": model_id,
                            "size": size,
                            "modified": modified
                        })
            
            return {
                "status": "success",
                "installed_models": installed_models,
                "available_updates": self._check_available_updates(installed_models)
            }
            
        except Exception as e:
            logger.error(f"Error checking model updates: {e}")
            return {"status": "error", "message": str(e)}
    
    def _check_available_updates(self, installed_models: List[Dict]) -> List[str]:
        """Check which models have available updates."""
        # This is a simplified implementation
        # In a real system, you'd check against a model registry
        updates = []
        
        installed_ids = {model["name"] for model in installed_models}
        
        for model_id, model_info in self.available_models.items():
            if model_info.model_id not in installed_ids:
                updates.append(model_info.model_id)
        
        return updates
    
    async def update_models(self, model_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update specified models or all models."""
        if not self.ollama_available:
            return {"status": "ollama_not_available"}
        
        if model_ids is None:
            # Update all available models
            model_ids = [info.model_id for info in self.available_models.values()]
        
        results = {}
        
        for model_id in model_ids:
            try:
                logger.info(f"Updating model: {model_id}")
                
                result = await asyncio.create_subprocess_exec(
                    "ollama", "pull", model_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    results[model_id] = {"status": "success", "message": "Updated successfully"}
                    logger.info(f"Successfully updated model: {model_id}")
                else:
                    results[model_id] = {"status": "error", "message": stderr.decode()}
                    logger.error(f"Failed to update model {model_id}: {stderr.decode()}")
                    
            except Exception as e:
                results[model_id] = {"status": "error", "message": str(e)}
                logger.error(f"Error updating model {model_id}: {e}")
        
        return {"status": "completed", "results": results}
    
    def get_optimal_model_for_content(
        self,
        content_type: str,
        complexity: str,
        content_length: int = 1000
    ) -> Optional[ModelInfo]:
        """Get optimal model based on content type, complexity, and length."""
        preset_models = self.get_preset_models(self.current_preset)
        
        # Enhanced model selection logic
        if content_type in ["manim_code", "python_code", "animation_code"]:
            # For coding tasks
            if complexity in ["advanced", "complex"]:
                # Use best available coding model
                return preset_models.get(ModelType.CODING)
            else:
                # For simple coding, lightweight model might suffice
                return preset_models.get(ModelType.LIGHTWEIGHT)
        
        elif content_type in ["script_generation", "educational_content", "content_analysis"]:
            # For content generation and analysis
            if complexity in ["advanced", "complex"] or content_length > 2000:
                # Use best reasoning model
                return preset_models.get(ModelType.REASONING)
            elif complexity == "simple" and content_length < 500:
                # Use lightweight model for simple tasks
                return preset_models.get(ModelType.LIGHTWEIGHT)
            else:
                # Use reasoning model for moderate complexity
                return preset_models.get(ModelType.REASONING)
        
        elif content_type in ["image_analysis", "diagram_understanding", "visual_content"]:
            # For vision tasks
            return preset_models.get(ModelType.VISION_LANGUAGE)
        
        else:
            # Default to reasoning model
            return preset_models.get(ModelType.REASONING)
    
    async def generate_with_ensemble(
        self,
        models: List[ModelInfo],
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        consensus_threshold: float = 0.7
    ) -> Optional[str]:
        """Generate content using model ensemble for improved quality."""
        if not models:
            return None
        
        try:
            # Generate responses from multiple models
            responses = []
            for model in models[:3]:  # Limit to 3 models for performance
                response = await self.generate_with_model(
                    model, prompt, temperature, max_tokens
                )
                if response:
                    responses.append(response)
            
            if not responses:
                return None
            
            # If only one response, return it
            if len(responses) == 1:
                return responses[0]
            
            # Simple ensemble: return longest response (often more detailed)
            # In a production system, you'd use more sophisticated consensus mechanisms
            best_response = max(responses, key=len)
            
            logger.info(f"Ensemble generation: {len(responses)} models, selected response length: {len(best_response)}")
            return best_response
            
        except Exception as e:
            logger.error(f"Ensemble generation failed: {e}")
            return None
    
    def route_to_optimal_model(
        self,
        task_type: str,
        content_complexity: str,
        content_length: int,
        performance_priority: str = "balanced"  # "speed", "quality", "balanced"
    ) -> Optional[ModelInfo]:
        """Intelligent model routing based on task requirements and performance priority."""
        try:
            # Get base model recommendation
            base_model = self.get_optimal_model_for_content(task_type, content_complexity, content_length)
            
            if not base_model:
                return None
            
            # Apply performance priority routing
            if performance_priority == "speed":
                # Prefer faster, smaller models
                if base_model.model_type == ModelType.REASONING:
                    # Use lightweight model for speed
                    preset_models = self.get_preset_models(self.current_preset)
                    return preset_models.get(ModelType.LIGHTWEIGHT, base_model)
                
            elif performance_priority == "quality":
                # Prefer larger, more capable models if system can handle it
                memory_gb = self.system_info["memory_gb"]
                
                if memory_gb > 24 and base_model.model_type == ModelType.CODING:
                    # Use advanced coding model if available
                    if "qwen2.5-coder-32b" in self.available_models:
                        return self.available_models["qwen2.5-coder-32b"]
                
                elif memory_gb > 32 and base_model.model_type == ModelType.REASONING:
                    # Use advanced reasoning model if available
                    if "deepseek-v3" in self.available_models:
                        return self.available_models["deepseek-v3"]
            
            # Default: return base model recommendation
            return base_model
            
        except Exception as e:
            logger.error(f"Model routing failed: {e}")
            return base_model if 'base_model' in locals() else None
    
    async def generate_with_fallback(
        self,
        primary_model: ModelInfo,
        fallback_models: List[ModelInfo],
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        max_retries: int = 3
    ) -> Optional[str]:
        """Generate content with automatic fallback to alternative models."""
        all_models = [primary_model] + fallback_models
        
        for attempt, model in enumerate(all_models):
            try:
                logger.info(f"Attempting generation with {model.name} (attempt {attempt + 1})")
                
                response = await self.generate_with_model(
                    model, prompt, temperature, max_tokens
                )
                
                if response and len(response.strip()) > 10:  # Minimum quality check
                    logger.info(f"✅ Generation successful with {model.name}")
                    return response
                else:
                    logger.warning(f"⚠️  Poor quality response from {model.name}")
                    
            except Exception as e:
                logger.warning(f"❌ Generation failed with {model.name}: {e}")
                continue
        
        logger.error("All model fallbacks exhausted")
        return None
    
    def get_model_performance_score(self, model: ModelInfo, task_type: str) -> float:
        """Calculate performance score for a model on a specific task type."""
        try:
            base_score = 0.5  # Default score
            
            # Task-specific scoring
            if task_type in ["manim_code", "python_code", "code_generation"]:
                if model.model_type == ModelType.CODING:
                    base_score += 0.3
                    # Bonus for advanced coding models
                    if "coder" in model.name.lower() and "32b" in model.parameters:
                        base_score += 0.2
                    elif "coder" in model.name.lower():
                        base_score += 0.1
                        
            elif task_type in ["content_analysis", "educational_content"]:
                if model.model_type == ModelType.REASONING:
                    base_score += 0.3
                    # Bonus for large reasoning models
                    if "70b" in model.parameters.lower() or "32b" in model.parameters:
                        base_score += 0.2
                        
            elif task_type in ["image_analysis", "visual_content"]:
                if model.model_type == ModelType.VISION_LANGUAGE:
                    base_score += 0.4
                    
            # Memory efficiency scoring (important for 16GB systems)
            memory_gb = self.system_info["memory_gb"]
            if memory_gb <= 16:
                if model.min_ram_gb <= 8:
                    base_score += 0.1  # Bonus for memory efficiency
                elif model.min_ram_gb > 16:
                    base_score -= 0.3  # Penalty for high memory usage
            
            # Parameter count efficiency
            if "7b" in model.parameters.lower():
                base_score += 0.05  # Good balance
            elif "3b" in model.parameters.lower():
                base_score += 0.02  # Efficient but less capable
            elif "32b" in model.parameters.lower() and memory_gb > 20:
                base_score += 0.1   # High capability if system can handle it
            
            return min(1.0, max(0.0, base_score))
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.5
    
    async def benchmark_models(self) -> Dict[str, Any]:
        """Benchmark available models for performance."""
        if not self.ollama_available:
            return {"status": "ollama_not_available"}
        
        benchmark_results = {}
        test_prompt = "Write a simple Python function that calculates the factorial of a number."
        
        preset_models = self.get_preset_models(self.current_preset)
        
        for model_type, model_info in preset_models.items():
            if await self.ensure_model_available(model_info):
                try:
                    import time
                    start_time = time.time()
                    
                    response = await self.generate_with_model(
                        model_info,
                        test_prompt,
                        temperature=0.1,
                        max_tokens=200
                    )
                    
                    end_time = time.time()
                    
                    if response:
                        benchmark_results[model_info.name] = {
                            "response_time": end_time - start_time,
                            "response_length": len(response),
                            "tokens_per_second": len(response.split()) / (end_time - start_time),
                            "status": "success"
                        }
                    else:
                        benchmark_results[model_info.name] = {
                            "status": "failed",
                            "error": "No response generated"
                        }
                        
                except Exception as e:
                    benchmark_results[model_info.name] = {
                        "status": "error",
                        "error": str(e)
                    }
        
        return {"status": "completed", "results": benchmark_results}
    
    async def install_recommended_models(self) -> Dict[str, Any]:
        """Install recommended models for the current system."""
        if not self.ollama_available:
            return {"status": "ollama_not_available"}
        
        preset_models = self.get_preset_models(self.current_preset)
        results = {}
        
        logger.info(f"Installing recommended models for {self.current_preset.value} preset...")
        
        for model_type, model_info in preset_models.items():
            try:
                logger.info(f"Installing {model_info.name} for {model_type.value} tasks...")
                
                success = await self.ensure_model_available(model_info)
                
                if success:
                    results[model_info.name] = {
                        "status": "success",
                        "type": model_type.value,
                        "size_gb": model_info.size_gb
                    }
                else:
                    results[model_info.name] = {
                        "status": "failed",
                        "type": model_type.value,
                        "error": "Installation failed"
                    }
                    
            except Exception as e:
                results[model_info.name] = {
                    "status": "error",
                    "type": model_type.value,
                    "error": str(e)
                }
        
        return {"status": "completed", "results": results}
    
    def get_system_recommendations(self) -> Dict[str, Any]:
        """Get system-specific recommendations."""
        memory_gb = self.system_info["memory_gb"]
        cpu_count = self.system_info["cpu_count"]
        gpu_info = self.system_info["gpu_info"]
        
        recommendations = {
            "recommended_preset": self.system_info["recommended_preset"],
            "memory_status": "adequate" if memory_gb >= 16 else "limited",
            "cpu_status": "adequate" if cpu_count >= 4 else "limited",
            "gpu_status": "available" if gpu_info else "not_detected",
            "warnings": [],
            "optimizations": []
        }
        
        # Add specific warnings and recommendations
        if memory_gb < 16:
            recommendations["warnings"].append("Less than 16GB RAM detected. Use FAST preset only.")
            recommendations["optimizations"].append("Consider upgrading to 16GB+ RAM for better performance.")
        
        if memory_gb <= 16:
            recommendations["warnings"].append("16GB RAM detected. FAST preset recommended.")
            recommendations["optimizations"].append("Use quantized models (q4_0) to reduce memory usage.")
        
        if not gpu_info:
            recommendations["optimizations"].append("GPU not detected. CPU-only inference will be slower.")
        
        if cpu_count < 4:
            recommendations["warnings"].append("Less than 4 CPU cores detected. Performance may be limited.")
        
        return recommendations
    
    def get_available_models_info(self) -> List[Dict[str, Any]]:
        """Get information about all available models."""
        models_info = []
        
        for model_id, model_info in self.available_models.items():
            memory_gb = self.system_info["memory_gb"]
            
            # Determine compatibility
            compatible = model_info.min_ram_gb <= memory_gb
            recommended = model_info.min_ram_gb <= memory_gb * 0.8  # Use 80% of RAM as safe limit
            
            models_info.append({
                "id": model_id,
                "name": model_info.name,
                "type": model_info.model_type.value,
                "size_gb": model_info.size_gb,
                "parameters": model_info.parameters,
                "description": model_info.description,
                "compatible": compatible,
                "recommended": recommended,
                "min_ram_gb": model_info.min_ram_gb,
                "recommended_for": model_info.recommended_for,
                "quantized_versions": model_info.quantized_versions or []
            })
        
        return models_info


# Global instance for easy access
ai_model_manager = AIModelManager()