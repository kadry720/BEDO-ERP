import frappe


class BedoValidationError(frappe.ValidationError):
    pass


class BedoPermissionError(frappe.PermissionError):
    pass
