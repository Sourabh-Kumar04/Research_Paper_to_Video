"""
Base agent framework for the RASO platform.

Provides abstract base class and common functionality for all RASO agents,
including error handling, logging, and state management.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from datetime import datetime

from backend.models import RASOMasterState, AgentError, AgentType, ErrorSeverity
from backend.config import get_config


class AgentExecutionError(Exception):
    """Exception raised during agent execution."""
    
    def __init__(self, message: str, error_code: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity


class BaseAgent(ABC):
    """Abstract base class for all RASO agents."""
    
    def __init__(self, agent_type: AgentType):
        """Initialize the base agent."""
        self.agent_type = agent_type
        self.config = get_config()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up agent-specific logger."""
        logger = logging.getLogger(f"raso.agents.{self.agent_type.value}")
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            # Create console handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.agent_type.value} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description and purpose."""
        pass
    
    @abstractmethod
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Execute the agent's main functionality.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
            
        Raises:
            AgentExecutionError: If execution fails
        """
        pass
    
    def validate_input(self, state: RASOMasterState) -> None:
        """
        Validate input state before execution.
        
        Args:
            state: State to validate
            
        Raises:
            AgentExecutionError: If validation fails
        """
        if not isinstance(state, RASOMasterState):
            raise AgentExecutionError(
                "Invalid state type provided",
                "INVALID_STATE_TYPE",
                ErrorSeverity.CRITICAL
            )
        
        # Check for critical errors that should abort processing
        if state.should_abort():
            raise AgentExecutionError(
                "Processing aborted due to critical errors",
                "PROCESSING_ABORTED",
                ErrorSeverity.CRITICAL
            )
    
    def handle_error(self, error: Exception, state: RASOMasterState, 
                    error_code: Optional[str] = None) -> RASOMasterState:
        """
        Handle errors during agent execution.
        
        Args:
            error: The exception that occurred
            state: Current workflow state
            error_code: Optional error code
            
        Returns:
            Updated state with error information
        """
        # Determine error details
        if isinstance(error, AgentExecutionError):
            message = error.message
            code = error.error_code
            severity = error.severity
        else:
            message = str(error)
            code = error_code or "UNKNOWN_ERROR"
            severity = ErrorSeverity.ERROR
        
        # Log the error
        self.logger.error(f"Agent execution failed: {message}", exc_info=True)
        
        # Add error to state
        agent_error = state.add_error(
            agent_type=self.agent_type,
            error_code=code,
            message=message,
            severity=severity,
            details={
                "agent_name": self.name,
                "timestamp": datetime.now().isoformat(),
                "exception_type": type(error).__name__,
            }
        )
        
        return state
    
    def log_progress(self, message: str, state: RASOMasterState, level: str = "info") -> None:
        """
        Log progress information.
        
        Args:
            message: Progress message
            state: Current workflow state
            level: Log level (debug, info, warning, error)
        """
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"Job {state.job_id}: {message}")
    
    async def safe_execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Safely execute the agent with error handling.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        try:
            # Update current agent in state
            state.current_agent = self.agent_type
            state.update_timestamp()
            
            # Log execution start
            self.log_progress(f"Starting {self.name} execution", state)
            
            # Validate input
            self.validate_input(state)
            
            # Execute agent logic
            updated_state = await self.execute(state)
            
            # Log successful completion
            self.log_progress(f"Completed {self.name} execution", state)
            
            return updated_state
            
        except Exception as error:
            # Handle and log error
            error_state = self.handle_error(error, state)
            
            # Re-raise critical errors
            if isinstance(error, AgentExecutionError) and error.severity == ErrorSeverity.CRITICAL:
                raise
            
            return error_state
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay using exponential backoff.
        
        Args:
            attempt: Retry attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        base_delay = self.config.system.retry_delay_seconds
        max_delay = 60.0  # Maximum 1 minute delay
        
        delay = min(base_delay * (2 ** attempt), max_delay)
        return delay
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if execution should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        # Don't retry critical errors
        if isinstance(error, AgentExecutionError) and error.severity == ErrorSeverity.CRITICAL:
            return False
        
        # Check retry limit
        if attempt >= self.config.system.retry_attempts:
            return False
        
        # Don't retry validation errors
        if isinstance(error, (ValueError, TypeError)):
            return False
        
        return True
    
    def create_execution_context(self, state: RASOMasterState) -> Dict[str, Any]:
        """
        Create execution context for the agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Execution context dictionary
        """
        return {
            "agent_type": self.agent_type.value,
            "agent_name": self.name,
            "job_id": state.job_id,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "retry_attempts": self.config.system.retry_attempts,
                "timeout_minutes": self.config.system.job_timeout_minutes,
            }
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} ({self.agent_type.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"<{self.__class__.__name__}(type={self.agent_type.value}, name='{self.name}')>"


class AgentRegistry:
    """Registry for managing RASO agents."""
    
    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[AgentType, Type[BaseAgent]] = {}
        self._instances: Dict[AgentType, BaseAgent] = {}
    
    def register(self, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class.
        
        Args:
            agent_class: Agent class to register
        """
        # Get agent type from class
        if not hasattr(agent_class, '_agent_type'):
            raise ValueError(f"Agent class {agent_class.__name__} must define _agent_type")
        
        agent_type = agent_class._agent_type
        self._agents[agent_type] = agent_class
    
    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """
        Get an agent instance by type.
        
        Args:
            agent_type: Type of agent to get
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent type is not registered
        """
        if agent_type not in self._agents:
            raise ValueError(f"Agent type {agent_type} is not registered")
        
        # Create instance if not cached
        if agent_type not in self._instances:
            agent_class = self._agents[agent_type]
            self._instances[agent_type] = agent_class(agent_type)
        
        return self._instances[agent_type]
    
    def list_agents(self) -> Dict[AgentType, str]:
        """
        List all registered agents.
        
        Returns:
            Dictionary mapping agent types to names
        """
        result = {}
        for agent_type, agent_class in self._agents.items():
            # Create temporary instance to get name
            temp_instance = agent_class(agent_type)
            result[agent_type] = temp_instance.name
        
        return result
    
    def is_registered(self, agent_type: AgentType) -> bool:
        """
        Check if an agent type is registered.
        
        Args:
            agent_type: Agent type to check
            
        Returns:
            True if registered, False otherwise
        """
        return agent_type in self._agents


# Global agent registry instance
agent_registry = AgentRegistry()


def register_agent(agent_type: AgentType):
    """
    Decorator for registering agent classes.
    
    Args:
        agent_type: Type of agent to register
        
    Returns:
        Decorator function
    """
    def decorator(agent_class: Type[BaseAgent]):
        agent_class._agent_type = agent_type
        agent_registry.register(agent_class)
        return agent_class
    
    return decorator