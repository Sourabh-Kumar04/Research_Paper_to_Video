"""
AI Model Performance Profiler for RASO Platform

This module provides comprehensive performance profiling and benchmarking
for AI models, including hardware-specific optimization recommendations.
"""

import asyncio
import time
import psutil
import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .ai_model_manager import ai_model_manager, ModelInfo, ModelType, ModelPreset

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a model."""
    model_name: str
    response_time_avg: float
    response_time_std: float
    tokens_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    gpu_usage_percent: Optional[float]
    quality_score: float  # 0-1, based on response quality
    reliability_score: float  # 0-1, based on success rate
    efficiency_score: float  # 0-1, overall efficiency
    test_timestamp: str
    hardware_config: Dict[str, Any]


@dataclass
class BenchmarkTest:
    """A benchmark test configuration."""
    name: str
    prompt: str
    expected_length_range: Tuple[int, int]  # min, max tokens
    complexity: str  # simple, medium, complex
    task_type: str  # coding, reasoning, vision_language
    timeout_seconds: int = 120


class AIModelProfiler:
    """Comprehensive AI model performance profiler."""
    
    def __init__(self):
        self.benchmark_tests = self._create_benchmark_tests()
        self.results_file = Path("config/model_performance_results.json")
        self.cached_results = self._load_cached_results()
        
    def _create_benchmark_tests(self) -> List[BenchmarkTest]:
        """Create comprehensive benchmark test suite."""
        return [
            # Coding Tests
            BenchmarkTest(
                name="Simple Python Function",
                prompt="Write a Python function that calculates the factorial of a number using recursion.",
                expected_length_range=(50, 200),
                complexity="simple",
                task_type="coding"
            ),
            
            BenchmarkTest(
                name="Manim Animation Code",
                prompt="Write a Manim scene that animates the equation y = x^2 being graphed, with the equation appearing first, then the axes, then the curve being drawn.",
                expected_length_range=(200, 500),
                complexity="medium",
                task_type="coding"
            ),
            
            BenchmarkTest(
                name="Complex Algorithm",
                prompt="Implement a Python class for a binary search tree with insert, delete, search, and in-order traversal methods. Include proper error handling and documentation.",
                expected_length_range=(300, 800),
                complexity="complex",
                task_type="coding"
            ),
            
            # Reasoning Tests
            BenchmarkTest(
                name="Simple Explanation",
                prompt="Explain what photosynthesis is in simple terms suitable for a middle school student.",
                expected_length_range=(100, 300),
                complexity="simple",
                task_type="reasoning"
            ),
            
            BenchmarkTest(
                name="Educational Content",
                prompt="Create an educational explanation of quantum entanglement that includes the key concepts, real-world applications, and why it's important for quantum computing.",
                expected_length_range=(300, 600),
                complexity="medium",
                task_type="reasoning"
            ),
            
            BenchmarkTest(
                name="Complex Analysis",
                prompt="Analyze the potential implications of artificial general intelligence on society, economy, and human development. Consider both positive and negative aspects, timeline considerations, and policy recommendations.",
                expected_length_range=(500, 1000),
                complexity="complex",
                task_type="reasoning"
            ),
            
            # Vision-Language Tests (for VL models)
            BenchmarkTest(
                name="Image Description",
                prompt="Describe what you would expect to see in a diagram showing the water cycle, including all major components and processes.",
                expected_length_range=(150, 400),
                complexity="simple",
                task_type="vision_language"
            ),
            
            BenchmarkTest(
                name="Diagram Analysis",
                prompt="Explain how you would analyze a flowchart diagram to understand a software development process, including what elements to look for and how to interpret the connections.",
                expected_length_range=(200, 500),
                complexity="medium",
                task_type="vision_language"
            )
        ]
    
    def _load_cached_results(self) -> Dict[str, Any]:
        """Load cached performance results."""
        try:
            if self.results_file.exists():
                with open(self.results_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"Failed to load cached results: {e}")
            return {}
    
    def _save_results(self) -> None:
        """Save performance results to cache."""
        try:
            self.results_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.results_file, 'w') as f:
                json.dump(self.cached_results, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    async def profile_model(
        self,
        model_info: ModelInfo,
        num_iterations: int = 3,
        include_quality_assessment: bool = True
    ) -> PerformanceMetrics:
        """Profile a single model's performance."""
        logger.info(f"Profiling model: {model_info.name}")
        
        # Ensure model is available
        if not await ai_model_manager.ensure_model_available(model_info):
            raise RuntimeError(f"Model {model_info.name} not available")
        
        # Get appropriate tests for model type
        relevant_tests = [
            test for test in self.benchmark_tests
            if test.task_type == model_info.model_type.value or 
               model_info.model_type == ModelType.REASONING  # Reasoning models can handle most tasks
        ]
        
        if not relevant_tests:
            # Fallback to simple tests
            relevant_tests = [test for test in self.benchmark_tests if test.complexity == "simple"]
        
        # Run benchmark tests
        response_times = []
        token_rates = []
        memory_usages = []
        cpu_usages = []
        gpu_usages = []
        quality_scores = []
        success_count = 0
        
        for iteration in range(num_iterations):
            logger.info(f"Running iteration {iteration + 1}/{num_iterations}")
            
            for test in relevant_tests[:3]:  # Limit to 3 tests per iteration for performance
                try:
                    # Monitor system resources before test
                    initial_memory = psutil.virtual_memory().used / (1024**2)  # MB
                    initial_cpu = psutil.cpu_percent()
                    
                    # Run the test
                    start_time = time.time()
                    
                    response = await ai_model_manager.generate_with_model(
                        model_info,
                        test.prompt,
                        temperature=0.1,  # Low temperature for consistent benchmarking
                        max_tokens=1000
                    )
                    
                    end_time = time.time()
                    
                    if response:
                        # Calculate metrics
                        response_time = end_time - start_time
                        response_length = len(response.split())
                        tokens_per_second = response_length / response_time if response_time > 0 else 0
                        
                        # Monitor system resources after test
                        final_memory = psutil.virtual_memory().used / (1024**2)  # MB
                        final_cpu = psutil.cpu_percent()
                        
                        memory_usage = final_memory - initial_memory
                        cpu_usage = final_cpu
                        
                        # GPU usage (if available)
                        gpu_usage = await self._get_gpu_usage()
                        
                        # Quality assessment
                        quality_score = 0.8  # Default score
                        if include_quality_assessment:
                            quality_score = self._assess_response_quality(
                                response, test.expected_length_range, test.complexity
                            )
                        
                        # Store metrics
                        response_times.append(response_time)
                        token_rates.append(tokens_per_second)
                        memory_usages.append(max(0, memory_usage))  # Ensure non-negative
                        cpu_usages.append(cpu_usage)
                        if gpu_usage is not None:
                            gpu_usages.append(gpu_usage)
                        quality_scores.append(quality_score)
                        success_count += 1
                        
                        logger.debug(f"Test '{test.name}': {response_time:.2f}s, {tokens_per_second:.1f} tok/s")
                    
                    # Small delay between tests
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Test '{test.name}' failed: {e}")
                    continue
        
        # Calculate aggregate metrics
        if not response_times:
            raise RuntimeError(f"All benchmark tests failed for model {model_info.name}")
        
        avg_response_time = statistics.mean(response_times)
        std_response_time = statistics.stdev(response_times) if len(response_times) > 1 else 0
        avg_tokens_per_second = statistics.mean(token_rates)
        avg_memory_usage = statistics.mean(memory_usages)
        avg_cpu_usage = statistics.mean(cpu_usages)
        avg_gpu_usage = statistics.mean(gpu_usages) if gpu_usages else None
        avg_quality_score = statistics.mean(quality_scores)
        
        # Calculate reliability score (success rate)
        total_tests = num_iterations * len(relevant_tests[:3])
        reliability_score = success_count / total_tests if total_tests > 0 else 0
        
        # Calculate efficiency score (composite metric)
        efficiency_score = self._calculate_efficiency_score(
            avg_tokens_per_second, avg_memory_usage, avg_quality_score, reliability_score
        )
        
        # Create performance metrics
        metrics = PerformanceMetrics(
            model_name=model_info.name,
            response_time_avg=avg_response_time,
            response_time_std=std_response_time,
            tokens_per_second=avg_tokens_per_second,
            memory_usage_mb=avg_memory_usage,
            cpu_usage_percent=avg_cpu_usage,
            gpu_usage_percent=avg_gpu_usage,
            quality_score=avg_quality_score,
            reliability_score=reliability_score,
            efficiency_score=efficiency_score,
            test_timestamp=datetime.now().isoformat(),
            hardware_config=ai_model_manager.system_info
        )
        
        # Cache results
        self.cached_results[model_info.name] = asdict(metrics)
        self._save_results()
        
        logger.info(f"Profiling complete for {model_info.name}: "
                   f"{avg_tokens_per_second:.1f} tok/s, "
                   f"quality: {avg_quality_score:.2f}, "
                   f"efficiency: {efficiency_score:.2f}")
        
        return metrics
    
    async def _get_gpu_usage(self) -> Optional[float]:
        """Get current GPU usage percentage."""
        try:
            import subprocess
            
            # Try NVIDIA first
            result = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                usage_str = stdout.decode().strip()
                if usage_str and usage_str.isdigit():
                    return float(usage_str)
            
            return None
            
        except Exception:
            return None
    
    def _assess_response_quality(
        self,
        response: str,
        expected_length_range: Tuple[int, int],
        complexity: str
    ) -> float:
        """Assess the quality of a model response."""
        try:
            score = 0.5  # Base score
            
            # Length assessment
            response_length = len(response.split())
            min_length, max_length = expected_length_range
            
            if min_length <= response_length <= max_length:
                score += 0.2  # Good length
            elif response_length < min_length * 0.5:
                score -= 0.2  # Too short
            elif response_length > max_length * 2:
                score -= 0.1  # Too long
            
            # Content quality indicators
            if any(keyword in response.lower() for keyword in ['def ', 'class ', 'import ', 'from ']):
                score += 0.1  # Contains code-like content
            
            if any(keyword in response.lower() for keyword in ['explanation', 'example', 'because', 'therefore']):
                score += 0.1  # Contains explanatory content
            
            # Complexity appropriateness
            if complexity == "simple" and len(response.split()) > 500:
                score -= 0.1  # Too complex for simple task
            elif complexity == "complex" and len(response.split()) < 200:
                score -= 0.2  # Too simple for complex task
            
            # Basic coherence check
            sentences = response.split('.')
            if len(sentences) > 1:
                score += 0.1  # Multi-sentence response
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return 0.5  # Default score
    
    def _calculate_efficiency_score(
        self,
        tokens_per_second: float,
        memory_usage_mb: float,
        quality_score: float,
        reliability_score: float
    ) -> float:
        """Calculate overall efficiency score."""
        try:
            # Normalize metrics (0-1 scale)
            
            # Speed score (normalize to reasonable range)
            speed_score = min(1.0, tokens_per_second / 50.0)  # 50 tok/s = perfect speed
            
            # Memory efficiency score (lower is better)
            memory_score = max(0.0, 1.0 - (memory_usage_mb / 1000.0))  # 1GB = 0 score
            
            # Weighted combination
            efficiency = (
                speed_score * 0.3 +
                memory_score * 0.2 +
                quality_score * 0.3 +
                reliability_score * 0.2
            )
            
            return max(0.0, min(1.0, efficiency))
            
        except Exception as e:
            logger.warning(f"Efficiency calculation failed: {e}")
            return 0.5
    
    async def profile_all_available_models(
        self,
        preset: Optional[ModelPreset] = None,
        num_iterations: int = 2
    ) -> Dict[str, PerformanceMetrics]:
        """Profile all available models or models in a specific preset."""
        results = {}
        
        if preset:
            models_to_test = ai_model_manager.get_preset_models(preset)
            model_list = list(models_to_test.values())
        else:
            model_list = list(ai_model_manager.available_models.values())
        
        logger.info(f"Profiling {len(model_list)} models...")
        
        for i, model_info in enumerate(model_list):
            try:
                logger.info(f"Profiling model {i+1}/{len(model_list)}: {model_info.name}")
                
                # Check if model is compatible with current system
                system_memory = ai_model_manager.system_info.get("memory_gb", 16)
                if model_info.min_ram_gb > system_memory:
                    logger.warning(f"Skipping {model_info.name}: requires {model_info.min_ram_gb}GB RAM, "
                                 f"system has {system_memory}GB")
                    continue
                
                metrics = await self.profile_model(model_info, num_iterations)
                results[model_info.name] = metrics
                
                # Small delay between models to prevent overheating
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Failed to profile {model_info.name}: {e}")
                continue
        
        logger.info(f"Profiling complete. Successfully profiled {len(results)} models.")
        return results
    
    def get_model_recommendations(
        self,
        task_type: str,
        performance_priority: str = "balanced",  # speed, quality, balanced
        max_memory_gb: Optional[float] = None
    ) -> List[Tuple[str, PerformanceMetrics, float]]:
        """Get model recommendations based on performance data."""
        if max_memory_gb is None:
            max_memory_gb = ai_model_manager.system_info.get("memory_gb", 16)
        
        # Filter cached results
        suitable_models = []
        
        for model_name, metrics_dict in self.cached_results.items():
            try:
                # Find model info
                model_info = None
                for info in ai_model_manager.available_models.values():
                    if info.name == model_name:
                        model_info = info
                        break
                
                if not model_info:
                    continue
                
                # Check memory compatibility
                if model_info.min_ram_gb > max_memory_gb:
                    continue
                
                # Check task type compatibility
                if (task_type in ["coding", "manim_code", "python_code"] and 
                    model_info.model_type not in [ModelType.CODING, ModelType.REASONING]):
                    continue
                elif (task_type in ["vision", "image_analysis", "diagram"] and 
                      model_info.model_type != ModelType.VISION_LANGUAGE):
                    continue
                
                # Create metrics object
                metrics = PerformanceMetrics(**metrics_dict)
                
                # Calculate recommendation score based on priority
                if performance_priority == "speed":
                    score = (
                        metrics.tokens_per_second * 0.4 +
                        (1.0 - metrics.response_time_avg / 60.0) * 0.3 +  # Normalize to 60s max
                        metrics.reliability_score * 0.2 +
                        metrics.quality_score * 0.1
                    )
                elif performance_priority == "quality":
                    score = (
                        metrics.quality_score * 0.4 +
                        metrics.reliability_score * 0.3 +
                        metrics.efficiency_score * 0.2 +
                        metrics.tokens_per_second / 50.0 * 0.1  # Normalize speed
                    )
                else:  # balanced
                    score = metrics.efficiency_score
                
                suitable_models.append((model_name, metrics, score))
                
            except Exception as e:
                logger.warning(f"Error processing cached results for {model_name}: {e}")
                continue
        
        # Sort by recommendation score
        suitable_models.sort(key=lambda x: x[2], reverse=True)
        
        return suitable_models[:5]  # Top 5 recommendations
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.cached_results:
            return {"status": "no_data", "message": "No performance data available"}
        
        # Analyze results
        all_metrics = []
        for metrics_dict in self.cached_results.values():
            try:
                metrics = PerformanceMetrics(**metrics_dict)
                all_metrics.append(metrics)
            except Exception:
                continue
        
        if not all_metrics:
            return {"status": "error", "message": "Failed to parse performance data"}
        
        # Calculate statistics
        avg_response_time = statistics.mean([m.response_time_avg for m in all_metrics])
        avg_tokens_per_second = statistics.mean([m.tokens_per_second for m in all_metrics])
        avg_quality_score = statistics.mean([m.quality_score for m in all_metrics])
        avg_efficiency_score = statistics.mean([m.efficiency_score for m in all_metrics])
        
        # Find best performers
        fastest_model = max(all_metrics, key=lambda m: m.tokens_per_second)
        highest_quality = max(all_metrics, key=lambda m: m.quality_score)
        most_efficient = max(all_metrics, key=lambda m: m.efficiency_score)
        most_reliable = max(all_metrics, key=lambda m: m.reliability_score)
        
        # System recommendations
        system_memory = ai_model_manager.system_info.get("memory_gb", 16)
        recommendations = []
        
        if system_memory <= 16:
            recommendations.append("Consider using FAST preset for optimal performance on 16GB systems")
            recommendations.append("Use quantized models (q4_0) to reduce memory usage")
        
        if avg_response_time > 30:
            recommendations.append("Consider using smaller models for faster response times")
        
        if avg_quality_score < 0.7:
            recommendations.append("Consider using larger models for better quality output")
        
        return {
            "status": "success",
            "summary": {
                "total_models_tested": len(all_metrics),
                "avg_response_time": avg_response_time,
                "avg_tokens_per_second": avg_tokens_per_second,
                "avg_quality_score": avg_quality_score,
                "avg_efficiency_score": avg_efficiency_score
            },
            "best_performers": {
                "fastest": {
                    "model": fastest_model.model_name,
                    "tokens_per_second": fastest_model.tokens_per_second
                },
                "highest_quality": {
                    "model": highest_quality.model_name,
                    "quality_score": highest_quality.quality_score
                },
                "most_efficient": {
                    "model": most_efficient.model_name,
                    "efficiency_score": most_efficient.efficiency_score
                },
                "most_reliable": {
                    "model": most_reliable.model_name,
                    "reliability_score": most_reliable.reliability_score
                }
            },
            "recommendations": recommendations,
            "system_info": ai_model_manager.system_info,
            "last_updated": datetime.now().isoformat()
        }
    
    def clear_cached_results(self) -> None:
        """Clear all cached performance results."""
        self.cached_results = {}
        if self.results_file.exists():
            self.results_file.unlink()
        logger.info("Cleared all cached performance results")


# Global instance for easy access
ai_model_profiler = AIModelProfiler()