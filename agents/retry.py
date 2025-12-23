"""
Retry mechanisms and exponential backoff for RASO agents.

Provides robust retry logic with exponential backoff, jitter, and circuit breaker patterns
for reliable agent execution in distributed environments.
"""

import asyncio
import random
from typing import Any, Callable, Optional, Type, Union, List
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum

from backend.models import AgentError, ErrorSeverity


class RetryStrategy(str, Enum):
    """Retry strategy options."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    FIBONACCI = "fibonacci"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        jitter: bool = True,
        backoff_multiplier: float = 2.0,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        non_retryable_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            strategy: Retry strategy to use
            jitter: Whether to add random jitter to delays
            backoff_multiplier: Multiplier for exponential backoff
            retryable_exceptions: Exceptions that should trigger retries
            non_retryable_exceptions: Exceptions that should not be retried
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.jitter = jitter
        self.backoff_multiplier = backoff_multiplier
        self.retryable_exceptions = retryable_exceptions or [Exception]
        self.non_retryable_exceptions = non_retryable_exceptions or [
            ValueError, TypeError, AttributeError, KeyError
        ]
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt.
        
        Args:
            attempt: Attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.backoff_multiplier ** attempt)
        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self.base_delay * self._fibonacci(attempt + 1)
        else:
            delay = self.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0.0, delay)
    
    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should trigger a retry.
        
        Args:
            exception: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        # Check attempt limit
        if attempt >= self.max_attempts:
            return False
        
        # Check non-retryable exceptions first
        for exc_type in self.non_retryable_exceptions:
            if isinstance(exception, exc_type):
                return False
        
        # Check retryable exceptions
        for exc_type in self.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        return False


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying half-open state
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to a function."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset."""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful function call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self) -> None:
        """Handle failed function call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    jitter: bool = True,
    backoff_multiplier: float = 2.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    non_retryable_exceptions: Optional[List[Type[Exception]]] = None,
):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        strategy: Retry strategy to use
        jitter: Whether to add random jitter to delays
        backoff_multiplier: Multiplier for exponential backoff
        retryable_exceptions: Exceptions that should trigger retries
        non_retryable_exceptions: Exceptions that should not be retried
        
    Returns:
        Decorated function with retry logic
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        strategy=strategy,
        jitter=jitter,
        backoff_multiplier=backoff_multiplier,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not config.should_retry(e, attempt):
                        raise e
                    
                    if attempt < config.max_attempts:
                        delay = config.calculate_delay(attempt)
                        await asyncio.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not config.should_retry(e, attempt):
                        raise e
                    
                    if attempt < config.max_attempts:
                        delay = config.calculate_delay(attempt)
                        import time
                        time.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


async def retry_with_config(func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
    """
    Execute function with retry logic using provided configuration.
    
    Args:
        func: Function to execute
        config: Retry configuration
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Exception: If all retries fail
    """
    last_exception = None
    
    for attempt in range(config.max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if not config.should_retry(e, attempt):
                raise e
            
            if attempt < config.max_attempts:
                delay = config.calculate_delay(attempt)
                await asyncio.sleep(delay)
    
    # If we get here, all retries failed
    raise last_exception


class RetryableOperation:
    """Context manager for retryable operations with detailed logging."""
    
    def __init__(self, operation_name: str, config: RetryConfig, logger=None):
        """
        Initialize retryable operation.
        
        Args:
            operation_name: Name of the operation for logging
            config: Retry configuration
            logger: Optional logger instance
        """
        self.operation_name = operation_name
        self.config = config
        self.logger = logger
        self.attempt = 0
        self.start_time: Optional[datetime] = None
    
    async def __aenter__(self):
        """Enter async context manager."""
        self.start_time = datetime.now()
        if self.logger:
            self.logger.info(f"Starting retryable operation: {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if self.logger:
                if exc_type is None:
                    self.logger.info(
                        f"Operation {self.operation_name} completed successfully "
                        f"after {self.attempt + 1} attempts in {duration:.2f}s"
                    )
                else:
                    self.logger.error(
                        f"Operation {self.operation_name} failed after "
                        f"{self.attempt + 1} attempts in {duration:.2f}s: {exc_val}"
                    )
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts + 1):
            self.attempt = attempt
            
            try:
                if self.logger and attempt > 0:
                    self.logger.info(
                        f"Retrying {self.operation_name} (attempt {attempt + 1}/{self.config.max_attempts + 1})"
                    )
                
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if self.logger:
                    self.logger.warning(
                        f"Attempt {attempt + 1} of {self.operation_name} failed: {str(e)}"
                    )
                
                if not self.config.should_retry(e, attempt):
                    if self.logger:
                        self.logger.error(f"Not retrying {self.operation_name}: {str(e)}")
                    raise e
                
                if attempt < self.config.max_attempts:
                    delay = self.config.calculate_delay(attempt)
                    if self.logger:
                        self.logger.info(f"Waiting {delay:.2f}s before retry")
                    await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        if self.logger:
            self.logger.error(f"All retries exhausted for {self.operation_name}")
        raise last_exception