import frappe
from frappe.model.document import Document


class BEDOAccessAuditLog(Document):
    def before_insert(self):
        if not self.created_at:
            self.created_at = frappe.utils.now_datetime()
