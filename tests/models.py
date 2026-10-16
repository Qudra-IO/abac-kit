"""Test fixture models: a consumer-style subject model + an ABAC policy."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from abac_kit import PolicyConfig, register
from abac_kit.subject import AbacSubjectMixin


class UserType(models.TextChoices):
    STAFF = "STAFF", "Staff"
    CUSTOMER = "CUSTOMER", "Customer"


class Role(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    CASHIER = "CASHIER", "Cashier"
    CHEF = "CHEF", "Chef"


class Permission(models.TextChoices):
    RETAIL_VIEW = "RETAIL_VIEW", "View Retail Inventory"
    RETAIL_POS = "RETAIL_POS", "Retail POS Access"
    FOODS_POS = "FOODS_POS", "Foods POS Access"
    MANAGE_EMPLOYEES = "MANAGE_EMPLOYEES", "Manage Employees"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("user_type", UserType.STAFF)
        extra_fields.setdefault("role", Role.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class TestUser(AbacSubjectMixin, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=UserType.choices, default=UserType.CUSTOMER)
    role = models.CharField(max_length=50, choices=Role.choices, blank=True, null=True)
    access_retail = models.BooleanField(default=False)
    access_foods = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    objects = UserManager()

    def __str__(self):
        return self.email


register(
    PolicyConfig(
        permissions=Permission,
        roles=Role,
        category_map={
            "RETAIL_VIEW": "RETAIL",
            "RETAIL_POS": "RETAIL",
            "FOODS_POS": "FOODS",
            "MANAGE_EMPLOYEES": "CORPORATE",
        },
        domain_map={
            "RETAIL_VIEW": "access_retail",
            "RETAIL_POS": "access_retail",
            "FOODS_POS": "access_foods",
            "MANAGE_EMPLOYEES": None,
        },
        role_default_permissions={
            Role.SUPER_ADMIN: [Permission.MANAGE_EMPLOYEES],
            Role.CASHIER: [Permission.RETAIL_VIEW, Permission.RETAIL_POS],
            Role.CHEF: [Permission.FOODS_POS],
        },
        role_default_domain_scope={
            Role.SUPER_ADMIN: {"access_retail": True, "access_foods": True},
            Role.CASHIER: {"access_retail": True, "access_foods": False},
            Role.CHEF: {"access_retail": False, "access_foods": True},
        },
        privileged_roles={Role.SUPER_ADMIN},
        non_delegable_permissions={Permission.MANAGE_EMPLOYEES},
        group_owner_roles={Role.SUPER_ADMIN},
        super_role=Role.SUPER_ADMIN,
        staff_user_type=UserType.STAFF,
    )
)
