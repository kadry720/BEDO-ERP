from frappe.tests.utils import FrappeTestCase

from bedo_erp.security.policies import is_system_admin


class TestSecurityPolicies(FrappeTestCase):
    def test_administrator_is_system_admin(self):
        self.assertTrue(is_system_admin("Administrator"))
