"""Shared utilities for logging, input sanitization, and retry logic."""
import logging
import re
import time
import unicodedata
from functools import wraps
from typing import Callable, TypeVar, Any

from agents.src.config import MAX_INPUT_LENGTH, LLM_MAX_RETRIES, LLM_RETRY_DELAY

# === Logging Setup ===
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# === Input Sanitization ===
def sanitize_input(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Sanitize user input before processing.
    
    - Enforces maximum length
    - Removes control characters (keeps newlines, tabs)
    - Normalizes unicode
    - Strips null bytes
    - Normalizes whitespace
    """
    if not text:
        return ""
    
    # Enforce length limit
    if len(text) > max_length:
        text = text[:max_length]
    
    # Normalize unicode (NFKC normalizes compatibility characters)
    text = unicodedata.normalize("NFKC", text)
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Remove control characters except newline, tab, carriage return
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    
    # Normalize excessive whitespace (but preserve single newlines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


# === Retry Decorator ===
T = TypeVar("T")

def retry_on_error(
    max_retries: int = LLM_MAX_RETRIES,
    delay: float = LLM_RETRY_DELAY,
    exceptions: tuple = (Exception,),
    logger: logging.Logger = None
) -> Callable:
    """
    Decorator to retry a function on specified exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds (doubles each retry)
        exceptions: Tuple of exception types to catch
        logger: Logger instance for logging retries
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if logger:
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                                f"Retrying in {current_delay:.1f}s..."
                            )
                        time.sleep(current_delay)
                        current_delay *= 2  # Exponential backoff
                    else:
                        if logger:
                            logger.error(f"{func.__name__} failed after {max_retries + 1} attempts: {e}")
            
            raise last_exception
        return wrapper
    return decorator


# === Error Response Helper ===
def create_error_response(error_type: str = "general") -> str:
    """Generate a user-friendly error message."""
    messages = {
        "llm": "I'm having trouble processing your request right now. Please try again in a moment.",
        "retrieval": "I couldn't retrieve the relevant information. Please try rephrasing your question.",
        "general": "An unexpected error occurred. Please try again.",
    }
    return messages.get(error_type, messages["general"])
