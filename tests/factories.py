"""Test helpers."""

from __future__ import annotations

from .models import Role, TestUser, UserType


def make_user(email, role=None, user_type=UserType.STAFF, **flags):
    return TestUser.objects.create_user(
        email=email, password="x", user_type=user_type, role=role, **flags
    )
