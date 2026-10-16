"""Django app configuration for abac-kit."""

from __future__ import annotations

from django.apps import AppConfig
from django.db.models.signals import pre_save


class AbacKitConfig(AppConfig):
    name = "abac_kit"
    verbose_name = "ABAC Kit"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from .registry import get_subject_model
        from .signals import (
            enforce_domain_cascade,
            enforce_domain_flag_on_permission_grant,
            set_default_domain_scope_on_role_change,
        )

        subject_model = get_subject_model()
        pre_save.connect(
            enforce_domain_cascade,
            sender=subject_model,
            weak=False,
            dispatch_uid="abac_kit.enforce_domain_cascade",
        )
        pre_save.connect(
            enforce_domain_flag_on_permission_grant,
            sender=subject_model,
            weak=False,
            dispatch_uid="abac_kit.enforce_domain_flag_on_permission_grant",
        )
        pre_save.connect(
            set_default_domain_scope_on_role_change,
            sender=subject_model,
            weak=False,
            dispatch_uid="abac_kit.set_default_domain_scope_on_role_change",
        )
