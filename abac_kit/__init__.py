"""abac-kit — attribute-based access control for Django & DRF."""

from __future__ import annotations

from .config import PolicyConfig
from .registry import get_config, get_subject_model, register

__version__ = "0.1.0"

__all__ = [
    "PolicyConfig",
    "register",
    "get_config",
    "get_subject_model",
    "__version__",
]
