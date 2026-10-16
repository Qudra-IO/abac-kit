"""Database models used by abac-kit.

``RolePermission`` stores the default permission assignments for a role, and
``UserPermissionOverride`` stores per-user grants/revokes that win over the role
defaults. Both are generic: ``role``/``permission`` are plain ``CharField`` s so
the same tables work for any project's catalog. The ``user`` foreign key points
at the project's own ``settings.AUTH_USER_MODEL``.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class RolePermission(models.Model):
    """A default permission granted to a role."""

    role = models.CharField(max_length=100, db_index=True)
    permission = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self) -> str:
        return f"{self.role} -> {self.permission}"


class UserPermissionOverride(models.Model):
    """A per-user grant (``is_revoked=False``) or revoke (``is_revoked=True``).

    Overrides are consulted *after* the super-role bypass but *before* the
    domain gate, so an explicit grant can unlock an arm-scoped permission even
    when the subject's domain flag is off, while an explicit revoke always
    denies.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abac_permission_overrides",
    )
    permission = models.CharField(max_length=100, db_index=True)
    is_revoked = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "permission")

    def __str__(self) -> str:
        action = "REVOKED" if self.is_revoked else "GRANTED"
        return f"{self.user} -> {self.permission} ({action})"
