"""
Core Package
Application core components (config, logging, etc.)
"""

from app.core.config import settings
from app.core.logger import setup_logger

__all__ = ["settings", "setup_logger"]