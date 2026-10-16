"""Helpers for seeding role default permissions into ``RolePermission``."""

from __future__ import annotations

from .models import RolePermission
from .registry import get_config


def seed_role_permissions(roles=None) -> int:
    """Create ``RolePermission`` rows from ``role_default_permissions``.

    Optionally restrict to a subset of roles. Idempotent. Returns the total
    number of ``RolePermission`` rows after seeding.
    """
    config = get_config()
    for role, perms in config.role_default_permissions.items():
        if roles and role not in roles:
            continue
        for perm in perms:
            RolePermission.objects.get_or_create(role=role, permission=perm)
    return RolePermission.objects.count()
