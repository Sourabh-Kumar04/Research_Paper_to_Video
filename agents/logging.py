"""
Comprehensive logging and debugging capabilities for RASO agents.

Provides structured logging, performance monitoring, and debugging tools
for agent execution and workflow orchestration.
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from contextlib import contextmanager
from functools import wraps

from backend.config import get_config
from backend.models import RASOMasterState, AgentType, WorkflowStatus


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "getMessage", "exc_info", "exc_text", "stack_info"]:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class AgentLogger:
    """Enhanced logger for RASO agents with context and performance tracking."""
    
    def __init__(self, agent_type: AgentType, job_id: Optional[str] = None):
        """
        Initialize agent logger.
        
        Args:
            agent_type: Type of agent
            job_id: Optional job identifier for context
        """
        self.agent_type = agent_type
        self.job_id = job_id
        self.config = get_config()
        
        # Create logger
        self.logger = logging.getLogger(f"raso.agents.{agent_type.value}")
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        # Set up handlers if not already configured
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Performance tracking
        self._operation_stack: List[Dict[str, Any]] = []
    
    def _setup_handlers(self) -> None:
        """Set up log handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        if self.config.env == "production":
            # Use structured logging in production
            console_handler.setFormatter(StructuredFormatter())
        else:
            # Use human-readable format in development
            formatter = logging.Formatter(
                f'%(asctime)s - {self.agent_type.value} - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # File handler if log path is configured
        if self.config.log_path:
            log_file = self.config.log_path / f"{self.agent_type.value}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get logging context."""
        context = {
            "agent_type": self.agent_type.value,
        }
        
        if self.job_id:
            context["job_id"] = self.job_id
        
        if self._operation_stack:
            context["operation"] = self._operation_stack[-1]["name"]
            context["operation_id"] = self._operation_stack[-1]["id"]
        
        return context
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, extra={**self._get_context(), **kwargs})
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, extra={**self._get_context(), **kwargs})
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, extra={**self._get_context(), **kwargs})
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message."""
        extra = {**self._get_context(), **kwargs}
        if exception:
            self.logger.error(message, exc_info=exception, extra=extra)
        else:
            self.logger.error(message, extra=extra)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message."""
        extra = {**self._get_context(), **kwargs}
        if exception:
            self.logger.critical(message, exc_info=exception, extra=extra)
        else:
            self.logger.critical(message, extra=extra)
    
    @contextmanager
    def operation(self, operation_name: str, **metadata):
        """
        Context manager for tracking operations with performance metrics.
        
        Args:
            operation_name: Name of the operation
            **metadata: Additional metadata to log
        """
        operation_id = f"{operation_name}_{datetime.now().timestamp()}"
        operation_data = {
            "id": operation_id,
            "name": operation_name,
            "start_time": datetime.now(),
            "metadata": metadata,
        }
        
        self._operation_stack.append(operation_data)
        
        try:
            self.info(f"Starting operation: {operation_name}", **metadata)
            yield operation_id
            
        except Exception as e:
            operation_data["error"] = str(e)
            operation_data["success"] = False
            self.error(f"Operation failed: {operation_name}", exception=e, **metadata)
            raise
            
        else:
            operation_data["success"] = True
            self.info(f"Operation completed: {operation_name}", **metadata)
            
        finally:
            # Calculate duration and log performance
            end_time = datetime.now()
            duration = (end_time - operation_data["start_time"]).total_seconds()
            operation_data["end_time"] = end_time
            operation_data["duration_seconds"] = duration
            
            self.info(
                f"Operation performance: {operation_name}",
                duration_seconds=duration,
                success=operation_data.get("success", False),
                **metadata
            )
            
            self._operation_stack.pop()
    
    def log_state_transition(self, old_status: WorkflowStatus, new_status: WorkflowStatus, 
                           state: RASOMasterState) -> None:
        """
        Log workflow state transition.
        
        Args:
            old_status: Previous workflow status
            new_status: New workflow status
            state: Current workflow state
        """
        self.info(
            f"State transition: {old_status.value} -> {new_status.value}",
            old_status=old_status.value,
            new_status=new_status.value,
            progress=state.progress.overall_progress,
            job_id=state.job_id,
        )
    
    def log_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Log performance metrics.
        
        Args:
            metrics: Performance metrics dictionary
        """
        self.info("Performance metrics", **metrics)
    
    def log_agent_execution(self, state: RASOMasterState, success: bool, 
                          duration: float, **kwargs) -> None:
        """
        Log agent execution summary.
        
        Args:
            state: Workflow state
            success: Whether execution was successful
            duration: Execution duration in seconds
            **kwargs: Additional logging data
        """
        self.info(
            f"Agent execution {'completed' if success else 'failed'}",
            success=success,
            duration_seconds=duration,
            job_id=state.job_id,
            progress=state.progress.overall_progress,
            error_count=len(state.errors),
            **kwargs
        )


def log_execution_time(logger: Optional[AgentLogger] = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Optional logger instance
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                if isinstance(func_logger, AgentLogger):
                    func_logger.debug(
                        f"Function {func.__name__} completed",
                        function=func.__name__,
                        duration_seconds=duration,
                        success=True,
                    )
                else:
                    func_logger.debug(f"Function {func.__name__} completed in {duration:.3f}s")
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                if isinstance(func_logger, AgentLogger):
                    func_logger.error(
                        f"Function {func.__name__} failed",
                        function=func.__name__,
                        duration_seconds=duration,
                        success=False,
                        exception=e,
                    )
                else:
                    func_logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {e}")
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                if isinstance(func_logger, AgentLogger):
                    func_logger.debug(
                        f"Function {func.__name__} completed",
                        function=func.__name__,
                        duration_seconds=duration,
                        success=True,
                    )
                else:
                    func_logger.debug(f"Function {func.__name__} completed in {duration:.3f}s")
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                if isinstance(func_logger, AgentLogger):
                    func_logger.error(
                        f"Function {func.__name__} failed",
                        function=func.__name__,
                        duration_seconds=duration,
                        success=False,
                        exception=e,
                    )
                else:
                    func_logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {e}")
                
                raise
        
        # Return appropriate wrapper
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class DebugContext:
    """Context manager for debugging agent execution."""
    
    def __init__(self, agent_type: AgentType, operation: str, state: RASOMasterState):
        """
        Initialize debug context.
        
        Args:
            agent_type: Type of agent
            operation: Operation being performed
            state: Current workflow state
        """
        self.agent_type = agent_type
        self.operation = operation
        self.state = state
        self.logger = AgentLogger(agent_type, state.job_id)
        self.start_time: Optional[datetime] = None
        self.debug_data: Dict[str, Any] = {}
    
    def __enter__(self):
        """Enter debug context."""
        self.start_time = datetime.now()
        self.logger.debug(
            f"Starting debug context: {self.operation}",
            operation=self.operation,
            state_status=self.state.progress.current_step.value,
            progress=self.state.progress.overall_progress,
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit debug context."""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            
            if exc_type is None:
                self.logger.debug(
                    f"Debug context completed: {self.operation}",
                    operation=self.operation,
                    duration_seconds=duration,
                    debug_data=self.debug_data,
                )
            else:
                self.logger.error(
                    f"Debug context failed: {self.operation}",
                    operation=self.operation,
                    duration_seconds=duration,
                    debug_data=self.debug_data,
                    exception=exc_val,
                )
    
    def add_debug_data(self, key: str, value: Any) -> None:
        """Add debug data to context."""
        self.debug_data[key] = value
    
    def checkpoint(self, message: str, **data) -> None:
        """Log a debug checkpoint."""
        self.logger.debug(
            f"Debug checkpoint: {message}",
            operation=self.operation,
            checkpoint_data=data,
        )


def setup_logging(config_override: Optional[Dict[str, Any]] = None) -> None:
    """
    Set up global logging configuration.
    
    Args:
        config_override: Optional configuration overrides
    """
    config = get_config()
    
    # Apply overrides
    if config_override:
        for key, value in config_override.items():
            setattr(config, key, value)
    
    # Configure root logger
    root_logger = logging.getLogger("raso")
    root_logger.setLevel(getattr(logging, config.log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    if config.env == "production":
        console_handler.setFormatter(StructuredFormatter())
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    # Add file handler if configured
    if config.log_path:
        config.log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(config.log_path / "raso.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)