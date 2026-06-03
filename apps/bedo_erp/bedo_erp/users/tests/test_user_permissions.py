import frappe
from frappe.tests.utils import FrappeTestCase

from bedo_erp.shared.constants import BEDO_ROLES


class TestUserPermissions(FrappeTestCase):
    def test_phase_1_roles_exist(self):
        missing_roles = [role for role in BEDO_ROLES if not frappe.db.exists("Role", role)]
        self.assertEqual(missing_roles, [])
