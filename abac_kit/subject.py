"""Optional mixin to attach ABAC behaviour to a project's user model.

Add it to your custom user model (anywhere in the bases) to get ``has_permission``,
``effective_permissions`` and ``get_domain_flags`` for free::

    from django.contrib.auth.models import AbstractBaseUser
    from abac_kit.subject import AbacSubjectMixin

    class User(AbacSubjectMixin, AbstractBaseUser):
        role = models.CharField(...)
        user_type = models.CharField(...)
        access_retail = models.BooleanField(default=False)
        ...
"""

from __future__ import annotations

from .engine import effective_permissions, subject_domains, subject_has_permission


class AbacSubjectMixin:
    """Provides ABAC convenience methods on top of a subject model.

    The subject model is expected to expose the attributes named by the
    registered :class:`~abac_kit.config.PolicyConfig` (``role_field`` and
    ``user_type_field``) plus any domain-flag fields referenced by
    ``domain_map``.
    """

    def has_permission(self, code: str) -> bool:
        """True if this subject holds the given permission code."""
        return subject_has_permission(self, code)

    @property
    def effective_permissions(self) -> list:
        """The subject's effective permission codes."""
        return effective_permissions(self)

    def get_domain_flags(self) -> set:
        """Domain field names this subject currently holds."""
        return subject_domains(self)
