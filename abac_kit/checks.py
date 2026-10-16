"""Django system checks for abac-kit."""

from __future__ import annotations

from django.core.checks import Error, register as register_check

from .registry import _registry


@register_check()
def abac_kit_configured(app_configs, **kwargs):
    if _registry["config"] is None:
        return [
            Error(
                "abac-kit has no registered PolicyConfig.",
                hint="Call abac_kit.register(PolicyConfig(...)) once at startup.",
                id="abac_kit.E001",
            )
        ]
    return []
