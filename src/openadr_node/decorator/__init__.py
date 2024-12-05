# decorator/__init__.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = ['logger']
