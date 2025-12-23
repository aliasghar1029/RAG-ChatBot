import logging
import sys
from datetime import datetime
from typing import Dict, Any

class CustomFormatter(logging.Formatter):
    """Custom formatter to add color and structure to logs"""

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Set up logging configuration"""
    logger = logging.getLogger("rag_chatbot")
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Console handler with custom formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(CustomFormatter())

    # Add handlers to logger
    logger.addHandler(console_handler)

    # Also configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    return logger

# Global logger instance
logger = setup_logging()

def log_api_call(endpoint: str, method: str, response_time: float, success: bool, user_id: str = None):
    """Log API calls with relevant information"""
    status = "SUCCESS" if success else "ERROR"
    logger.info(f"API_CALL - {method} {endpoint} - {response_time:.3f}s - {status} - User: {user_id or 'anonymous'}")

def log_embedding_generation(text_length: int, response_time: float):
    """Log embedding generation events"""
    logger.debug(f"EMBEDDING_GEN - Text length: {text_length} chars - Time: {response_time:.3f}s")

def log_search_query(query: str, results_count: int, response_time: float):
    """Log search queries"""
    logger.debug(f"SEARCH_QUERY - Query: '{query[:50]}...' - Results: {results_count} - Time: {response_time:.3f}s")

def log_error(error: Exception, context: str = ""):
    """Log errors with context"""
    logger.error(f"ERROR - {context} - {str(error)} - Type: {type(error).__name__}")