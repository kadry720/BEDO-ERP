from frappe.tests.utils import FrappeTestCase

from bedo_erp.identity.services import get_permissions_summary


class TestIdentity(FrappeTestCase):
    def test_administrator_permission_summary_can_manage_phase_1(self):
        summary = get_permissions_summary("Administrator", ["BEDO System Admin"])
        self.assertTrue(summary["can_manage_phase_1"])
        self.assertTrue(summary["can_manage_security_settings"])
