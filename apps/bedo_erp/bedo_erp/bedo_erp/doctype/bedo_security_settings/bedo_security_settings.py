from frappe.model.document import Document


class BEDOSecuritySettings(Document):
    def validate(self):
        if self.max_failed_login_attempts is None:
            self.max_failed_login_attempts = 5
        if self.lockout_duration_minutes is None:
            self.lockout_duration_minutes = 15
        if self.session_timeout_minutes is None:
            self.session_timeout_minutes = 120
