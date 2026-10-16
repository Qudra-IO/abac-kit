"""Signal handlers that keep the subject's domain flags in sync with roles and
permission overrides.

Connected to the configured subject model from :meth:`AbacKitConfig.ready`. All
logic reads the registered :class:`~abac_kit.config.PolicyConfig`, so the
handlers know nothing about a specific project's flags.

Handlers:

* ``enforce_domain_cascade`` — when a domain flag is switched off, delete the
  subject's permission overrides scoped to that domain.
* ``enforce_domain_flag_on_permission_grant`` — when a subject holds a granted
  override in a domain they don't have a flag for, turn that flag on.
* ``set_default_domain_scope_on_role_change`` — apply the role's default domain
  scope on creation and whenever the role changes.
"""

from __future__ import annotations

from .engine import is_staff, subject_role
from .models import UserPermissionOverride
from .registry import get_config


def _permissions_for_domain(domain_field):
    config = get_config()
    return [perm for perm, domain in config.domain_map.items() if domain == domain_field]


def enforce_domain_cascade(sender, instance, **kwargs):
    config = get_config()
    if not is_staff(instance):
        return
    if not instance.pk:
        return
    try:
        old = sender._default_manager.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    for field in config.domain_fields():
        if getattr(old, field, False) and not getattr(instance, field, False):
            UserPermissionOverride.objects.filter(
                user=instance,
                permission__in=_permissions_for_domain(field),
            ).delete()


def enforce_domain_flag_on_permission_grant(sender, instance, **kwargs):
    config = get_config()
    if not is_staff(instance):
        return
    if not instance.pk:
        return
    for field in config.domain_fields():
        if not getattr(instance, field, False):
            granted = UserPermissionOverride.objects.filter(
                user=instance,
                permission__in=_permissions_for_domain(field),
                is_revoked=False,
            ).exists()
            if granted:
                setattr(instance, field, True)


def set_default_domain_scope_on_role_change(sender, instance, **kwargs):
    config = get_config()
    if not is_staff(instance):
        return
    role = subject_role(instance)
    if not role:
        return

    if not instance.pk:
        scope = config.role_default_domain_scope.get(role)
        if scope:
            for field, enabled in scope.items():
                setattr(instance, field, enabled)
        return

    try:
        old = sender._default_manager.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if subject_role(old) != role:
        scope = config.role_default_domain_scope.get(role)
        if scope:
            for field, enabled in scope.items():
                setattr(instance, field, enabled)
