import frappe
from frappe.model.document import Document


class BEDOUserProfile(Document):
    def validate(self):
        if not self.auth_source:
            self.auth_source = "Local"
        if self.is_active_in_bedo_erp is None:
            self.is_active_in_bedo_erp = 1
        if self.email and self.user:
            user_email = frappe.db.get_value("User", self.user, "email")
            if user_email and self.email != user_email:
                self.email = user_email
