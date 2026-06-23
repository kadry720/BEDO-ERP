from __future__ import annotations

from datetime import datetime
from typing import Any

from bedo_platform.constants import (
    COMMAND_CENTER_WORKFLOW_TYPE,
    SRS_NODE_ACTION_PATHS,
    SRS_NODE_BMDP,
    SRS_NODE_CASE_1,
    SRS_NODE_CASE_2,
    SRS_NODE_CASE_3,
    SRS_NODE_CASE_4,
    SRS_NODE_COORDINATION,
    SRS_NODE_DEADLINE_LOCKED,
    SRS_NODE_DELIVERABLES,
    SRS_NODE_DUAL_GATE_APPROVAL,
    SRS_NODE_EXTENSION_DEADLINE,
    SRS_NODE_GATE_2_PMDP,
    SRS_NODE_PHYSICAL_BUILD_TEST,
    SRS_NODE_PMDP,
    SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
    SRS_NODE_SRS_DIRECTOR_APPROVAL,
    SUPPLIERS_WORKFLOW_TYPE,
)
from bedo_platform.services.security_audit_service import log_security_event

RESET_COMMAND_CENTER = "COMMAND_CENTER"
RESET_SRS_ACTION_PATHS = "SRS_ACTION_PATHS"
RESET_SRS_COORDINATION = "SRS_COORDINATION"
SUPERSEDED_BY_RESET = "SUPERSEDED_BY_RESET"


def normalize_reset_target(target: str) -> str:
    normalized = str(target or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "COMMAND_CENTER": RESET_COMMAND_CENTER,
        "RESET_COMMAND_CENTER": RESET_COMMAND_CENTER,
        "SRS_ACTION_PATHS": RESET_SRS_ACTION_PATHS,
        "ACTION_PATHS": RESET_SRS_ACTION_PATHS,
        "RESET_TO_ACTION_PATHS": RESET_SRS_ACTION_PATHS,
        "SRS_COORDINATION": RESET_SRS_COORDINATION,
        "COORDINATION": RESET_SRS_COORDINATION,
        "RESET_TO_COORDINATION": RESET_SRS_COORDINATION,
    }
    if normalized not in aliases:
        raise ValueError(f"Unsupported reset target: {target}")
    return aliases[normalized]


def _utcnow() -> datetime:
    return datetime.utcnow()


def _require_gm(actor: str) -> None:
    import frappe

    if "General Manager" not in set(frappe.get_roles(actor)):
        frappe.throw("General Manager access is required.", frappe.PermissionError)


def _workflow_for_item(trainer_item: str):
    import frappe

    name = frappe.db.get_value("SRS Workflow Instance", {"trainer_item": trainer_item}, "name")
    if not name:
        frappe.throw("SRS workflow has not started for this trainer item.", frappe.DoesNotExistError)
    return frappe.get_doc("SRS Workflow Instance", name)


def _active_handoff(trainer_item: str):
    import frappe

    name = frappe.db.get_value("BEDO Command Center Handoff", {"trainer_item": trainer_item, "is_active": 1}, "name")
    return frappe.get_doc("BEDO Command Center Handoff", name) if name else None


def _supersede_meeting(meeting: str, reset_id: str) -> int:
    import frappe

    if not meeting or not frappe.db.exists("BEDO Meeting", meeting):
        return 0
    frappe.db.set_value(
        "BEDO Meeting",
        meeting,
        {"status": SUPERSEDED_BY_RESET, "is_superseded": 1, "superseded_by_reset": reset_id},
        update_modified=False,
    )
    for participant in frappe.get_all("BEDO Meeting Participant", filters={"meeting": meeting}, pluck="name"):
        frappe.db.set_value(
            "BEDO Meeting Participant",
            participant,
            {"is_active": 0, "superseded_by_reset": reset_id},
            update_modified=False,
        )
    return 1


def _supersede_related_meetings(reference_doctype: str, reference_name: str, reset_id: str) -> int:
    import frappe

    count = 0
    for meeting in frappe.get_all(
        "BEDO Meeting",
        filters={"related_reference_doctype": reference_doctype, "related_reference_name": reference_name, "is_superseded": 0},
        pluck="name",
    ):
        count += _supersede_meeting(meeting, reset_id)
    return count


def _supersede_approvals(filters: dict[str, Any], reset_id: str) -> int:
    import frappe

    count = 0
    for approval in frappe.get_all("SRS Approval", filters={**filters, "status": "WAITING"}, pluck="name"):
        frappe.db.set_value(
            "SRS Approval",
            approval,
            {"status": "DENIED", "comments": f"Superseded by reset {reset_id}"},
            update_modified=False,
        )
        count += 1
    return count


def _supersede_deadlines(filters: dict[str, Any]) -> int:
    import frappe

    count = 0
    for deadline in frappe.get_all(
        "BEDO Deadline",
        filters={**filters, "status": ["in", ["ACTIVE", "OVERDUE"]]},
        pluck="name",
    ):
        frappe.db.set_value("BEDO Deadline", deadline, "status", SUPERSEDED_BY_RESET, update_modified=False)
        count += 1
    return count


def _deactivate_supplier_files(source_handoff: str) -> int:
    import frappe

    count = 0
    for supplier in frappe.get_all("BEDO Supplier File", filters={"source_handoff": source_handoff, "is_active": 1}, fields=["name", "deadline"]):
        frappe.db.set_value("BEDO Supplier File", supplier.name, "is_active", 0, update_modified=False)
        if supplier.deadline:
            frappe.db.set_value("BEDO Deadline", supplier.deadline, "status", SUPERSEDED_BY_RESET, update_modified=False)
        count += 1
    return count


def _supersede_ard_workflows(trainer_item: str, reset_id: str) -> int:
    import frappe

    count = 0
    for workflow in frappe.get_all(
        "ARD Workflow Instance",
        filters={"trainer_item": trainer_item, "is_superseded": 0},
        pluck="name",
    ):
        frappe.db.set_value(
            "ARD Workflow Instance",
            workflow,
            {"status": SUPERSEDED_BY_RESET, "is_superseded": 1, "superseded_by_reset": reset_id},
            update_modified=False,
        )
        for node_state in frappe.get_all("ARD Workflow Node State", filters={"workflow_instance": workflow, "is_superseded": 0}, pluck="name"):
            frappe.db.set_value(
                "ARD Workflow Node State",
                node_state,
                {"status": SUPERSEDED_BY_RESET, "is_superseded": 1, "superseded_by_reset": reset_id},
                update_modified=False,
            )
        for team_member in frappe.get_all("ARD Workflow Team Member", filters={"workflow_instance": workflow, "is_active": 1}, pluck="name"):
            frappe.db.set_value(
                "ARD Workflow Team Member",
                team_member,
                {"is_active": 0, "superseded_by_reset": reset_id},
                update_modified=False,
            )
        count += 1
    return count


def _log_reset(event_type: str, actor: str, workflow, reset_id: str, message: str = "") -> None:
    log_security_event(
        event_type,
        user=actor,
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        workflow_type="SRS",
        node_id=workflow.current_node,
        status="Success",
        message=f"{reset_id}: {message}".strip(),
    )


def reset_command_center(trainer_item: str, actor: str, *, reason: str = "") -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    workflow = _workflow_for_item(trainer_item)
    handoff = _active_handoff(trainer_item)
    if not handoff:
        frappe.throw("Command Center handoff not found.", frappe.DoesNotExistError)
    reset_id = f"RESET-CC-{handoff.name}-G{int(handoff.generation or 1) + 1}"
    superseded_meetings = _supersede_meeting(getattr(handoff, "handover_meeting", ""), reset_id)
    superseded_meetings += _supersede_related_meetings("BEDO Command Center Handoff", handoff.name, reset_id)
    superseded_approvals = _supersede_approvals({"command_center_handoff": handoff.name}, reset_id)
    superseded_supplier_files = _deactivate_supplier_files(handoff.name)
    superseded_deadlines = _supersede_deadlines({"trainer_item": trainer_item, "workflow_type": ["in", [COMMAND_CENTER_WORKFLOW_TYPE, SUPPLIERS_WORKFLOW_TYPE]]})
    superseded_ard_workflows = _supersede_ard_workflows(trainer_item, reset_id)

    handoff.status = "PENDING_COMMAND_CENTER"
    handoff.command_center_case = ""
    handoff.deadline_days = 0
    handoff.approved_deadline_days = 0
    handoff.deadline = ""
    handoff.responsible_user = ""
    handoff.submitted_by = ""
    handoff.submitted_at = None
    handoff.gm_approval = ""
    handoff.gm_approved_by = ""
    handoff.gm_approved_at = None
    handoff.case3_cleared_at = None
    handoff.handover_meeting = ""
    handoff.handover_confirmation_status = "NOT_STARTED"
    handoff.handover_confirmed_by = ""
    handoff.handover_confirmed_at = None
    handoff.handover_failure_description = ""
    handoff.handover_failed_by = ""
    handoff.handover_failed_at = None
    handoff.completed_by = ""
    handoff.completed_at = None
    handoff.notes = reason[:500]
    handoff.generation = int(handoff.generation or 1) + 1
    handoff.flags.ignore_permissions = True
    handoff.save(ignore_permissions=True)
    frappe.db.commit()
    _log_reset("workflow_reset_command_center", actor, workflow, reset_id, reason)
    return {
        "success": True,
        "target": RESET_COMMAND_CENTER,
        "trainer_item": trainer_item,
        "handoff": handoff.name,
        "reset_id": reset_id,
        "superseded_meetings": superseded_meetings,
        "superseded_approvals": superseded_approvals,
        "superseded_supplier_files": superseded_supplier_files,
        "superseded_deadlines": superseded_deadlines,
        "superseded_ard_workflows": superseded_ard_workflows,
    }


def _supersede_command_center_downstream(trainer_item: str, reset_id: str) -> dict[str, int]:
    handoff = _active_handoff(trainer_item)
    if not handoff:
        return {"meetings": 0, "approvals": 0, "supplier_files": 0, "ard_workflows": _supersede_ard_workflows(trainer_item, reset_id)}
    return {
        "meetings": _supersede_meeting(getattr(handoff, "handover_meeting", ""), reset_id)
        + _supersede_related_meetings("BEDO Command Center Handoff", handoff.name, reset_id),
        "approvals": _supersede_approvals({"command_center_handoff": handoff.name}, reset_id),
        "supplier_files": _deactivate_supplier_files(handoff.name),
        "ard_workflows": _supersede_ard_workflows(trainer_item, reset_id),
    }


def _set_workflow_node_status(workflow, node_id: str, status: str, actor: str) -> None:
    import frappe

    state_name = frappe.db.get_value("SRS Workflow Node State", {"workflow_instance": workflow.name, "node_id": node_id}, "name")
    if not state_name:
        return
    values: dict[str, Any] = {"status": status, "last_action_by": actor, "overdue_at": None}
    if status != "COMPLETED":
        values.update({"started_at": None, "completed_at": None, "deadline_start_at": None, "deadline_due_at": None, "deadline_days": 0})
    frappe.db.set_value("SRS Workflow Node State", state_name, values, update_modified=False)


def reset_srs_to_action_paths(trainer_item: str, actor: str, *, reason: str = "") -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    workflow = _workflow_for_item(trainer_item)
    reset_id = f"RESET-SRS-ACTION-PATHS-{workflow.name}-{int(datetime.utcnow().timestamp())}"
    _supersede_command_center_downstream(trainer_item, reset_id)
    _supersede_approvals({"workflow_instance": workflow.name}, reset_id)
    _supersede_deadlines({"trainer_item": trainer_item})
    for node_id in [
        SRS_NODE_CASE_1,
        SRS_NODE_CASE_2,
        SRS_NODE_CASE_3,
        SRS_NODE_CASE_4,
        SRS_NODE_GATE_2_PMDP,
        SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
        SRS_NODE_PHYSICAL_BUILD_TEST,
        SRS_NODE_EXTENSION_DEADLINE,
        SRS_NODE_SRS_DIRECTOR_APPROVAL,
        SRS_NODE_PMDP,
        SRS_NODE_BMDP,
    ]:
        _set_workflow_node_status(workflow, node_id, "LOCKED", actor)
    workflow.status = "ACTION_PATHS_IN_PROGRESS"
    workflow.current_node = SRS_NODE_ACTION_PATHS
    workflow.pmdp_gate_path = ""
    workflow.pmdp_gate_submitted_by = ""
    workflow.pmdp_gate_submitted_at = None
    workflow.physical_build_started_at = None
    workflow.pmdp_path = ""
    workflow.pmdp_submitted_by = ""
    workflow.pmdp_submitted_at = None
    workflow.bmdp_path = ""
    workflow.completed_at = None
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"status": "SRS_IN_PROGRESS", "current_node": SRS_NODE_ACTION_PATHS, "current_responsible_user": workflow.project_owner or ""})
    frappe.db.commit()
    _log_reset("workflow_reset_srs_action_paths", actor, workflow, reset_id, reason)
    return {"success": True, "target": RESET_SRS_ACTION_PATHS, "trainer_item": trainer_item, "workflow": workflow.name, "reset_id": reset_id}


def reset_srs_to_coordination(trainer_item: str, actor: str, *, reason: str = "") -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    workflow = _workflow_for_item(trainer_item)
    reset_id = f"RESET-SRS-COORDINATION-{workflow.name}-{int(datetime.utcnow().timestamp())}"
    _supersede_command_center_downstream(trainer_item, reset_id)
    _supersede_approvals({"workflow_instance": workflow.name}, reset_id)
    _supersede_deadlines({"trainer_item": trainer_item})
    for row in frappe.get_all("SRS Deliverables Matrix", filters={"workflow_instance": workflow.name}, pluck="name"):
        frappe.db.set_value("SRS Deliverables Matrix", row, "status", SUPERSEDED_BY_RESET, update_modified=False)
    for row in frappe.get_all("SRS Item Team Member", filters={"workflow_instance": workflow.name, "is_project_owner": 0}, pluck="name"):
        frappe.delete_doc("SRS Item Team Member", row, ignore_permissions=True)
    for node_id in [
        SRS_NODE_DELIVERABLES,
        SRS_NODE_DUAL_GATE_APPROVAL,
        SRS_NODE_DEADLINE_LOCKED,
        SRS_NODE_ACTION_PATHS,
        SRS_NODE_CASE_1,
        SRS_NODE_CASE_2,
        SRS_NODE_CASE_3,
        SRS_NODE_CASE_4,
        SRS_NODE_GATE_2_PMDP,
        SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
        SRS_NODE_PHYSICAL_BUILD_TEST,
        SRS_NODE_EXTENSION_DEADLINE,
        SRS_NODE_SRS_DIRECTOR_APPROVAL,
        SRS_NODE_PMDP,
        SRS_NODE_BMDP,
    ]:
        _set_workflow_node_status(workflow, node_id, "LOCKED", actor)
    _set_workflow_node_status(workflow, SRS_NODE_COORDINATION, "IN_PROGRESS", actor)
    workflow.status = "COORDINATION_IN_PROGRESS"
    workflow.current_node = SRS_NODE_COORDINATION
    workflow.case_classification = ""
    workflow.deadline_proposal_days = 0
    workflow.approved_deadline_days = 0
    workflow.gm_approved_by = ""
    workflow.gm_approved_at = None
    workflow.srs_manager_approved_by = ""
    workflow.srs_manager_approved_at = None
    workflow.deadline_locked_at = None
    workflow.pmdp_gate_path = ""
    workflow.pmdp_gate_submitted_by = ""
    workflow.pmdp_gate_submitted_at = None
    workflow.physical_build_started_at = None
    workflow.pmdp_path = ""
    workflow.pmdp_submitted_by = ""
    workflow.pmdp_submitted_at = None
    workflow.bmdp_path = ""
    workflow.completed_at = None
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"status": "SRS_IN_PROGRESS", "current_node": SRS_NODE_COORDINATION, "current_responsible_user": workflow.project_owner or ""})
    frappe.db.commit()
    _log_reset("workflow_reset_srs_coordination", actor, workflow, reset_id, reason)
    return {"success": True, "target": RESET_SRS_COORDINATION, "trainer_item": trainer_item, "workflow": workflow.name, "reset_id": reset_id}


def execute_workflow_reset(trainer_item: str, target: str, actor: str, *, reason: str = "") -> dict[str, Any]:
    normalized = normalize_reset_target(target)
    if normalized == RESET_COMMAND_CENTER:
        return reset_command_center(trainer_item, actor, reason=reason)
    if normalized == RESET_SRS_ACTION_PATHS:
        return reset_srs_to_action_paths(trainer_item, actor, reason=reason)
    if normalized == RESET_SRS_COORDINATION:
        return reset_srs_to_coordination(trainer_item, actor, reason=reason)
    raise ValueError(f"Unsupported reset target: {target}")
