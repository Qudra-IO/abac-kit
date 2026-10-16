"""Django REST Framework permission classes backed by the abac-kit engine.

These mirror a typical RBAC/ABAC permission API so a project can drop them into
``permission_classes`` or ``get_permissions()``::

    from abac_kit.permissions import HasPermission, IsStaffUser

    class MyView(APIView):
        permission_classes = [HasPermission("manage_orders")]
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from .engine import is_super_role, subject_has_permission, subject_role, subject_user_type
from .registry import get_config


def _user(request):
    return getattr(request, "user", None)


class HasPermission(BasePermission):
    """Grant access when the request user holds a specific permission."""

    def __init__(self, permission_code: str):
        self.permission_code = permission_code

    def __call__(self):
        return self

    def has_permission(self, request, view) -> bool:
        return subject_has_permission(_user(request), self.permission_code)

    def has_object_permission(self, request, view, obj) -> bool:
        return self.has_permission(request, view)


class HasAnyPermission(BasePermission):
    """Grant access when the request user holds any of several permissions."""

    def __init__(self, permission_codes):
        self.permission_codes = permission_codes

    def __call__(self):
        return self

    def has_permission(self, request, view) -> bool:
        user = _user(request)
        return any(subject_has_permission(user, code) for code in self.permission_codes)

    def has_object_permission(self, request, view, obj) -> bool:
        return self.has_permission(request, view)


class IsStaffUser(BasePermission):
    """Grant access to authenticated staff subjects only."""

    def has_permission(self, request, view) -> bool:
        user = _user(request)
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        config = get_config()
        if config.staff_user_type is None:
            return True
        return subject_user_type(user) == config.staff_user_type


class IsSuperAdmin(BasePermission):
    """Grant access to the configured super role only."""

    def has_permission(self, request, view) -> bool:
        user = _user(request)
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        if not is_super_role(user):
            return False
        return True


class IsSameBranch(BasePermission):
    """Object-level check: super role bypasses; others must share a branch."""

    branch_field = "branch"

    def has_object_permission(self, request, view, obj) -> bool:
        user = _user(request)
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        if is_super_role(user):
            return True
        if not hasattr(obj, self.branch_field):
            return True
        return getattr(obj, self.branch_field) == getattr(user, self.branch_field)


class IsOwnerOrStaff(BasePermission):
    """Object-level check: staff bypass; owners match on ``user_id``/``user``."""

    def has_object_permission(self, request, view, obj) -> bool:
        user = _user(request)
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        config = get_config()
        if config.staff_user_type is not None and subject_user_type(user) == config.staff_user_type:
            return True
        if hasattr(obj, "user_id"):
            return obj.user_id == getattr(user, "pk", None)
        if hasattr(obj, "user"):
            return obj.user == user
        return False
