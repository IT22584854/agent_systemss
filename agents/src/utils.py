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
            "%(asctime)s.%(msecs)03d | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# === Input Sanitization ===
DANGEROUS_TOKENS = frozenset([
    "<|im_start|>", "<|im_end|>", "<|system|>", "[INST]", "<<SYS>>",
])

_FAST_PATTERNS = None

def _get_compiled_patterns():
    """Lazy compile patterns once, reuse forever."""
    global _FAST_PATTERNS
    if _FAST_PATTERNS is None:
        _FAST_PATTERNS = [
            (re.compile(r"(?i)ignore.{0,20}(previous|all).{0,20}instructions?"), "instruction_override"),
            (re.compile(r"(?i)you are now|act as a|pretend to be"), "role_hijack"),
            (re.compile(r"(?i)show.{0,15}system.{0,15}prompt"), "prompt_extraction"),
        ]
    return _FAST_PATTERNS


def detect_injection_fast(text: str) -> tuple[bool, str]:
    """
    Fast injection detection with early exit.
    Target: <1ms for typical inputs.
    """
    text_lower = text.lower()
    
    # TIER 1: O(n) substring checks 
    for token in DANGEROUS_TOKENS:
        if token.lower() in text_lower:
            return (True, "dangerous_token")
    
    # TIER 2: Only 3 critical patterns 
    for pattern, injection_type in _get_compiled_patterns():
        if pattern.search(text):
            return (True, injection_type)
    
    return (False, "")


def sanitize_input(
    text: str, 
    max_length: int = 2000,
    check_injection: bool = True
) -> str:
    """Sanitize with minimal latency impact."""
    if not text:
        return ""
    
    # prevents everything else from being slow
    if len(text) > max_length:
        text = text[:max_length]
    
    # Fast path: skip sanitization for short, simple inputs
    if len(text) < 500 and text.isascii() and not check_injection:
        return text.strip()
    
    # Unicode + control char removal (~0.05ms)
    text = text.replace("\x00", "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    
    # Injection check (~0.1ms with fast patterns)
    if check_injection:
        is_suspicious, injection_type = detect_injection_fast(text)
        if is_suspicious:
            # Log async if possible, don't block
            text = f"[FLAGGED:{injection_type}] {text}"
    
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
