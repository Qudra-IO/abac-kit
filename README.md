# abac-kit

Attribute-based access control (ABAC) for **Django** and **Django REST Framework**.

Define your own roles, permissions, and domain scopes, register a single
`PolicyConfig`, and get a full authorization engine — permission classes,
per-user overrides, domain (arm) scoping, and delegation helpers — without
rewriting the same access-control logic in every project.

## Features

- **Declarative policy** — one `PolicyConfig` describes your roles, permissions,
  categories, domain scopes, and delegation rules.
- **DRF permission classes** — `HasPermission`, `HasAnyPermission`, `IsStaffUser`,
  `IsSuperAdmin`, `IsSameBranch`, `IsOwnerOrStaff`.
- **Per-user overrides** — grant or revoke individual permissions on top of role
  defaults; a grant can bypass a domain gate, a revoke always denies.
- **Domain (arm) scoping** — each permission can be gated by a subject attribute
  (e.g. `access_retail`), keeping staff isolated to their business arm.
- **Signals** — domain flags stay in sync when roles change or permissions are
  granted/revoked.
- **Delegation helpers** — compute which roles/permissions a subject may grant.

## Install

```bash
pip install abac-kit
```

## Quick start

### 1. Define your policy

```python
from django.db import models
from abac_kit import PolicyConfig, register

class Permission(models.TextChoices):
    VIEW_ORDERS = "VIEW_ORDERS", "View orders"
    MANAGE_ORDERS = "MANAGE_ORDERS", "Manage orders"
    MANAGE_USERS = "MANAGE_USERS", "Manage users"

class Role(models.TextChoices):
    ADMIN = "ADMIN", "Administrator"
    AGENT = "AGENT", "Support agent"

register(
    PolicyConfig(
        permissions=Permission,
        roles=Role,
        domain_map={
            "VIEW_ORDERS": "access_orders",
            "MANAGE_ORDERS": "access_orders",
            "MANAGE_USERS": None,
        },
        role_default_permissions={
            Role.ADMIN: [Permission.MANAGE_USERS],
            Role.AGENT: [Permission.VIEW_ORDERS, Permission.MANAGE_ORDERS],
        },
        role_default_domain_scope={
            Role.ADMIN: {"access_orders": True},
            Role.AGENT: {"access_orders": True},
        },
        privileged_roles={Role.ADMIN},
        non_delegable_permissions={Permission.MANAGE_USERS},
        group_owner_roles={Role.ADMIN},
        super_role=Role.ADMIN,
        staff_user_type="STAFF",
    )
)
```

### 2. Add the mixin to your user model

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from abac_kit.subject import AbacSubjectMixin

class User(AbacSubjectMixin, AbstractBaseUser):
    role = models.CharField(max_length=50, choices=Role.choices, blank=True, null=True)
    user_type = models.CharField(max_length=20, default="STAFF")
    access_orders = models.BooleanField(default=False)
    ...
```

### 3. Use the permission classes in views

```python
from rest_framework.views import APIView
from abac_kit.permissions import HasPermission

class OrderListView(APIView):
    permission_classes = [HasPermission("VIEW_ORDERS")]
```

### 4. Wire up the app and seed defaults

```python
INSTALLED_APPS = [
    ...
    "abac_kit",
    "yourapp",
]
```

```bash
python manage.py migrate
```

Seed role defaults (e.g. from a data migration or management command):

```python
from abac_kit.seed import seed_role_permissions

seed_role_permissions()
```

## Configuration reference

`PolicyConfig` fields:

| Field | Description |
|---|---|
| `permissions` | `TextChoices` subclass of every permission code |
| `roles` | `TextChoices` subclass of every role |
| `category_map` | `{permission: category}` for UIs |
| `domain_map` | `{permission: subject_field_name \| None}` — gates a permission behind a subject attribute |
| `role_default_permissions` | `{role: [permission, ...]}` |
| `role_default_domain_scope` | `{role: {field: bool, ...}}` — flags a role turns on |
| `privileged_roles` | roles non-privileged staff may not create/manage |
| `non_delegable_permissions` | permissions never grantable by non-super users |
| `group_owner_roles` | roles with full cross-domain visibility |
| `super_role` | role that bypasses all checks |
| `staff_user_type` | `user_type` value identifying staff (or `None`) |
| `role_field` | subject attribute holding the role (default `"role"`) |
| `user_type_field` | subject attribute holding the user type (default `"user_type"`) |

## Engine API

```python
from abac_kit.engine import (
    subject_has_permission,
    effective_permissions,
    grantable_permissions,
    creatable_roles,
    is_group_owner,
    subject_domains,
    accessible_domains,
    scoped_domain,
)
```

## License

MIT — see [LICENSE](LICENSE).
