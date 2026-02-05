"""
Performance Monitoring and Optimization System

This module provides comprehensive performance monitoring, hardware acceleration detection,
parallel processing capabilities, and progress reporting for video generation tasks.
"""

import os
import time
import psutil
import threading
import multiprocessing
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import json
import logging
import queue
import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class SystemInfo:
    """System hardware information"""
    cpu_count: int
    cpu_freq: float
    memory_total: int
    memory_available: int
    gpu_available: bool
    gpu_info: List[Dict[str, Any]]
    disk_space: Dict[str, int]
    platform: str

@dataclass
class PerformanceMetrics:
    """Performance metrics for a task"""
    task_id: str
    task_name: str
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    cpu_usage: List[float]
    memory_usage: List[float]
    gpu_usage: List[float]
    disk_io: Dict[str, int]
    network_io: Dict[str, int]
    custom_metrics: Dict[str, Any]

@dataclass
class ProgressUpdate:
    """Progress update for a task"""
    task_id: str
    task_name: str
    progress: float  # 0.0 to 1.0
    stage: str
    message: str
    timestamp: float
    estimated_remaining: Optional[float]

class HardwareAccelerationDetector:
    """Detects and manages hardware acceleration capabilities"""
    
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        self.cuda_available = self._check_cuda()
        self.opencl_available = self._check_opencl()
        self.ffmpeg_gpu_support = self._check_ffmpeg_gpu()
    
    def _detect_gpu(self) -> List[Dict[str, Any]]:
        """Detect available GPUs"""
        gpus = []
        
        try:
            # Try nvidia-ml-py for NVIDIA GPUs
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                gpus.append({
                    'index': i,
                    'name': name,
                    'vendor': 'NVIDIA',
                    'memory_total': memory_info.total,
                    'memory_free': memory_info.free,
                    'memory_used': memory_info.used
                })
                
        except ImportError:
            logger.info("pynvml not available, trying alternative GPU detection")
        except Exception as e:
            logger.warning(f"NVIDIA GPU detection failed: {e}")
        
        # Try alternative methods for other GPUs
        try:
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'VGA' in line or 'Display' in line:
                        if 'NVIDIA' not in line and len(gpus) == 0:  # Don't duplicate NVIDIA
                            gpus.append({
                                'name': line.strip(),
                                'vendor': 'Unknown',
                                'memory_total': 0,
                                'memory_free': 0,
                                'memory_used': 0
                            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return gpus
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_opencl(self) -> bool:
        """Check if OpenCL is available"""
        try:
            import pyopencl as cl
            platforms = cl.get_platforms()
            return len(platforms) > 0
        except ImportError:
            return False
        except Exception:
            return False
    
    def _check_ffmpeg_gpu(self) -> Dict[str, bool]:
        """Check FFmpeg GPU acceleration support"""
        support = {
            'nvenc': False,
            'vaapi': False,
            'qsv': False,
            'videotoolbox': False
        }
        
        try:
            result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                output = result.stdout.lower()
                support['nvenc'] = 'nvenc' in output
                support['vaapi'] = 'vaapi' in output
                support['qsv'] = 'qsv' in output
                support['videotoolbox'] = 'videotoolbox' in output
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("FFmpeg not found or not responding")
        
        return support
    
    def get_best_encoder(self) -> str:
        """Get the best available hardware encoder"""
        if self.ffmpeg_gpu_support['nvenc'] and self.cuda_available:
            return 'h264_nvenc'
        elif self.ffmpeg_gpu_support['qsv']:
            return 'h264_qsv'
        elif self.ffmpeg_gpu_support['vaapi']:
            return 'h264_vaapi'
        elif self.ffmpeg_gpu_support['videotoolbox']:
            return 'h264_videotoolbox'
        else:
            return 'libx264'  # Software fallback
    
    def get_acceleration_flags(self) -> List[str]:
        """Get FFmpeg acceleration flags"""
        flags = []
        
        if self.cuda_available and self.ffmpeg_gpu_support['nvenc']:
            flags.extend(['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'])
        elif self.ffmpeg_gpu_support['vaapi']:
            flags.extend(['-hwaccel', 'vaapi'])
        elif self.ffmpeg_gpu_support['qsv']:
            flags.extend(['-hwaccel', 'qsv'])
        
        return flags

class PerformanceMonitor:
    """Monitors system performance during tasks"""
    
    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.active_tasks = {}
        self.completed_tasks = {}
        self.monitoring_threads = {}
        self.hardware_detector = HardwareAccelerationDetector()
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> SystemInfo:
        """Get system hardware information"""
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemInfo(
            cpu_count=psutil.cpu_count(),
            cpu_freq=cpu_freq.current if cpu_freq else 0.0,
            memory_total=memory.total,
            memory_available=memory.available,
            gpu_available=len(self.hardware_detector.gpu_info) > 0,
            gpu_info=self.hardware_detector.gpu_info,
            disk_space={'total': disk.total, 'free': disk.free, 'used': disk.used},
            platform=os.name
        )
    
    def start_monitoring(self, task_id: str, task_name: str) -> PerformanceMetrics:
        """Start monitoring a task"""
        metrics = PerformanceMetrics(
            task_id=task_id,
            task_name=task_name,
            start_time=time.time(),
            end_time=None,
            duration=None,
            cpu_usage=[],
            memory_usage=[],
            gpu_usage=[],
            disk_io={'read': 0, 'write': 0},
            network_io={'sent': 0, 'recv': 0},
            custom_metrics={}
        )
        
        self.active_tasks[task_id] = metrics
        
        # Start monitoring thread
        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=self._monitor_task,
            args=(task_id, stop_event),
            daemon=True
        )
        monitor_thread.start()
        self.monitoring_threads[task_id] = (monitor_thread, stop_event)
        
        logger.info(f"Started monitoring task: {task_name} ({task_id})")
        return metrics
    
    def stop_monitoring(self, task_id: str) -> Optional[PerformanceMetrics]:
        """Stop monitoring a task"""
        if task_id not in self.active_tasks:
            return None
        
        # Stop monitoring thread
        if task_id in self.monitoring_threads:
            thread, stop_event = self.monitoring_threads[task_id]
            stop_event.set()
            thread.join(timeout=2.0)
            del self.monitoring_threads[task_id]
        
        # Finalize metrics
        metrics = self.active_tasks[task_id]
        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time
        
        # Move to completed tasks
        self.completed_tasks[task_id] = metrics
        del self.active_tasks[task_id]
        
        logger.info(f"Stopped monitoring task: {metrics.task_name} ({task_id}) - Duration: {metrics.duration:.2f}s")
        return metrics
    
    def _monitor_task(self, task_id: str, stop_event: threading.Event):
        """Monitor task performance in background thread"""
        process = psutil.Process()
        initial_disk_io = psutil.disk_io_counters()
        initial_net_io = psutil.net_io_counters()
        
        while not stop_event.wait(self.monitoring_interval):
            if task_id not in self.active_tasks:
                break
            
            try:
                metrics = self.active_tasks[task_id]
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                metrics.cpu_usage.append(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                metrics.memory_usage.append(memory.percent)
                
                # GPU usage (if available)
                gpu_usage = self._get_gpu_usage()
                if gpu_usage:
                    metrics.gpu_usage.append(gpu_usage)
                
                # Disk I/O
                current_disk_io = psutil.disk_io_counters()
                if current_disk_io and initial_disk_io:
                    metrics.disk_io['read'] = current_disk_io.read_bytes - initial_disk_io.read_bytes
                    metrics.disk_io['write'] = current_disk_io.write_bytes - initial_disk_io.write_bytes
                
                # Network I/O
                current_net_io = psutil.net_io_counters()
                if current_net_io and initial_net_io:
                    metrics.network_io['sent'] = current_net_io.bytes_sent - initial_net_io.bytes_sent
                    metrics.network_io['recv'] = current_net_io.bytes_recv - initial_net_io.bytes_recv
                
            except Exception as e:
                logger.warning(f"Error monitoring task {task_id}: {e}")
    
    def _get_gpu_usage(self) -> Optional[float]:
        """Get current GPU usage"""
        try:
            import pynvml
            if len(self.hardware_detector.gpu_info) > 0:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Use first GPU
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                return utilization.gpu
        except Exception:
            pass
        return None
    
    def add_custom_metric(self, task_id: str, metric_name: str, value: Any):
        """Add custom metric to a task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].custom_metrics[metric_name] = value
    
    def get_task_metrics(self, task_id: str) -> Optional[PerformanceMetrics]:
        """Get metrics for a task"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        return None
    
    def start_operation(self, operation_name: str) -> str:
        """
        Start monitoring an operation (alias for start_monitoring with auto-generated task_id)
        
        Args:
            operation_name: Name of the operation to monitor
            
        Returns:
            Task ID for the operation
        """
        task_id = f"{operation_name}_{int(time.time())}"
        self.start_monitoring(task_id, operation_name)
        return task_id
    
    def end_operation(self, task_id: str, success: bool = True, error: str = None) -> Optional[PerformanceMetrics]:
        """
        End monitoring an operation (alias for stop_monitoring with additional metadata)
        
        Args:
            task_id: Task ID returned by start_operation
            success: Whether the operation was successful
            error: Error message if operation failed
            
        Returns:
            Final performance metrics
        """
        metrics = self.stop_monitoring(task_id)
        
        if metrics and not success and error:
            # Add error information to custom metrics
            metrics.custom_metrics['success'] = success
            metrics.custom_metrics['error'] = error
            logger.error(f"Operation {metrics.task_name} failed: {error}")
        elif metrics and success:
            metrics.custom_metrics['success'] = success
            logger.info(f"Operation {metrics.task_name} completed successfully in {metrics.duration:.2f}s")
        
        return metrics

    def get_system_performance_summary(self) -> Dict[str, Any]:
        """Get overall system performance summary"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_usage': (disk.used / disk.total) * 100,
            'disk_free_gb': disk.free / (1024**3),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'gpu_available': self.system_info.gpu_available,
            'hardware_acceleration': {
                'cuda': self.hardware_detector.cuda_available,
                'opencl': self.hardware_detector.opencl_available,
                'ffmpeg_gpu': self.hardware_detector.ffmpeg_gpu_support
            }
        }

class ParallelProcessor:
    """Manages parallel processing of video generation tasks"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 8)
        self.performance_monitor = PerformanceMonitor()
        
    def process_scenes_parallel(self, 
                              scenes: List[Dict[str, Any]], 
                              process_func: Callable,
                              progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        Process video scenes in parallel
        
        Args:
            scenes: List of scene data
            process_func: Function to process each scene
            progress_callback: Optional progress callback
            
        Returns:
            List of processed results
        """
        task_id = f"parallel_scenes_{int(time.time())}"
        self.performance_monitor.start_monitoring(task_id, "Parallel Scene Processing")
        
        results = []
        completed = 0
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_scene = {
                    executor.submit(process_func, scene): scene 
                    for scene in scenes
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_scene):
                    scene = future_to_scene[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        
                        # Report progress
                        if progress_callback:
                            progress = completed / len(scenes)
                            progress_callback(progress, f"Processed scene {completed}/{len(scenes)}")
                        
                        # Add custom metric
                        self.performance_monitor.add_custom_metric(
                            task_id, 
                            f"scene_{completed}_completed", 
                            time.time()
                        )
                        
                    except Exception as e:
                        logger.error(f"Scene processing failed: {e}")
                        results.append(None)  # Placeholder for failed scene
        
        finally:
            metrics = self.performance_monitor.stop_monitoring(task_id)
            if metrics:
                logger.info(f"Parallel processing completed in {metrics.duration:.2f}s")
        
        return results
    
    def optimize_processing_parameters(self, task_complexity: str = "medium") -> Dict[str, Any]:
        """
        Optimize processing parameters based on system capabilities
        
        Args:
            task_complexity: Task complexity level ("low", "medium", "high")
            
        Returns:
            Optimized parameters
        """
        system_info = self.performance_monitor.system_info
        hardware_detector = self.performance_monitor.hardware_detector
        
        # Base parameters
        params = {
            'max_workers': self.max_workers,
            'use_gpu': system_info.gpu_available,
            'encoder': hardware_detector.get_best_encoder(),
            'acceleration_flags': hardware_detector.get_acceleration_flags(),
            'memory_limit_gb': system_info.memory_available / (1024**3) * 0.8,  # Use 80% of available
            'parallel_scenes': True,
            'quality_preset': 'medium'
        }
        
        # Adjust based on complexity
        if task_complexity == "low":
            params.update({
                'max_workers': min(self.max_workers, 4),
                'quality_preset': 'fast',
                'parallel_scenes': True
            })
        elif task_complexity == "high":
            params.update({
                'max_workers': self.max_workers,
                'quality_preset': 'slow',
                'parallel_scenes': system_info.cpu_count >= 8
            })
        
        # Memory-based adjustments
        memory_gb = system_info.memory_total / (1024**3)
        if memory_gb < 8:
            params.update({
                'max_workers': min(params['max_workers'], 2),
                'parallel_scenes': False,
                'quality_preset': 'fast'
            })
        elif memory_gb >= 32:
            params.update({
                'max_workers': min(params['max_workers'] * 2, 16),
                'parallel_scenes': True
            })
        
        return params

class ProgressReporter:
    """Reports progress for long-running tasks"""
    
    def __init__(self):
        self.active_tasks = {}
        self.callbacks = {}
        self.lock = threading.Lock()
    
    def start_task(self, task_id: str, task_name: str, total_steps: int = 100):
        """Start tracking progress for a task"""
        with self.lock:
            self.active_tasks[task_id] = {
                'name': task_name,
                'total_steps': total_steps,
                'current_step': 0,
                'progress': 0.0,
                'stage': 'Starting',
                'message': f'Starting {task_name}',
                'start_time': time.time(),
                'last_update': time.time()
            }
    
    def update_progress(self, 
                       task_id: str, 
                       progress: float, 
                       stage: str = None, 
                       message: str = None):
        """Update task progress"""
        with self.lock:
            if task_id not in self.active_tasks:
                return
            
            task = self.active_tasks[task_id]
            task['progress'] = max(0.0, min(1.0, progress))
            task['current_step'] = int(progress * task['total_steps'])
            task['last_update'] = time.time()
            
            if stage:
                task['stage'] = stage
            if message:
                task['message'] = message
            
            # Calculate estimated remaining time
            elapsed = task['last_update'] - task['start_time']
            if progress > 0:
                estimated_total = elapsed / progress
                estimated_remaining = estimated_total - elapsed
                task['estimated_remaining'] = max(0, estimated_remaining)
            
            # Call registered callbacks
            if task_id in self.callbacks:
                update = ProgressUpdate(
                    task_id=task_id,
                    task_name=task['name'],
                    progress=progress,
                    stage=task['stage'],
                    message=task['message'],
                    timestamp=task['last_update'],
                    estimated_remaining=task.get('estimated_remaining')
                )
                
                for callback in self.callbacks[task_id]:
                    try:
                        callback(update)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")
    
    def finish_task(self, task_id: str, success: bool = True):
        """Mark task as finished"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task['progress'] = 1.0
                task['stage'] = 'Completed' if success else 'Failed'
                task['message'] = f"Task {'completed' if success else 'failed'}"
                
                # Final callback
                if task_id in self.callbacks:
                    update = ProgressUpdate(
                        task_id=task_id,
                        task_name=task['name'],
                        progress=1.0,
                        stage=task['stage'],
                        message=task['message'],
                        timestamp=time.time(),
                        estimated_remaining=0.0
                    )
                    
                    for callback in self.callbacks[task_id]:
                        try:
                            callback(update)
                        except Exception as e:
                            logger.warning(f"Final progress callback failed: {e}")
                
                # Clean up
                del self.active_tasks[task_id]
                if task_id in self.callbacks:
                    del self.callbacks[task_id]
    
    def register_callback(self, task_id: str, callback: Callable[[ProgressUpdate], None]):
        """Register progress callback for a task"""
        with self.lock:
            if task_id not in self.callbacks:
                self.callbacks[task_id] = []
            self.callbacks[task_id].append(callback)
    
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a task"""
        with self.lock:
            return self.active_tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get progress for all active tasks"""
        with self.lock:
            return self.active_tasks.copy()

@contextmanager
def monitor_performance(task_name: str, monitor: PerformanceMonitor = None):
    """Context manager for performance monitoring"""
    if monitor is None:
        monitor = PerformanceMonitor()
    
    task_id = f"{task_name}_{int(time.time())}"
    metrics = monitor.start_monitoring(task_id, task_name)
    
    try:
        yield metrics
    finally:
        final_metrics = monitor.stop_monitoring(task_id)
        if final_metrics:
            logger.info(f"Task '{task_name}' completed in {final_metrics.duration:.2f}s")

# Example usage and testing
if __name__ == "__main__":
    # Test hardware detection
    detector = HardwareAccelerationDetector()
    print(f"GPU Available: {len(detector.gpu_info) > 0}")
    print(f"CUDA Available: {detector.cuda_available}")
    print(f"Best Encoder: {detector.get_best_encoder()}")
    print(f"Acceleration Flags: {detector.get_acceleration_flags()}")
    
    # Test performance monitoring
    monitor = PerformanceMonitor()
    print(f"System Info: {monitor.system_info}")
    
    # Test with context manager
    with monitor_performance("test_task", monitor) as metrics:
        time.sleep(2)  # Simulate work
        print(f"Task running: {metrics.task_name}")
    
    # Test progress reporting
    reporter = ProgressReporter()
    
    def progress_callback(update: ProgressUpdate):
        print(f"Progress: {update.progress:.1%} - {update.message}")
    
    task_id = "test_progress"
    reporter.start_task(task_id, "Test Task")
    reporter.register_callback(task_id, progress_callback)
    
    for i in range(5):
        time.sleep(0.5)
        reporter.update_progress(task_id, i / 4, f"Step {i+1}", f"Processing step {i+1}")
    
    reporter.finish_task(task_id, success=True)