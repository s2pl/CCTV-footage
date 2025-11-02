"""
Retry decorators for network operations
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Any
try:
    from ..config import config
except ImportError:
    import sys
    from pathlib import Path
    if str(Path(__file__).parent.parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import config

logger = logging.getLogger(__name__)


def async_retry(max_attempts: int = None, delay: float = 1.0, backoff: float = 2.0):
    """
    Async retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts (default from config)
        delay: Initial delay in seconds
        backoff: Backoff multiplier
    """
    if max_attempts is None:
        max_attempts = config.MAX_RETRY_ATTEMPTS
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator


def sync_retry(max_attempts: int = None, delay: float = 1.0, backoff: float = 2.0):
    """
    Sync retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts (default from config)
        delay: Initial delay in seconds
        backoff: Backoff multiplier
    """
    import time
    
    if max_attempts is None:
        max_attempts = config.MAX_RETRY_ATTEMPTS
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

