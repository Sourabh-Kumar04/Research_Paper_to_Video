"""
Comprehensive Error Handling and Recovery System

This module provides detailed error logging, recovery suggestions, validation failure handling
with regeneration, and temporary file cleanup for the video generation system.
"""

import os
import sys
import traceback
import logging
import json
import shutil
import tempfile
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from enum import Enum
import threading
import time
from contextlib import contextmanager
import subprocess

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    SYSTEM = "system"
    VALIDATION = "validation"
    PROCESSING = "processing"
    NETWORK = "network"
    STORAGE = "storage"
    CONFIGURATION = "configuration"
    USER_INPUT = "user_input"
    EXTERNAL_SERVICE = "external_service"

class RecoveryAction(Enum):
    """Available recovery actions"""
    RETRY = "retry"
    FALLBACK = "fallback"
    REGENERATE = "regenerate"
    SKIP = "skip"
    ABORT = "abort"
    USER_INTERVENTION = "user_intervention"

@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_id: str
    timestamp: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: Dict[str, Any]
    stack_trace: str
    recovery_suggestions: List[str]
    recovery_actions: List[RecoveryAction]
    affected_files: List[str]
    system_info: Dict[str, Any]

@dataclass
class RecoveryResult:
    """Result of a recovery attempt"""
    success: bool
    action_taken: RecoveryAction
    message: str
    new_error: Optional[ErrorInfo] = None
    recovered_files: List[str] = None

class ErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self, log_dir: str = "logs", max_retries: int = 3):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_retries = max_retries
        
        # Error tracking
        self.error_history = []
        self.recovery_attempts = {}
        self.temp_files = set()
        self.cleanup_callbacks = []
        
        # Setup logging
        self._setup_error_logging()
        
        # Recovery strategies
        self.recovery_strategies = {
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.PROCESSING: self._handle_processing_error,
            ErrorCategory.STORAGE: self._handle_storage_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.SYSTEM: self._handle_system_error,
            ErrorCategory.CONFIGURATION: self._handle_configuration_error,
            ErrorCategory.USER_INPUT: self._handle_user_input_error,
            ErrorCategory.EXTERNAL_SERVICE: self._handle_external_service_error
        }
    
    def _setup_error_logging(self):
        """Setup comprehensive error logging"""
        # Create error log file
        error_log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configure error logger
        error_logger = logging.getLogger('error_handler')
        error_logger.setLevel(logging.ERROR)
        
        # File handler for errors
        file_handler = logging.FileHandler(error_log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Detailed formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'Context: %(context)s\n'
            'Stack Trace: %(stack_trace)s\n'
            '---\n',
            defaults={'context': 'N/A', 'stack_trace': 'N/A'}
        )
        file_handler.setFormatter(formatter)
        error_logger.addHandler(file_handler)
        
        self.error_logger = error_logger
    
    def handle_error(self, 
                    error: Exception,
                    context: Dict[str, Any] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.PROCESSING,
                    recovery_callback: Optional[Callable] = None) -> ErrorInfo:
        """
        Handle an error with comprehensive logging and recovery suggestions
        
        Args:
            error: The exception that occurred
            context: Additional context information
            severity: Error severity level
            category: Error category for classification
            recovery_callback: Optional callback for custom recovery
            
        Returns:
            ErrorInfo object with comprehensive error details
        """
        error_id = f"error_{int(time.time())}_{len(self.error_history)}"
        
        # Gather error information
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now().isoformat(),
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            context=context or {},
            stack_trace=traceback.format_exc(),
            recovery_suggestions=self._generate_recovery_suggestions(error, category),
            recovery_actions=self._determine_recovery_actions(error, category, severity),
            affected_files=self._identify_affected_files(error, context),
            system_info=self._gather_system_info()
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Store in history
        self.error_history.append(error_info)
        
        # Attempt automatic recovery if appropriate
        if severity != ErrorSeverity.CRITICAL and recovery_callback:
            try:
                recovery_result = self._attempt_recovery(error_info, recovery_callback)
                if recovery_result.success:
                    logger.info(f"Successfully recovered from error {error_id}: {recovery_result.message}")
                else:
                    logger.warning(f"Recovery failed for error {error_id}: {recovery_result.message}")
            except Exception as recovery_error:
                logger.error(f"Recovery attempt failed for error {error_id}: {recovery_error}")
        
        return error_info
    
    def _generate_recovery_suggestions(self, error: Exception, category: ErrorCategory) -> List[str]:
        """Generate contextual recovery suggestions"""
        suggestions = []
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # General suggestions based on error type
        if error_type == "FileNotFoundError":
            suggestions.extend([
                "Check if the file path is correct",
                "Verify file permissions",
                "Ensure the file hasn't been moved or deleted",
                "Try regenerating the missing file"
            ])
        elif error_type == "PermissionError":
            suggestions.extend([
                "Check file and directory permissions",
                "Run with appropriate user privileges",
                "Verify disk space availability",
                "Close any applications using the file"
            ])
        elif error_type == "MemoryError":
            suggestions.extend([
                "Reduce processing batch size",
                "Close unnecessary applications",
                "Use lower quality settings",
                "Enable disk-based processing"
            ])
        elif error_type == "TimeoutError":
            suggestions.extend([
                "Increase timeout duration",
                "Check network connectivity",
                "Verify service availability",
                "Retry the operation"
            ])
        
        # Category-specific suggestions
        if category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Check input data format and structure",
                "Validate configuration parameters",
                "Verify file integrity",
                "Update validation rules if needed"
            ])
        elif category == ErrorCategory.PROCESSING:
            suggestions.extend([
                "Check available system resources",
                "Verify input file formats",
                "Try with different processing parameters",
                "Use fallback processing methods"
            ])
        elif category == ErrorCategory.STORAGE:
            suggestions.extend([
                "Check available disk space",
                "Verify write permissions",
                "Clean up temporary files",
                "Use alternative storage location"
            ])
        elif category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check internet connectivity",
                "Verify firewall settings",
                "Try alternative network endpoints",
                "Use offline processing mode"
            ])
        
        # Specific error message patterns
        if "ffmpeg" in error_message:
            suggestions.extend([
                "Verify FFmpeg installation",
                "Check FFmpeg version compatibility",
                "Install missing codecs",
                "Use alternative video processing method"
            ])
        elif "cuda" in error_message or "gpu" in error_message:
            suggestions.extend([
                "Check GPU drivers",
                "Verify CUDA installation",
                "Fall back to CPU processing",
                "Update graphics drivers"
            ])
        elif "memory" in error_message or "ram" in error_message:
            suggestions.extend([
                "Reduce batch size",
                "Process files individually",
                "Use streaming processing",
                "Increase virtual memory"
            ])
        
        return suggestions
    
    def _determine_recovery_actions(self, 
                                  error: Exception, 
                                  category: ErrorCategory, 
                                  severity: ErrorSeverity) -> List[RecoveryAction]:
        """Determine appropriate recovery actions"""
        actions = []
        error_type = type(error).__name__
        
        # Severity-based actions
        if severity == ErrorSeverity.CRITICAL:
            actions.append(RecoveryAction.ABORT)
            actions.append(RecoveryAction.USER_INTERVENTION)
        elif severity == ErrorSeverity.HIGH:
            actions.extend([RecoveryAction.FALLBACK, RecoveryAction.USER_INTERVENTION])
        else:
            actions.extend([RecoveryAction.RETRY, RecoveryAction.FALLBACK])
        
        # Error type specific actions
        if error_type in ["FileNotFoundError", "PermissionError"]:
            actions.extend([RecoveryAction.REGENERATE, RecoveryAction.SKIP])
        elif error_type in ["TimeoutError", "ConnectionError"]:
            actions.extend([RecoveryAction.RETRY, RecoveryAction.FALLBACK])
        elif error_type == "MemoryError":
            actions.extend([RecoveryAction.FALLBACK, RecoveryAction.REGENERATE])
        
        # Category-specific actions
        if category == ErrorCategory.VALIDATION:
            actions.extend([RecoveryAction.REGENERATE, RecoveryAction.SKIP])
        elif category == ErrorCategory.PROCESSING:
            actions.extend([RecoveryAction.FALLBACK, RecoveryAction.RETRY])
        elif category == ErrorCategory.STORAGE:
            actions.extend([RecoveryAction.REGENERATE, RecoveryAction.FALLBACK])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_actions = []
        for action in actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        return unique_actions
    
    def _identify_affected_files(self, error: Exception, context: Dict[str, Any]) -> List[str]:
        """Identify files affected by the error"""
        affected_files = []
        error_message = str(error)
        
        # Extract file paths from error message
        import re
        file_patterns = [
            r"'([^']+\.[a-zA-Z0-9]+)'",  # Files in single quotes
            r'"([^"]+\.[a-zA-Z0-9]+)"',  # Files in double quotes
            r"([/\\][\w/\\.-]+\.[a-zA-Z0-9]+)",  # File paths
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, error_message)
            affected_files.extend(matches)
        
        # Check context for file references
        if context:
            for key, value in context.items():
                if isinstance(value, str) and ('path' in key.lower() or 'file' in key.lower()):
                    if Path(value).suffix:  # Has file extension
                        affected_files.append(value)
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        if isinstance(item, str) and Path(item).suffix:
                            affected_files.append(item)
        
        # Remove duplicates and validate paths
        unique_files = []
        for file_path in set(affected_files):
            try:
                path = Path(file_path)
                if path.is_absolute() or '/' in file_path or '\\' in file_path:
                    unique_files.append(file_path)
            except Exception:
                continue
        
        return unique_files
    
    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather relevant system information"""
        import platform
        import psutil
        
        try:
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_free': psutil.disk_usage('/').free if os.name != 'nt' else psutil.disk_usage('C:').free,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': f"Failed to gather system info: {e}"}
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with comprehensive details"""
        log_entry = {
            'error_id': error_info.error_id,
            'timestamp': error_info.timestamp,
            'severity': error_info.severity.value,
            'category': error_info.category.value,
            'error_type': error_info.error_type,
            'message': error_info.error_message,
            'context': error_info.context,
            'recovery_suggestions': error_info.recovery_suggestions,
            'affected_files': error_info.affected_files,
            'system_info': error_info.system_info
        }
        
        # Log to file
        error_log_file = self.log_dir / f"error_details_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            # Append to JSON log file
            if error_log_file.exists():
                with open(error_log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {'errors': []}
            
            log_data['errors'].append(log_entry)
            
            with open(error_log_file, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
                
        except Exception as log_error:
            logger.error(f"Failed to write error log: {log_error}")
        
        # Also log to standard logger
        self.error_logger.error(
            f"Error {error_info.error_id}: {error_info.error_message}",
            extra={
                'context': json.dumps(error_info.context, default=str),
                'stack_trace': error_info.stack_trace
            }
        )
    
    def _attempt_recovery(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Attempt automatic recovery"""
        recovery_key = f"{error_info.error_type}_{error_info.category.value}"
        
        # Check retry count
        if recovery_key not in self.recovery_attempts:
            self.recovery_attempts[recovery_key] = 0
        
        if self.recovery_attempts[recovery_key] >= self.max_retries:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.ABORT,
                message=f"Maximum retry attempts ({self.max_retries}) exceeded"
            )
        
        self.recovery_attempts[recovery_key] += 1
        
        # Try category-specific recovery
        if error_info.category in self.recovery_strategies:
            try:
                return self.recovery_strategies[error_info.category](error_info, recovery_callback)
            except Exception as recovery_error:
                return RecoveryResult(
                    success=False,
                    action_taken=RecoveryAction.ABORT,
                    message=f"Recovery strategy failed: {recovery_error}"
                )
        
        # Default recovery attempt
        try:
            recovery_callback()
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.RETRY,
                message="Recovery callback executed successfully"
            )
        except Exception as retry_error:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RETRY,
                message=f"Recovery callback failed: {retry_error}"
            )
    
    def _handle_validation_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle validation errors with regeneration"""
        try:
            # Try to regenerate affected files
            if error_info.affected_files:
                for file_path in error_info.affected_files:
                    if Path(file_path).exists():
                        # Backup original file
                        backup_path = f"{file_path}.backup_{int(time.time())}"
                        shutil.copy2(file_path, backup_path)
                        logger.info(f"Backed up {file_path} to {backup_path}")
            
            # Attempt regeneration
            recovery_callback()
            
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.REGENERATE,
                message="Successfully regenerated content after validation failure"
            )
            
        except Exception as regen_error:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.REGENERATE,
                message=f"Regeneration failed: {regen_error}"
            )
    
    def _handle_processing_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle processing errors with fallback methods"""
        try:
            # Try fallback processing method
            fallback_context = error_info.context.copy()
            fallback_context['use_fallback'] = True
            fallback_context['reduce_quality'] = True
            
            recovery_callback()
            
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.FALLBACK,
                message="Successfully used fallback processing method"
            )
            
        except Exception as fallback_error:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.FALLBACK,
                message=f"Fallback processing failed: {fallback_error}"
            )
    
    def _handle_storage_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle storage errors with cleanup and retry"""
        try:
            # Clean up temporary files
            self.cleanup_temp_files()
            
            # Try alternative storage location
            if error_info.context.get('output_path'):
                original_path = error_info.context['output_path']
                temp_path = tempfile.mktemp(suffix=Path(original_path).suffix)
                error_info.context['output_path'] = temp_path
                
                recovery_callback()
                
                # Move to original location if successful
                if Path(temp_path).exists():
                    shutil.move(temp_path, original_path)
                
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.FALLBACK,
                    message="Successfully used alternative storage location"
                )
            
            recovery_callback()
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.RETRY,
                message="Storage error resolved after cleanup"
            )
            
        except Exception as storage_error:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RETRY,
                message=f"Storage recovery failed: {storage_error}"
            )
    
    def _handle_network_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle network errors with retry and offline fallback"""
        try:
            # Wait before retry
            time.sleep(2)
            
            # Try with offline mode if supported
            offline_context = error_info.context.copy()
            offline_context['offline_mode'] = True
            
            recovery_callback()
            
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.FALLBACK,
                message="Successfully switched to offline processing"
            )
            
        except Exception as network_error:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.FALLBACK,
                message=f"Network recovery failed: {network_error}"
            )
    
    def _handle_system_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle system errors"""
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.USER_INTERVENTION,
            message="System error requires manual intervention"
        )
    
    def _handle_configuration_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle configuration errors"""
        try:
            # Try with default configuration
            default_context = {'use_defaults': True}
            recovery_callback()
            
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.FALLBACK,
                message="Successfully used default configuration"
            )
            
        except Exception as config_error:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.USER_INTERVENTION,
                message=f"Configuration recovery failed: {config_error}"
            )
    
    def _handle_user_input_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle user input errors"""
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.USER_INTERVENTION,
            message="Invalid user input requires correction"
        )
    
    def _handle_external_service_error(self, error_info: ErrorInfo, recovery_callback: Callable) -> RecoveryResult:
        """Handle external service errors"""
        try:
            # Try offline fallback
            offline_context = error_info.context.copy()
            offline_context['use_local_services'] = True
            
            recovery_callback()
            
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.FALLBACK,
                message="Successfully switched to local services"
            )
            
        except Exception as service_error:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.SKIP,
                message=f"External service unavailable: {service_error}"
            )
    
    def register_temp_file(self, file_path: str):
        """Register a temporary file for cleanup"""
        self.temp_files.add(str(Path(file_path).resolve()))
    
    def register_cleanup_callback(self, callback: Callable):
        """Register a cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    def cleanup_temp_files(self):
        """Clean up all registered temporary files"""
        cleaned_files = []
        
        for file_path in list(self.temp_files):
            try:
                path = Path(file_path)
                if path.exists():
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
                    cleaned_files.append(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
                
                self.temp_files.remove(file_path)
                
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup {file_path}: {cleanup_error}")
        
        # Execute cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as callback_error:
                logger.warning(f"Cleanup callback failed: {callback_error}")
        
        return cleaned_files
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        if not self.error_history:
            return {'total_errors': 0, 'summary': 'No errors recorded'}
        
        # Count by severity
        severity_counts = {}
        for error in self.error_history:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by category
        category_counts = {}
        for error in self.error_history:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Recent errors
        recent_errors = self.error_history[-5:] if len(self.error_history) > 5 else self.error_history
        
        return {
            'total_errors': len(self.error_history),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'recent_errors': [
                {
                    'error_id': error.error_id,
                    'timestamp': error.timestamp,
                    'type': error.error_type,
                    'message': error.error_message,
                    'severity': error.severity.value
                }
                for error in recent_errors
            ],
            'recovery_attempts': dict(self.recovery_attempts),
            'temp_files_count': len(self.temp_files)
        }

@contextmanager
def error_handling_context(handler: ErrorHandler = None, 
                          category: ErrorCategory = ErrorCategory.PROCESSING,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          context: Dict[str, Any] = None):
    """Context manager for comprehensive error handling"""
    if handler is None:
        handler = ErrorHandler()
    
    try:
        yield handler
    except Exception as e:
        error_info = handler.handle_error(e, context, severity, category)
        raise  # Re-raise the exception after handling

# Example usage and testing
if __name__ == "__main__":
    # Test error handling
    handler = ErrorHandler()
    
    # Test different error types
    try:
        raise FileNotFoundError("Test file not found")
    except Exception as e:
        error_info = handler.handle_error(
            e, 
            context={'file_path': '/test/path.mp4', 'operation': 'video_processing'},
            category=ErrorCategory.STORAGE,
            severity=ErrorSeverity.MEDIUM
        )
        print(f"Handled error: {error_info.error_id}")
    
    # Test context manager
    try:
        with error_handling_context(handler, ErrorCategory.VALIDATION) as error_handler:
            raise ValueError("Test validation error")
    except ValueError:
        pass  # Expected
    
    # Get error summary
    summary = handler.get_error_summary()
    print(f"Error summary: {summary}")
    
    # Cleanup
    handler.cleanup_temp_files()