from django.test import TestCase

from abac_kit import get_config
from abac_kit.engine import permission_codes, role_codes

from .models import Permission, Role, UserType


class ConfigTests(TestCase):
    def test_config_is_registered(self):
        config = get_config()
        self.assertEqual(config.super_role, Role.SUPER_ADMIN)
        self.assertEqual(config.staff_user_type, UserType.STAFF)

    def test_permission_codes(self):
        self.assertEqual(set(permission_codes()), set(Permission.values))

    def test_role_codes(self):
        self.assertEqual(set(role_codes()), set(Role.values))

    def test_domain_fields(self):
        self.assertEqual(get_config().domain_fields(), {"access_retail", "access_foods"})
