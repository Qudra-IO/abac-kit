"""Central registry holding the active :class:`~abac_kit.config.PolicyConfig`.

Exactly one config may be registered per process. Register it once at startup,
for example from an ``AppConfig.ready()`` hook or directly from your
``models.py`` module::

    from abac_kit import PolicyConfig, register

    register(PolicyConfig(...))
"""

from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .config import PolicyConfig

_registry: dict = {"config": None}


def register(config: PolicyConfig) -> PolicyConfig:
    """Register the project's :class:`PolicyConfig`.

    Returns the config for convenience. Raises ``TypeError`` if given anything
    other than a :class:`PolicyConfig`.
    """
    if not isinstance(config, PolicyConfig):
        raise TypeError(
            f"register() expects a PolicyConfig instance, got {type(config).__name__!r}."
        )
    _registry["config"] = config
    return config


def get_config() -> PolicyConfig:
    """Return the registered config, raising if none has been registered."""
    config = _registry["config"]
    if config is None:
        raise ImproperlyConfigured(
            "abac-kit is not configured. Call abac_kit.register(PolicyConfig(...)) "
            "once at startup (e.g. in an AppConfig.ready() or your models module)."
        )
    return config


def get_subject_model():
    """Return the configured subject model (``settings.AUTH_USER_MODEL``)."""
    return apps.get_model(settings.AUTH_USER_MODEL)
