from django.test import TestCase

from abac_kit.engine import (
    accessible_domains,
    creatable_roles,
    effective_permissions,
    grantable_permissions,
    is_group_owner,
    scoped_domain,
    subject_domains,
    subject_has_permission,
)
from abac_kit.models import UserPermissionOverride
from abac_kit.seed import seed_role_permissions

from .factories import make_user
from .models import Permission, Role, UserType


class EngineTests(TestCase):
    def setUp(self):
        seed_role_permissions()

    # -- effective permissions ------------------------------------------

    def test_super_admin_has_all_permissions(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        self.assertEqual(set(effective_permissions(admin)), set(Permission.values))

    def test_cashier_has_retail_permissions_only(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        perms = effective_permissions(cashier)
        self.assertIn("RETAIL_POS", perms)
        self.assertIn("RETAIL_VIEW", perms)
        self.assertNotIn("FOODS_POS", perms)
        self.assertNotIn("MANAGE_EMPLOYEES", perms)

    def test_customer_has_no_permissions(self):
        customer = make_user("cust@test.com", role=None, user_type=UserType.CUSTOMER)
        self.assertEqual(effective_permissions(customer), [])

    # -- subject_has_permission -----------------------------------------

    def test_super_admin_bypass(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        self.assertTrue(subject_has_permission(admin, "RETAIL_POS"))
        self.assertTrue(subject_has_permission(admin, "MANAGE_EMPLOYEES"))

    def test_domain_gate(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertTrue(subject_has_permission(cashier, "RETAIL_POS"))
        self.assertFalse(subject_has_permission(cashier, "FOODS_POS"))

    def test_override_grant_bypasses_domain_gate(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertFalse(subject_has_permission(cashier, "FOODS_POS"))
        UserPermissionOverride.objects.create(
            user=cashier, permission="FOODS_POS", is_revoked=False
        )
        self.assertTrue(subject_has_permission(cashier, "FOODS_POS"))

    def test_override_revoke_denies_within_arm(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertTrue(subject_has_permission(cashier, "RETAIL_POS"))
        UserPermissionOverride.objects.create(
            user=cashier, permission="RETAIL_POS", is_revoked=True
        )
        self.assertFalse(subject_has_permission(cashier, "RETAIL_POS"))

    def test_non_staff_always_denied(self):
        customer = make_user("cust@test.com", role=None, user_type=UserType.CUSTOMER)
        UserPermissionOverride.objects.create(
            user=customer, permission="RETAIL_POS", is_revoked=False
        )
        self.assertFalse(subject_has_permission(customer, "RETAIL_POS"))

    # -- delegation helpers ---------------------------------------------

    def test_grantable_permissions_arm_scoped(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        grantable = grantable_permissions(cashier)
        self.assertIn("RETAIL_POS", grantable)
        self.assertNotIn("FOODS_POS", grantable)
        self.assertNotIn("MANAGE_EMPLOYEES", grantable)

    def test_grantable_permissions_super_admin(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        self.assertEqual(set(grantable_permissions(admin)), set(Permission.values))

    def test_creatable_roles(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        roles = creatable_roles(cashier)
        self.assertIn(Role.CASHIER, roles)
        self.assertNotIn(Role.SUPER_ADMIN, roles)
        self.assertNotIn(Role.CHEF, roles)

    # -- domain helpers -------------------------------------------------

    def test_subject_domains(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertEqual(subject_domains(admin), {"access_retail", "access_foods"})
        self.assertEqual(subject_domains(cashier), {"access_retail"})

    def test_is_group_owner(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertTrue(is_group_owner(admin))
        self.assertFalse(is_group_owner(cashier))

    def test_scoped_domain_pins_single_domain_user(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        self.assertEqual(scoped_domain(cashier, "access_foods"), "access_retail")
        self.assertEqual(scoped_domain(admin, "access_foods"), "access_foods")

    def test_accessible_domains_sorted(self):
        admin = make_user("admin@test.com", Role.SUPER_ADMIN)
        self.assertEqual(accessible_domains(admin), ["access_foods", "access_retail"])
