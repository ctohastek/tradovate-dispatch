# app/parser/__init__.py
from .parser import CommandParser

try:
    from .validator import CommandValidator
    __all__ = ["CommandParser", "CommandValidator"]
except ImportError:
    __all__ = ["CommandParser"]
