from __future__ import annotations

from datetime import datetime
from typing import Any

from bedo_platform.services.deadline_service import create_deadline, to_storage_datetime

SUPPLIER_ORDER_STATUS_OPEN = "OPEN"
SUPPLIER_ORDER_STATUS_TRACKED_OUTSIDE_ARD = "TRACKED_OUTSIDE_ARD"


def create_supplier_order_from_ard(
    *,
    interruption,
    order_type: str,
    deadline_days: int,
    actor: str,
    notes: str = "",
    bom_path: str = "",
) -> dict[str, Any]:
    import frappe

    generation = int(getattr(interruption, "generation", 1) or 1)
    existing = frappe.db.get_value(
        "BEDO Supplier Order",
        {
            "source_doctype": "ARD Interruption Request",
            "source_name": interruption.name,
            "source_generation": generation,
            "supplier_order_type": order_type,
            "is_superseded": 0,
        },
        "name",
    )
    if existing:
        return {"success": True, "supplier_order": existing, "created": False}

    deadline_name = ""
    if int(deadline_days or 0) > 0:
        deadline = create_deadline(
            project=interruption.project,
            trainer_item=interruption.trainer_item,
            workflow_type="SUPPLIERS",
            node_id=f"ARD_{order_type}",
            triggered_by=actor,
            deadline_days=int(deadline_days),
        )
        deadline_name = str(deadline["name"])

    doc = frappe.get_doc(
        {
            "doctype": "BEDO Supplier Order",
            "project": interruption.project,
            "trainer_item": interruption.trainer_item,
            "source_doctype": "ARD Interruption Request",
            "source_name": interruption.name,
            "source_generation": generation,
            "supplier_order_type": order_type,
            "status": SUPPLIER_ORDER_STATUS_TRACKED_OUTSIDE_ARD,
            "deadline_days": int(deadline_days or 0),
            "deadline": deadline_name,
            "notes": notes[:500],
            "bom_path": bom_path[:500],
            "created_by": actor,
            "created_at": to_storage_datetime(datetime.utcnow()),
            "is_superseded": 0,
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    return {"success": True, "supplier_order": doc.name, "created": True}
