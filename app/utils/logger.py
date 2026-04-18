import logging
import sys


def setup_logger(name: str = "ai-agent-hybrid", level: str = "INFO") -> logging.Logger:
    """Setup structured logger untuk aplikasi."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Hindari duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Format: timestamp - name - level - message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Get child logger untuk modul tertentu."""
    return logging.getLogger(f"ai-agent-hybrid.{module_name}")
