"""Public package interface for the GCSE past paper generator."""

from .generator import PastPaperService
from .schemas import GenerationParams, PaperBundle, ValidationError

__all__ = [
    "GenerationParams",
    "PaperBundle",
    "PastPaperService",
    "ValidationError",
]
