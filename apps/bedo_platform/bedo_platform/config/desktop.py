from frappe import _


def get_data():
    return [
        {
            "module_name": "BEDO Platform",
            "category": "Modules",
            "label": _("BEDO Platform"),
            "color": "#1f6f8b",
            "icon": "octicon octicon-organization",
            "type": "module",
            "description": _("BEDO platform foundation"),
        }
    ]
