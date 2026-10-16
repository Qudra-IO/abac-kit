from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from abac_kit.models import RolePermission, UserPermissionOverride
from abac_kit.permissions import (
    HasAnyPermission,
    HasPermission,
    IsStaffUser,
    IsSuperAdmin,
)
from abac_kit.seed import seed_role_permissions

from .factories import make_user
from .models import Role, UserType


class PermissionClassTests(TestCase):
    def setUp(self):
        seed_role_permissions()
        self.factory = APIRequestFactory()

    def _req(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_has_permission_super_admin(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        self.assertTrue(HasPermission("RETAIL_POS").has_permission(self._req(admin), None))
        self.assertTrue(HasPermission("FOODS_POS").has_permission(self._req(admin), None))

    def test_has_permission_cashier(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertTrue(HasPermission("RETAIL_POS").has_permission(self._req(cashier), None))
        self.assertFalse(HasPermission("FOODS_POS").has_permission(self._req(cashier), None))

    def test_has_any_permission(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertTrue(
            HasAnyPermission(["FOODS_POS", "RETAIL_POS"]).has_permission(self._req(cashier), None)
        )
        self.assertFalse(
            HasAnyPermission(["FOODS_POS", "MANAGE_EMPLOYEES"]).has_permission(
                self._req(cashier), None
            )
        )

    def test_is_staff_user(self):
        staff = make_user("staff@test.com", Role.CASHIER)
        customer = make_user("cust@test.com", role=None, user_type=UserType.CUSTOMER)
        self.assertTrue(IsStaffUser().has_permission(self._req(staff), None))
        self.assertFalse(IsStaffUser().has_permission(self._req(customer), None))

    def test_is_super_admin(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertTrue(IsSuperAdmin().has_permission(self._req(admin), None))
        self.assertFalse(IsSuperAdmin().has_permission(self._req(cashier), None))


class ModelTests(TestCase):
    def test_role_permission_str(self):
        rp = RolePermission.objects.create(role="CASHIER", permission="RETAIL_POS")
        self.assertEqual(str(rp), "CASHIER -> RETAIL_POS")

    def test_role_permission_unique_together(self):
        RolePermission.objects.create(role="CASHIER", permission="RETAIL_POS")
        with self.assertRaises(IntegrityError):
            RolePermission.objects.create(role="CASHIER", permission="RETAIL_POS")

    def test_override_str(self):
        user = make_user("u@test.com", Role.CASHIER)
        override = UserPermissionOverride.objects.create(
            user=user, permission="RETAIL_POS", is_revoked=True
        )
        self.assertIn("REVOKED", str(override))

    def test_override_unique_together(self):
        user = make_user("u@test.com", Role.CASHIER)
        UserPermissionOverride.objects.create(user=user, permission="RETAIL_POS", is_revoked=True)
        with self.assertRaises(IntegrityError):
            UserPermissionOverride.objects.create(
                user=user, permission="RETAIL_POS", is_revoked=False
            )
