from frappe.tests.utils import FrappeTestCase

from bedo_erp.audit.services import normalize_filters


class TestAudit(FrappeTestCase):
    def test_normalize_success_filter(self):
        filters = normalize_filters({"success": "1", "event_type": "Login Success"})
        self.assertEqual(filters["success"], 1)
        self.assertEqual(filters["event_type"], "Login Success")
