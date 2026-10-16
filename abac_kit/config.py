"""Configuration object that describes a project's ABAC policy.

Consumers build a :class:`PolicyConfig` and pass it to :func:`abac_kit.register`
once at startup. The rest of the library (engine, signals, permission classes)
reads exclusively from this object, which is why the library has no knowledge
of any particular project's roles, permissions, or domain flags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence


@dataclass
class PolicyConfig:
    """Declarative description of an ABAC policy.

    Attributes
    ----------
    permissions:
        A ``django.db.models.TextChoices`` subclass enumerating every granular
        permission code. Used to resolve the full permission catalog (for
        super-user "has everything" and list endpoints).
    roles:
        A ``django.db.models.TextChoices`` subclass enumerating every role.
    category_map:
        Maps a permission code to a category label (for listing/UIs).
    domain_map:
        Maps a permission code to the *subject model field name* that gates it
        (e.g. ``"access_retail"``), or ``None`` for arm-neutral permissions that
        ignore domain flags.
    role_default_permissions:
        Maps a role to the list of permission codes it receives by default.
    role_default_domain_scope:
        Maps a role to ``{field_name: bool}`` describing which domain flags the
        role turns on. Used by signals (to apply defaults on role changes) and
        by the delegation helpers (to compute "domains a role requires").
    privileged_roles:
        Roles that non-privileged staff may not create or manage.
    non_delegable_permissions:
        Permission codes that may never be granted/revoked by non-super users
        (e.g. app-configuration permissions).
    super_role:
        The role code that bypasses all checks and is granted every permission.
    staff_user_type:
        The ``user_type`` value that identifies a staff subject. Subjects with
        any other ``user_type`` are treated as non-staff (no granular
        permissions). Set to ``None`` to skip the staff check entirely.
    group_owner_roles:
        Roles that have full cross-domain visibility (e.g. super admin and a
        corporate auditor). Used by :func:`abac_kit.engine.is_group_owner`.
    role_field:
        Attribute name on the subject that holds the role code. Default ``"role"``.
    user_type_field:
        Attribute name on the subject that holds the user type. Default
        ``"user_type"``.
    """

    permissions: Any = None
    roles: Any = None

    category_map: Mapping[str, Any] = field(default_factory=dict)
    domain_map: Mapping[str, Optional[str]] = field(default_factory=dict)
    role_default_permissions: Mapping[str, Sequence[str]] = field(default_factory=dict)
    role_default_domain_scope: Mapping[str, Mapping[str, bool]] = field(default_factory=dict)

    privileged_roles: set = field(default_factory=set)
    non_delegable_permissions: set = field(default_factory=set)
    group_owner_roles: set = field(default_factory=set)

    super_role: Optional[str] = None
    staff_user_type: Optional[str] = None

    role_field: str = "role"
    user_type_field: str = "user_type"

    def __post_init__(self) -> None:
        self.privileged_roles = set(self.privileged_roles or ())
        self.non_delegable_permissions = set(self.non_delegable_permissions or ())
        self.group_owner_roles = set(self.group_owner_roles or ())

    # -- Convenience accessors -------------------------------------------------

    def permission_values(self) -> list:
        if self.permissions is None:
            return []
        return [value for value in self.permissions.values]

    def role_values(self) -> list:
        if self.roles is None:
            return []
        return [value for value in self.roles.values]

    def domain_fields(self) -> set:
        """Every non-None domain field referenced by ``domain_map``."""
        return {field for field in self.domain_map.values() if field}
