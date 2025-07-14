"""
Retry manager with circuit breaker pattern and intelligent backoff strategies.
"""
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True
    exponential_base: float = 2.0


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryableException(Exception):
    """Base exception for retryable errors."""


class NonRetryableException(Exception):
    """Exception for errors that should not be retried."""


class CircuitBreaker:
    """Circuit breaker implementation for handling cascading failures."""
    
    def __init__(self, config: CircuitBreakerConfig):
        """Initialize circuit breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.next_attempt_time: Optional[datetime] = None
        
    def can_execute(self) -> bool:
        """Check if execution is allowed.
        
        Returns:
            True if execution is allowed
        """
        now = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if (self.next_attempt_time and now >= self.next_attempt_time):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record a successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker transitioning to CLOSED")
        else:
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.next_attempt_time = datetime.now() + timedelta(seconds=self.config.recovery_timeout)
            logger.warning("Circuit breaker transitioning to OPEN from HALF_OPEN")
        elif (self.state == CircuitState.CLOSED and 
              self.failure_count >= self.config.failure_threshold):
            self.state = CircuitState.OPEN
            self.next_attempt_time = datetime.now() + timedelta(seconds=self.config.recovery_timeout)
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information.
        
        Returns:
            State information dictionary
        """
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'next_attempt_time': self.next_attempt_time.isoformat() if self.next_attempt_time else None
        }


class RetryManager:
    """Advanced retry manager with multiple strategies and circuit breaker."""
    
    def __init__(self, 
                 retry_config: Optional[RetryConfig] = None,
                 circuit_config: Optional[CircuitBreakerConfig] = None):
        """Initialize retry manager.
        
        Args:
            retry_config: Retry configuration
            circuit_config: Circuit breaker configuration
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_config or CircuitBreakerConfig())
        self.retry_history: List[Dict[str, Any]] = []
        
    def execute_with_retry(self,
                          func: Callable,
                          *args,
                          retry_on: Optional[List[type]] = None,
                          no_retry_on: Optional[List[type]] = None,
                          **kwargs) -> Any:
        """Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            retry_on: Exception types to retry on
            no_retry_on: Exception types to never retry on
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries failed
        """
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN")
        
        retry_on = retry_on or [Exception]
        no_retry_on = no_retry_on or [NonRetryableException]
        
        last_exception = None
        attempt = 0
        
        while attempt < self.retry_config.max_attempts:
            try:
                attempt += 1
                logger.debug(f"Executing {func.__name__} (attempt {attempt}/{self.retry_config.max_attempts})")
                
                result = func(*args, **kwargs)
                
                # Success
                self.circuit_breaker.record_success()
                self._record_retry_success(func.__name__, attempt)
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this exception should not be retried
                if any(isinstance(e, exc_type) for exc_type in no_retry_on):
                    logger.info(f"Non-retryable exception: {type(e).__name__}")
                    self.circuit_breaker.record_failure()
                    self._record_retry_failure(func.__name__, attempt, str(e), retryable=False)
                    raise e
                
                # Check if this exception should be retried
                if not any(isinstance(e, exc_type) for exc_type in retry_on):
                    logger.info(f"Exception not in retry list: {type(e).__name__}")
                    self.circuit_breaker.record_failure()
                    self._record_retry_failure(func.__name__, attempt, str(e), retryable=False)
                    raise e
                
                # This is a retryable exception
                if attempt < self.retry_config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt} failed with {type(e).__name__}: {e}. "
                                 f"Retrying in {delay:.2f}s")
                    
                    self._record_retry_failure(func.__name__, attempt, str(e), retryable=True)
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    self.circuit_breaker.record_failure()
                    self._record_retry_failure(func.__name__, attempt, str(e), retryable=False)
                    logger.error(f"All {self.retry_config.max_attempts} attempts failed for {func.__name__}")
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise Exception("All retry attempts failed")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        if self.retry_config.strategy == RetryStrategy.FIXED:
            delay = self.retry_config.base_delay
            
        elif self.retry_config.strategy == RetryStrategy.LINEAR:
            delay = self.retry_config.base_delay * attempt
            
        elif self.retry_config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.retry_config.base_delay * (
                self.retry_config.exponential_base ** (attempt - 1)
            )
            
        elif self.retry_config.strategy == RetryStrategy.FIBONACCI:
            fib = self._fibonacci(attempt)
            delay = self.retry_config.base_delay * fib
            
        else:
            delay = self.retry_config.base_delay
        
        # Apply backoff multiplier
        delay *= self.retry_config.backoff_multiplier
        
        # Cap at max delay
        delay = min(delay, self.retry_config.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.retry_config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    @staticmethod
    def _fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number.
        
        Args:
            n: Position in sequence
            
        Returns:
            Fibonacci number
        """
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    def _record_retry_success(self, func_name: str, attempts: int) -> None:
        """Record successful retry operation.
        
        Args:
            func_name: Name of function
            attempts: Number of attempts made
        """
        record = {
            'timestamp': datetime.now(),
            'function': func_name,
            'success': True,
            'attempts': attempts,
            'final_error': None
        }
        self.retry_history.append(record)
        
        # Keep only last 100 records
        if len(self.retry_history) > 100:
            self.retry_history.pop(0)
    
    def _record_retry_failure(self, func_name: str, attempts: int, error: str, retryable: bool) -> None:
        """Record failed retry operation.
        
        Args:
            func_name: Name of function
            attempts: Number of attempts made
            error: Error message
            retryable: Whether error was retryable
        """
        record = {
            'timestamp': datetime.now(),
            'function': func_name,
            'success': False,
            'attempts': attempts,
            'final_error': error,
            'retryable': retryable
        }
        self.retry_history.append(record)
        
        # Keep only last 100 records
        if len(self.retry_history) > 100:
            self.retry_history.pop(0)
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self.retry_history:
            return {
                'total_operations': 0,
                'success_rate': 0.0,
                'average_attempts': 0.0,
                'circuit_breaker_state': self.circuit_breaker.get_state_info()
            }
        
        total_ops = len(self.retry_history)
        successful_ops = sum(1 for record in self.retry_history if record['success'])
        total_attempts = sum(record['attempts'] for record in self.retry_history)
        
        # Get recent error breakdown
        recent_errors = {}
        for record in self.retry_history[-20:]:  # Last 20 operations
            if not record['success'] and record['final_error']:
                error_type = record['final_error'].split(':')[0]  # Get error type
                recent_errors[error_type] = recent_errors.get(error_type, 0) + 1
        
        return {
            'total_operations': total_ops,
            'successful_operations': successful_ops,
            'failed_operations': total_ops - successful_ops,
            'success_rate': (successful_ops / total_ops) * 100 if total_ops > 0 else 0.0,
            'average_attempts': total_attempts / total_ops if total_ops > 0 else 0.0,
            'recent_error_breakdown': recent_errors,
            'circuit_breaker_state': self.circuit_breaker.get_state_info()
        }
    
    def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self.circuit_breaker.state = CircuitState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.success_count = 0
        self.circuit_breaker.last_failure_time = None
        self.circuit_breaker.next_attempt_time = None
        logger.info("Circuit breaker manually reset to CLOSED")


def retry_on_exception(retry_config: Optional[RetryConfig] = None,
                      retry_on: Optional[List[type]] = None,
                      no_retry_on: Optional[List[type]] = None):
    """Decorator for automatic retry on exceptions.
    
    Args:
        retry_config: Retry configuration
        retry_on: Exception types to retry on
        no_retry_on: Exception types to never retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        retry_manager = RetryManager(retry_config)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_manager.execute_with_retry(
                func, *args, 
                retry_on=retry_on,
                no_retry_on=no_retry_on,
                **kwargs
            )
        
        # Attach retry manager for access
        wrapper.retry_manager = retry_manager
        return wrapper
    
    return decorator


# Common retry configurations
class CommonRetryConfigs:
    """Pre-defined retry configurations for common scenarios."""
    
    # Fast retry for lightweight operations
    FAST = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
    
    # Standard retry for normal operations
    STANDARD = RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
    
    # Aggressive retry for critical operations
    AGGRESSIVE = RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=60.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
    
    # Patient retry for slow operations
    PATIENT = RetryConfig(
        max_attempts=3,
        base_delay=5.0,
        max_delay=120.0,
        strategy=RetryStrategy.LINEAR
    )


# Common circuit breaker configurations
class CommonCircuitConfigs:
    """Pre-defined circuit breaker configurations."""
    
    # Sensitive circuit breaker
    SENSITIVE = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        success_threshold=2
    )
    
    # Standard circuit breaker
    STANDARD = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        success_threshold=3
    )
    
    # Tolerant circuit breaker
    TOLERANT = CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=120,
        success_threshold=5
    )