from django.test import TestCase

from abac_kit.models import UserPermissionOverride

from .factories import make_user
from .models import Role, UserType


class SignalTests(TestCase):
    def test_new_staff_gets_default_domain_scope(self):
        chef = make_user("chef@test.com", Role.CHEF)
        self.assertFalse(chef.access_retail)
        self.assertTrue(chef.access_foods)

    def test_role_change_updates_domain_scope(self):
        user = make_user("user@test.com", Role.CASHIER)
        self.assertTrue(user.access_retail)
        self.assertFalse(user.access_foods)

        user.role = Role.CHEF
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.access_retail)
        self.assertTrue(user.access_foods)

    def test_customer_is_not_touched_by_signals(self):
        customer = make_user("cust@test.com", role=None, user_type=UserType.CUSTOMER)
        self.assertFalse(customer.access_retail)
        self.assertFalse(customer.access_foods)

    def test_domain_cascade_deletes_overrides(self):
        chef = make_user("chef@test.com", Role.CHEF)
        UserPermissionOverride.objects.create(
            user=chef, permission="FOODS_POS", is_revoked=False
        )
        chef.access_foods = False
        chef.save()
        self.assertFalse(
            UserPermissionOverride.objects.filter(user=chef, permission="FOODS_POS").exists()
        )

    def test_grant_flips_domain_flag(self):
        cashier = make_user("cashier@test.com", Role.CASHIER)
        self.assertFalse(cashier.access_foods)
        UserPermissionOverride.objects.create(
            user=cashier, permission="FOODS_POS", is_revoked=False
        )
        cashier.save()
        cashier.refresh_from_db()
        self.assertTrue(cashier.access_foods)
