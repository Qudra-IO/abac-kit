"""The decision engine.

All authorization logic lives here and reads exclusively from the registered
:class:`~abac_kit.config.PolicyConfig`. Subjects are plain objects (typically
the Django user model) exposing ``role``/``user_type``/domain-flag attributes.
"""

from __future__ import annotations

from typing import Iterable, Optional

from .models import RolePermission, UserPermissionOverride
from .registry import get_config


def _subject_attr(subject, name, default=None):
    return getattr(subject, name, default)


def subject_role(subject) -> Optional[str]:
    config = get_config()
    return _subject_attr(subject, config.role_field)


def subject_user_type(subject) -> Optional[str]:
    config = get_config()
    return _subject_attr(subject, config.user_type_field)


def is_authenticated(subject) -> bool:
    return bool(_subject_attr(subject, "is_authenticated", False))


def is_staff(subject) -> bool:
    config = get_config()
    if config.staff_user_type is None:
        return True
    return subject_user_type(subject) == config.staff_user_type


def is_super_role(subject) -> bool:
    config = get_config()
    if config.super_role is None:
        return False
    return subject_role(subject) == config.super_role


def subject_domains(subject) -> set:
    """Domain field names the subject currently holds (truthy flags)."""
    config = get_config()
    return {field for field in config.domain_fields() if _subject_attr(subject, field, False)}


def role_required_domains(role) -> set:
    """Domain field names a role requires (truthy entries in its scope)."""
    config = get_config()
    scope = config.role_default_domain_scope.get(role, {})
    return {field for field, enabled in scope.items() if enabled}


def permission_codes() -> list:
    return get_config().permission_values()


def role_codes() -> list:
    return get_config().role_values()


def subject_has_permission(subject, code: str) -> bool:
    """Return whether ``subject`` holds ``code``.

    Decision order: unauthenticated/non-staff -> deny; super role -> allow;
    explicit override -> follow it; domain gate -> deny if flag off; finally
    consult ``RolePermission`` defaults.
    """
    if subject is None or not is_authenticated(subject):
        return False
    if not is_staff(subject):
        return False
    if is_super_role(subject):
        return True

    override = UserPermissionOverride.objects.filter(user=subject, permission=code).first()
    if override is not None:
        return not override.is_revoked

    domain_field = get_config().domain_map.get(code)
    if domain_field and not _subject_attr(subject, domain_field, False):
        return False

    return RolePermission.objects.filter(role=subject_role(subject), permission=code).exists()


def effective_permissions(subject) -> list:
    """List the effective permission codes for ``subject``.

    Super role -> every code; otherwise role defaults merged with overrides
    (a grant adds, a revoke removes). Non-staff subjects return ``[]``.
    """
    if subject is None or not is_authenticated(subject):
        return []
    if not is_staff(subject):
        return []
    if is_super_role(subject):
        return permission_codes()

    role = subject_role(subject)
    role_perms = list(RolePermission.objects.filter(role=role).values_list("permission", flat=True))
    overrides = UserPermissionOverride.objects.filter(user=subject).values_list(
        "permission", "is_revoked"
    )
    override_map = {perm: revoked for perm, revoked in overrides}

    result = []
    for perm in role_perms:
        if perm in override_map:
            if not override_map[perm]:
                result.append(perm)
        else:
            result.append(perm)
    for perm, revoked in override_map.items():
        if not revoked and perm not in role_perms:
            result.append(perm)
    return result


def grantable_permissions(subject) -> list:
    """Permission codes ``subject`` may grant/revoke for others.

    Super role can grant everything; everyone else is limited to arm-scoped
    permissions whose domain matches one of their own domains, excluding
    non-delegable permissions.
    """
    config = get_config()
    if is_super_role(subject):
        return permission_codes()
    domains = subject_domains(subject)
    return [
        code
        for code, domain in config.domain_map.items()
        if domain in domains and code not in config.non_delegable_permissions
    ]


def creatable_roles(subject) -> list:
    """Role codes ``subject`` may create/manage.

    Super role can create any role; everyone else is limited to non-privileged
    roles whose required domains are a subset of their own.
    """
    config = get_config()
    if is_super_role(subject):
        return role_codes()
    domains = subject_domains(subject)
    result = []
    for role in role_codes():
        if role in config.privileged_roles:
            continue
        if role_required_domains(role) <= domains:
            result.append(role)
    return result


def is_group_owner(subject) -> bool:
    """True for roles with full cross-domain visibility."""
    if subject is None or not is_authenticated(subject):
        return False
    if not is_staff(subject):
        return False
    return subject_role(subject) in get_config().group_owner_roles


def accessible_domains(subject) -> list:
    """Domain field names the subject has access to (sorted, stable order)."""
    return sorted(subject_domains(subject))


def scoped_domain(subject, requested_domain=None):
    """Pin a single-domain subject to their only domain.

    Group owners keep the requested domain unchanged. A subject holding exactly
    one domain is pinned to it; otherwise the requested value is returned.
    """
    if is_group_owner(subject):
        return requested_domain
    domains = accessible_domains(subject)
    if len(domains) == 1:
        return domains[0]
    return requested_domain
