"""
AI Model Configuration Interface for RASO Platform

This module provides a web-based interface for configuring AI model selection,
performance benchmarking, and hardware-optimized recommendations.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, render_template, request, jsonify, send_from_directory
import logging

from .ai_model_manager import ai_model_manager, ModelPreset, ModelType

logger = logging.getLogger(__name__)


@dataclass
class ModelConfigurationState:
    """Current model configuration state."""
    current_preset: str
    selected_models: Dict[str, str]  # task_type -> model_id
    custom_configurations: Dict[str, Dict[str, Any]]
    performance_benchmarks: Dict[str, Dict[str, Any]]
    system_info: Dict[str, Any]
    last_updated: str


class AIModelConfigUI:
    """Web-based AI model configuration interface."""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.app = Flask(__name__, 
                        template_folder=Path(__file__).parent / "templates",
                        static_folder=Path(__file__).parent / "static")
        self.host = host
        self.port = port
        self.config_file = Path("config/ai_model_config.json")
        self.config_state = self._load_configuration()
        
        self._setup_routes()
    
    def _load_configuration(self) -> ModelConfigurationState:
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return ModelConfigurationState(**data)
            else:
                # Create default configuration
                return self._create_default_configuration()
                
        except Exception as e:
            logger.warning(f"Failed to load configuration: {e}")
            return self._create_default_configuration()
    
    def _create_default_configuration(self) -> ModelConfigurationState:
        """Create default model configuration."""
        system_info = ai_model_manager.system_info
        recommended_preset = system_info.get("recommended_preset", ModelPreset.FAST)
        
        # Get default models for recommended preset
        preset_models = ai_model_manager.get_preset_models(recommended_preset)
        
        selected_models = {}
        for model_type, model_info in preset_models.items():
            selected_models[model_type.value] = model_info.name
        
        return ModelConfigurationState(
            current_preset=recommended_preset.value,
            selected_models=selected_models,
            custom_configurations={},
            performance_benchmarks={},
            system_info=system_info,
            last_updated=""
        )
    
    def _save_configuration(self) -> None:
        """Save current configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config_state), f, indent=2, default=str)
                
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def _setup_routes(self) -> None:
        """Set up Flask routes for the web interface."""
        
        @self.app.route('/')
        def index():
            """Main configuration interface."""
            return render_template('ai_model_config.html')
        
        @self.app.route('/api/system-info')
        def get_system_info():
            """Get system hardware information and recommendations."""
            try:
                system_info = ai_model_manager.system_info
                recommendations = ai_model_manager.get_system_recommendations()
                
                return jsonify({
                    "status": "success",
                    "system_info": system_info,
                    "recommendations": recommendations
                })
                
            except Exception as e:
                logger.error(f"Error getting system info: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/available-models')
        def get_available_models():
            """Get list of all available models with compatibility info."""
            try:
                models_info = ai_model_manager.get_available_models_info()
                
                return jsonify({
                    "status": "success",
                    "models": models_info
                })
                
            except Exception as e:
                logger.error(f"Error getting available models: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/preset-models/<preset>')
        def get_preset_models(preset):
            """Get recommended models for a specific preset."""
            try:
                preset_enum = ModelPreset(preset)
                preset_models = ai_model_manager.get_preset_models(preset_enum)
                
                models_data = {}
                for model_type, model_info in preset_models.items():
                    models_data[model_type.value] = {
                        "name": model_info.name,
                        "model_id": model_info.model_id,
                        "size_gb": model_info.size_gb,
                        "parameters": model_info.parameters,
                        "description": model_info.description,
                        "recommended_for": model_info.recommended_for
                    }
                
                return jsonify({
                    "status": "success",
                    "preset": preset,
                    "models": models_data
                })
                
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid preset"}), 400
            except Exception as e:
                logger.error(f"Error getting preset models: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/current-config')
        def get_current_config():
            """Get current model configuration."""
            try:
                return jsonify({
                    "status": "success",
                    "config": asdict(self.config_state)
                })
                
            except Exception as e:
                logger.error(f"Error getting current config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/set-preset', methods=['POST'])
        def set_preset():
            """Set model preset."""
            try:
                data = request.get_json()
                preset_name = data.get('preset')
                
                if not preset_name:
                    return jsonify({"status": "error", "message": "Preset required"}), 400
                
                preset_enum = ModelPreset(preset_name)
                ai_model_manager.set_preset(preset_enum)
                
                # Update configuration state
                self.config_state.current_preset = preset_name
                
                # Update selected models for new preset
                preset_models = ai_model_manager.get_preset_models(preset_enum)
                for model_type, model_info in preset_models.items():
                    self.config_state.selected_models[model_type.value] = model_info.name
                
                self._save_configuration()
                
                return jsonify({
                    "status": "success",
                    "message": f"Preset set to {preset_name}",
                    "selected_models": self.config_state.selected_models
                })
                
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid preset"}), 400
            except Exception as e:
                logger.error(f"Error setting preset: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/set-custom-model', methods=['POST'])
        def set_custom_model():
            """Set custom model for specific task type."""
            try:
                data = request.get_json()
                task_type = data.get('task_type')
                model_name = data.get('model_name')
                
                if not task_type or not model_name:
                    return jsonify({"status": "error", "message": "Task type and model name required"}), 400
                
                # Validate model exists
                model_found = False
                for model_info in ai_model_manager.available_models.values():
                    if model_info.name == model_name:
                        model_found = True
                        break
                
                if not model_found:
                    return jsonify({"status": "error", "message": "Model not found"}), 404
                
                # Update configuration
                self.config_state.current_preset = "custom"
                self.config_state.selected_models[task_type] = model_name
                
                self._save_configuration()
                
                return jsonify({
                    "status": "success",
                    "message": f"Custom model set for {task_type}",
                    "task_type": task_type,
                    "model_name": model_name
                })
                
            except Exception as e:
                logger.error(f"Error setting custom model: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/benchmark-models', methods=['POST'])
        async def benchmark_models():
            """Run performance benchmarks on available models."""
            try:
                # Run benchmarks asynchronously
                benchmark_results = await ai_model_manager.benchmark_models()
                
                # Update configuration state
                self.config_state.performance_benchmarks = benchmark_results.get("results", {})
                self._save_configuration()
                
                return jsonify({
                    "status": "success",
                    "benchmarks": benchmark_results
                })
                
            except Exception as e:
                logger.error(f"Error running benchmarks: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/install-models', methods=['POST'])
        async def install_models():
            """Install recommended models for current preset."""
            try:
                # Install models asynchronously
                install_results = await ai_model_manager.install_recommended_models()
                
                return jsonify({
                    "status": "success",
                    "installation": install_results
                })
                
            except Exception as e:
                logger.error(f"Error installing models: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/model-status')
        async def get_model_status():
            """Get status of installed models."""
            try:
                model_status = await ai_model_manager.check_model_updates()
                
                return jsonify({
                    "status": "success",
                    "model_status": model_status
                })
                
            except Exception as e:
                logger.error(f"Error getting model status: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/optimize-for-hardware', methods=['POST'])
        def optimize_for_hardware():
            """Get hardware-optimized model recommendations."""
            try:
                data = request.get_json()
                priority = data.get('priority', 'balanced')  # speed, quality, balanced
                
                system_info = ai_model_manager.system_info
                memory_gb = system_info.get("memory_gb", 16)
                
                recommendations = {}
                
                # Generate recommendations based on hardware and priority
                if priority == "speed":
                    # Prioritize fastest models
                    if memory_gb >= 16:
                        recommendations = {
                            "coding": "CodeQwen1.5-7B-Chat",
                            "reasoning": "Llama-3.2-3B-Instruct",
                            "vision_language": "Moondream2",
                            "preset": "fast"
                        }
                    else:
                        recommendations = {
                            "coding": "Llama-3.2-3B-Instruct",
                            "reasoning": "Llama-3.2-3B-Instruct",
                            "vision_language": "Moondream2",
                            "preset": "fast"
                        }
                
                elif priority == "quality":
                    # Prioritize best quality within hardware limits
                    if memory_gb >= 32:
                        recommendations = {
                            "coding": "Qwen2.5-Coder-32B-Instruct",
                            "reasoning": "DeepSeek-V3",
                            "vision_language": "LLaVA-NeXT-34B",
                            "preset": "quality"
                        }
                    elif memory_gb >= 20:
                        recommendations = {
                            "coding": "Codestral-22B-v0.1",
                            "reasoning": "Qwen2.5-14B-Instruct",
                            "vision_language": "Qwen2-VL-7B-Instruct",
                            "preset": "balanced"
                        }
                    else:
                        recommendations = {
                            "coding": "Qwen2.5-7B-Instruct",
                            "reasoning": "Qwen2.5-7B-Instruct",
                            "vision_language": "Qwen2-VL-7B-Instruct",
                            "preset": "fast"
                        }
                
                else:  # balanced
                    # Balance between speed and quality
                    if memory_gb >= 20:
                        recommendations = {
                            "coding": "CodeQwen1.5-7B-Chat",
                            "reasoning": "Qwen2.5-14B-Instruct",
                            "vision_language": "Qwen2-VL-7B-Instruct",
                            "preset": "balanced"
                        }
                    else:
                        recommendations = {
                            "coding": "CodeQwen1.5-7B-Chat",
                            "reasoning": "Qwen2.5-7B-Instruct",
                            "vision_language": "Moondream2",
                            "preset": "fast"
                        }
                
                return jsonify({
                    "status": "success",
                    "recommendations": recommendations,
                    "priority": priority,
                    "system_memory_gb": memory_gb
                })
                
            except Exception as e:
                logger.error(f"Error optimizing for hardware: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            """Serve static files."""
            return send_from_directory(self.app.static_folder, filename)
    
    def run(self, debug: bool = False) -> None:
        """Run the configuration interface."""
        logger.info(f"Starting AI Model Configuration UI on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug)
    
    async def run_async(self, debug: bool = False) -> None:
        """Run the configuration interface asynchronously."""
        from hypercorn.asyncio import serve
        from hypercorn.config import Config
        
        config = Config()
        config.bind = [f"{self.host}:{self.port}"]
        
        logger.info(f"Starting AI Model Configuration UI on http://{self.host}:{self.port}")
        await serve(self.app, config)


# Global instance for easy access
ai_config_ui = AIModelConfigUI()


if __name__ == "__main__":
    # Run the configuration interface
    ai_config_ui.run(debug=True)