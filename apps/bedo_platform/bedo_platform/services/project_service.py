from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from bedo_platform.constants import (
    ARD_ROLES,
    CASE_CLASSIFICATIONS,
    COMMAND_CENTER_SRS_ARD_GM_APPROVAL,
    COMMAND_CENTER_WORKFLOW_TYPE,
    COMMAND_CENTER_ROLES,
    GLOBAL_DEADLINE_EXTENSION_APPROVAL,
    GLOBAL_VIEW_ROLES,
    GM_APPROVAL_CASES,
    NODE_STATUS_COMPLETED,
    NODE_STATUS_IN_PROGRESS,
    NODE_STATUS_LOCKED,
    NODE_STATUS_NOT_APPLICABLE,
    NODE_STATUS_READY,
    NODE_STATUS_WAITING_APPROVAL,
    SRS_FUNCTIONAL_NODES,
    SRS_NODE_ACTION_PATHS,
    SRS_NODE_BMDP,
    SRS_NODE_CASE_1,
    SRS_NODE_CASE_2,
    SRS_NODE_CASE_3,
    SRS_NODE_CASE_4,
    SRS_NODE_CASES_1_2,
    SRS_NODE_CASES_3_4,
    SRS_NODE_COMMAND_CENTER_APPROVAL,
    SRS_NODE_COORDINATION,
    SRS_NODE_DEADLINE_LOCKED,
    SRS_NODE_DELIVERABLES,
    SRS_NODE_DUAL_GATE_APPROVAL,
    SRS_NODE_EXTENSION_DEADLINE,
    SRS_NODE_FINAL_GM_APPROVAL,
    SRS_NODE_GATEWAY,
    SRS_NODE_GATE_2_PMDP,
    SRS_NODE_GM_APPROVAL,
    SRS_NODE_MANAGER_APPROVAL,
    SRS_NODE_PHYSICAL_BUILD_TEST,
    SRS_NODE_PMDP,
    SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
    SRS_NODE_PRODUCT_DIGITAL_RELEASE,
    SRS_NODE_SRS_DIRECTOR_APPROVAL,
    SRS_PLACEHOLDER_NODES,
    SRS_ROLES,
    SRS_WORKFLOW_TYPE,
    SUPPLIER_DEADLINE_EXTENSION_APPROVAL,
    SUPPLIERS_WORKFLOW_TYPE,
)
from bedo_platform.services.deadline_service import (
    complete_deadlines,
    create_deadline,
    deadline_quantity_label,
    deadline_unit_label,
    extend_active_deadline,
    extend_deadline_by_name,
    get_deadlines_for_trainer_item,
    server_now_iso,
    to_cairo_iso,
)
from bedo_platform.services.notification_service import notify_many, project_action_url
from bedo_platform.services.security_audit_service import log_security_event
from bedo_platform.services.user_profile_service import assert_user_can_login

PROJECT_STATUS_DRAFT = "DRAFT"
PROJECT_STATUS_DETAILS_FINALIZED = "DETAILS_FINALIZED"
PROJECT_STATUS_RELEASED_TO_SRS = "RELEASED_TO_SRS"
PROJECT_STATUS_IN_SRS = "IN_SRS"

ITEM_STATUS_DRAFT = "DRAFT"
ITEM_STATUS_RELEASED = "RELEASED_TO_SRS"
ITEM_STATUS_SRS_IN_PROGRESS = "SRS_IN_PROGRESS"
ITEM_STATUS_SRS_COMPLETE = "SRS_COMPLETE"

STATE_GATEWAY = "SRS_GATEWAY_IN_PROGRESS"
STATE_OWNER_ASSIGNED = "PROJECT_OWNER_ASSIGNED"
STATE_COORDINATION = "COORDINATION_IN_PROGRESS"
STATE_DELIVERABLES = "DELIVERABLES_SUBMITTED"
STATE_WAITING_GM = "WAITING_GM_APPROVAL"
STATE_WAITING_MANAGER = "WAITING_SRS_MANAGER_APPROVAL"
STATE_DEADLINE_LOCKED = "DEADLINE_LOCKED"
STATE_ACTION_PATHS = "ACTION_PATHS_IN_PROGRESS"
STATE_GATE_2_PMDP = "GATE_2_PMDP_IN_PROGRESS"
STATE_WAITING_PMDP_DUAL_GATE = "WAITING_PMDP_DUAL_GATE_APPROVAL"
STATE_PHYSICAL_BUILD = "PHYSICAL_BUILD_IN_PROGRESS"
STATE_WAITING_EXTENSION_APPROVAL = "WAITING_EXTENSION_APPROVAL"
STATE_PMDP_READY = "PMDP_IN_PROGRESS"
STATE_COMMAND_CENTER_APPROVAL = "COMMAND_CENTER_APPROVAL_IN_PROGRESS"
STATE_WAITING_FINAL_GM = "WAITING_FINAL_GM_APPROVAL"
STATE_COMPLETE = "SRS_COMPLETE"

CASE_1 = "Case 1 - Legacy Validation"
CASE_2 = "Case 2 - Standard Innovation"
CASE_3 = "Case 3 - Experimental Prototyping"
CASE_4 = "Case 4 - Vanguard Manufacturing"

COMMAND_CENTER_CASES = {
    "Case 1 - Save for later": "Save for later",
    "Case 2 - Buy Critical Components then deliver to ARD": "Buy Critical Components then deliver to ARD",
    "Case 3 - Deliver to ARD directly": "Deliver to ARD directly",
}

COMMAND_CENTER_CASE_1 = "Case 1 - Save for later"
COMMAND_CENTER_CASE_2 = "Case 2 - Buy Critical Components then deliver to ARD"
COMMAND_CENTER_CASE_3 = "Case 3 - Deliver to ARD directly"
COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD = "SRS_TO_ARD"
COMMAND_CENTER_HANDOFF_PENDING = "PENDING_COMMAND_CENTER"
COMMAND_CENTER_HANDOFF_WAITING_GM = "WAITING_GM_APPROVAL"
COMMAND_CENTER_HANDOFF_IN_PROGRESS = "COMMAND_CENTER_IN_PROGRESS"
COMMAND_CENTER_HANDOFF_ROUTED_TO_SUPPLIERS = "ROUTED_TO_SUPPLIERS"
COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_PENDING = "HANDOVER_MEETING_PENDING"
COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_SCHEDULED = "HANDOVER_MEETING_SCHEDULED"
COMMAND_CENTER_HANDOFF_HANDOVER_CONFIRMATION_PENDING = "HANDOVER_CONFIRMATION_PENDING"
COMMAND_CENTER_HANDOFF_HANDOVER_FAILED_WAITING_GM = "HANDOVER_FAILED_WAITING_GM"
COMMAND_CENTER_HANDOFF_READY_FOR_ARD = "READY_FOR_ARD"
COMMAND_CENTER_HANDOFF_COMPLETED = "COMPLETED"
SUPPLIER_FILE_IN_PROGRESS = "IN_PROGRESS"
SUPPLIER_FILE_WAITING_EXTENSION = "WAITING_EXTENSION_APPROVAL"
SUPPLIER_FILE_OVERDUE = "OVERDUE"
SUPPLIER_FILE_COMPLETED = "COMPLETED"
COMMAND_CENTER_CASE_1_NODE = "COMMAND_CENTER_CASE_1"
SUPPLIER_CASE_2_NODE = "SUPPLIER_CASE_2_DELIVERY"
HANDOVER_FAILURE_GM_APPROVAL = "HANDOVER_FAILURE_GM_APPROVAL"
ARD_INTERRUPTION_GM_APPROVAL = "ARD_INTERRUPTION_GM_APPROVAL"


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)

SRS_FLOWCHART_NODE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": SRS_NODE_PRODUCT_DIGITAL_RELEASE,
        "label": "Product Digital Release",
        "lane": "operations",
        "column": "deadline_1",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [],
    },
    {
        "id": SRS_NODE_GATEWAY,
        "label": "SRS Gateway",
        "lane": "srs_entry",
        "column": "deadline_1",
        "kind": "action",
        "clickable": True,
        "requiredRoles": ["SRS Manager"],
        "requiredPreviousNodes": [SRS_NODE_PRODUCT_DIGITAL_RELEASE],
    },
    {
        "id": SRS_NODE_COORDINATION,
        "label": "Mandatory Coordination Meeting",
        "lane": "study_phase",
        "column": "deadline_2",
        "kind": "action",
        "clickable": True,
        "requiredPreviousNodes": [SRS_NODE_GATEWAY],
    },
    {
        "id": SRS_NODE_DELIVERABLES,
        "label": "Deliverables Submission",
        "lane": "study_phase",
        "column": "deadline_2",
        "kind": "action",
        "clickable": True,
        "requiredPreviousNodes": [SRS_NODE_COORDINATION],
    },
    {
        "id": SRS_NODE_DUAL_GATE_APPROVAL,
        "label": "Dual Gate Approval",
        "lane": "study_phase",
        "column": "deadline_2",
        "kind": "approval",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_DELIVERABLES],
    },
    {
        "id": SRS_NODE_DEADLINE_LOCKED,
        "label": "Deadline Locked in ERP",
        "lane": "study_phase",
        "column": "deadline_2",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_DUAL_GATE_APPROVAL],
    },
    {
        "id": SRS_NODE_ACTION_PATHS,
        "label": "Action Paths",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_DEADLINE_LOCKED],
    },
    {
        "id": SRS_NODE_CASE_1,
        "label": "Case 1",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_ACTION_PATHS],
    },
    {
        "id": SRS_NODE_CASE_2,
        "label": "Case 2",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_ACTION_PATHS],
    },
    {
        "id": SRS_NODE_CASE_3,
        "label": "Case 3",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_ACTION_PATHS],
    },
    {
        "id": SRS_NODE_CASE_4,
        "label": "Case 4",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_ACTION_PATHS],
    },
    {
        "id": SRS_NODE_GATE_2_PMDP,
        "label": "Gate 2 PMDP",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "input",
        "clickable": True,
        "requiredPreviousNodes": [SRS_NODE_CASE_3],
    },
    {
        "id": SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
        "label": "Dual Gate Approval (SRS + Pillar 4)",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "approval",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_GATE_2_PMDP],
    },
    {
        "id": SRS_NODE_PHYSICAL_BUILD_TEST,
        "label": "Physical Build & Test",
        "lane": "study_phase",
        "column": "deadline_4",
        "kind": "action",
        "clickable": True,
        "requiredPreviousNodes": [SRS_NODE_PMDP_DUAL_GATE_APPROVAL],
    },
    {
        "id": SRS_NODE_EXTENSION_DEADLINE,
        "label": "Extension Deadline",
        "lane": "study_phase",
        "column": "deadline_4",
        "kind": "action",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_PHYSICAL_BUILD_TEST],
    },
    {
        "id": SRS_NODE_SRS_DIRECTOR_APPROVAL,
        "label": "SRS Director Approval",
        "lane": "study_phase",
        "column": "deadline_4",
        "kind": "approval",
        "clickable": False,
        "requiredRoles": ["SRS Manager"],
        "requiredPreviousNodes": [SRS_NODE_EXTENSION_DEADLINE],
    },
    {
        "id": SRS_NODE_PMDP,
        "label": "PMDP",
        "lane": "study_phase",
        "column": "deadline_4",
        "kind": "input",
        "clickable": True,
        "requiredPreviousNodes": [SRS_NODE_PHYSICAL_BUILD_TEST],
    },
    {
        "id": SRS_NODE_BMDP,
        "label": "BMDP",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "input",
        "clickable": True,
        "requiredPreviousNodes": [SRS_NODE_DUAL_GATE_APPROVAL, SRS_NODE_DEADLINE_LOCKED, SRS_NODE_ACTION_PATHS, SRS_NODE_PMDP],
    },
]

SRS_FLOWCHART_EDGES = [
    [SRS_NODE_PRODUCT_DIGITAL_RELEASE, SRS_NODE_GATEWAY],
    [SRS_NODE_GATEWAY, SRS_NODE_COORDINATION],
    [SRS_NODE_COORDINATION, SRS_NODE_DELIVERABLES],
    [SRS_NODE_DELIVERABLES, SRS_NODE_DUAL_GATE_APPROVAL],
    [SRS_NODE_DUAL_GATE_APPROVAL, SRS_NODE_DEADLINE_LOCKED],
    [SRS_NODE_DEADLINE_LOCKED, SRS_NODE_ACTION_PATHS],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_1],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_2],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_3],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_4],
    [SRS_NODE_CASE_1, SRS_NODE_BMDP],
    [SRS_NODE_CASE_2, SRS_NODE_BMDP],
    [SRS_NODE_CASE_4, SRS_NODE_BMDP],
    [SRS_NODE_CASE_3, SRS_NODE_GATE_2_PMDP],
    [SRS_NODE_GATE_2_PMDP, SRS_NODE_PMDP_DUAL_GATE_APPROVAL],
    [SRS_NODE_PMDP_DUAL_GATE_APPROVAL, SRS_NODE_PHYSICAL_BUILD_TEST],
    [SRS_NODE_PHYSICAL_BUILD_TEST, SRS_NODE_EXTENSION_DEADLINE],
    [SRS_NODE_EXTENSION_DEADLINE, SRS_NODE_SRS_DIRECTOR_APPROVAL],
    [SRS_NODE_SRS_DIRECTOR_APPROVAL, SRS_NODE_PHYSICAL_BUILD_TEST],
    [SRS_NODE_PHYSICAL_BUILD_TEST, SRS_NODE_PMDP],
    [SRS_NODE_PMDP, SRS_NODE_BMDP],
]


def _roles(user: str) -> set[str]:
    import frappe

    return set(frappe.get_roles(user))


def _require_role(user: str, role: str) -> None:
    import frappe

    if role not in _roles(user):
        frappe.throw(f"{role} access is required.", frappe.PermissionError)


def _is_gm(user: str) -> bool:
    return "General Manager" in _roles(user)


def _is_global_viewer(user: str) -> bool:
    return bool(_roles(user) & GLOBAL_VIEW_ROLES)


def _is_srs_manager(user: str) -> bool:
    return "SRS Manager" in _roles(user)


def _is_srs_user(user: str) -> bool:
    return bool(_roles(user) & SRS_ROLES)


def _is_command_center_representative(user: str) -> bool:
    return bool(_roles(user) & COMMAND_CENTER_ROLES)


def _is_ard_user(user: str) -> bool:
    return bool(_roles(user) & ARD_ROLES)


def _require_gm(user: str) -> None:
    _require_role(user, "General Manager")


def _primary_department_key(user: str) -> str:
    import frappe

    department = frappe.db.get_value(
        "BEDO User Role Assignment",
        {"user": user, "is_primary_department": 1, "is_active": 1},
        "department",
    )
    if not department:
        return ""
    return frappe.db.get_value("BEDO Department", department, "department_key") or ""


def _safe_user_row(user: str) -> dict[str, str]:
    import frappe

    doc = frappe.get_doc("User", user)
    roles = [role for role in frappe.get_roles(user) if role in {"General Manager", *SRS_ROLES}]
    department_key = _primary_department_key(user)
    department = frappe.db.get_value("BEDO Department", {"department_key": department_key}, "department_name") or department_key
    return {
        "user": user,
        "username": doc.username or user,
        "first_name": doc.first_name or "",
        "last_name": doc.last_name or "",
        "full_name": " ".join(part for part in [doc.first_name, doc.last_name] if part) or doc.username or user,
        "email": doc.email or "",
        "department_key": department_key,
        "department": department,
        "business_role": roles[0] if roles else "",
    }


def _user_full_name(user: str | None) -> str:
    if not user:
        return ""
    try:
        return _safe_user_row(user)["full_name"]
    except Exception:
        return user or ""


def _active_users_with_role(role: str) -> list[str]:
    import frappe

    users = []
    for row in frappe.get_all("Has Role", filters={"role": role}, fields=["parent"]):
        if row.parent not in {"Administrator", "Guest"} and assert_user_can_login(row.parent):
            users.append(row.parent)
    return sorted(set(users))


def _active_users_in_departments(department_keys: set[str]) -> list[str]:
    import frappe

    result = []
    for row in frappe.get_all("User", filters={"enabled": 1}, fields=["name"]):
        if row.name in {"Administrator", "Guest"} or not assert_user_can_login(row.name):
            continue
        if _primary_department_key(row.name) in department_keys:
            result.append(row.name)
    return sorted(set(result))


def _project_or_throw(project: str):
    import frappe

    if not frappe.db.exists("BEDO Project", project):
        frappe.throw("Project not found.", frappe.DoesNotExistError)
    return frappe.get_doc("BEDO Project", project)


def _item_or_throw(trainer_item: str):
    import frappe

    if not frappe.db.exists("BEDO Trainer Item", trainer_item):
        frappe.throw("Trainer item not found.", frappe.DoesNotExistError)
    return frappe.get_doc("BEDO Trainer Item", trainer_item)


def _workflow_for_item(trainer_item: str):
    import frappe

    name = frappe.db.get_value("SRS Workflow Instance", {"trainer_item": trainer_item}, "name")
    if not name:
        frappe.throw("SRS workflow has not started for this trainer item.", frappe.DoesNotExistError)
    return frappe.get_doc("SRS Workflow Instance", name)


def _ensure_command_center_handoff(workflow, *, actor: str, notify: bool = False):
    import frappe

    name = frappe.db.get_value(
        "BEDO Command Center Handoff",
        {
            "srs_workflow_instance": workflow.name,
            "trainer_item": workflow.trainer_item,
            "handoff_type": COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
            "is_active": 1,
        },
        "name",
    )
    if name:
        return frappe.get_doc("BEDO Command Center Handoff", name)

    doc = frappe.get_doc(
        {
            "doctype": "BEDO Command Center Handoff",
            "project": workflow.project,
            "trainer_item": workflow.trainer_item,
            "srs_workflow_instance": workflow.name,
            "handoff_type": COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
            "status": COMMAND_CENTER_HANDOFF_PENDING,
            "submitted_by": actor,
            "submitted_at": _utcnow(),
            "is_active": 1,
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    if notify:
        notify_many(
            _active_users_with_role("Command Center Representative"),
            title="SRS to ARD handoff ready",
            message="BMDP is complete. Command Center decision is required for the SRS to ARD handoff.",
            notification_type="COMMAND_CENTER_HANDOFF_READY",
            project=workflow.project,
            trainer_item=workflow.trainer_item,
            workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
            node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
            action_url=project_action_url("command-center", workflow.project, workflow.trainer_item),
            priority="High",
        )
    _log_workflow(
        "command_center_handoff_created",
        actor,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
    )
    return doc


def _handoff_for_item(trainer_item: str):
    import frappe

    name = frappe.db.get_value(
        "BEDO Command Center Handoff",
        {"trainer_item": trainer_item, "handoff_type": COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD, "is_active": 1},
        "name",
    )
    return frappe.get_doc("BEDO Command Center Handoff", name) if name else None


def _handoff_or_throw(handoff: str):
    import frappe

    if not handoff or not frappe.db.exists("BEDO Command Center Handoff", handoff):
        frappe.throw("Command Center handoff not found.", frappe.DoesNotExistError)
    return frappe.get_doc("BEDO Command Center Handoff", handoff)


def _supplier_file_or_throw(supplier_file: str):
    import frappe

    if not supplier_file or not frappe.db.exists("BEDO Supplier File", supplier_file):
        frappe.throw("Supplier file not found.", frappe.DoesNotExistError)
    return frappe.get_doc("BEDO Supplier File", supplier_file)


def _node_state(workflow: str, node_id: str):
    import frappe

    name = frappe.db.get_value("SRS Workflow Node State", {"workflow_instance": workflow, "node_id": node_id}, "name")
    return frappe.get_doc("SRS Workflow Node State", name) if name else None


def _set_node_state(
    workflow,
    node_id: str,
    status: str,
    *,
    actor: str,
    responsible_user: str = "",
    deadline: dict[str, Any] | None = None,
) -> str:
    import frappe

    doc = _node_state(workflow.name, node_id)
    if not doc:
        doc = frappe.new_doc("SRS Workflow Node State")
        doc.workflow_instance = workflow.name
        doc.project = workflow.project
        doc.trainer_item = workflow.trainer_item
        doc.node_id = node_id
    previous_status = doc.status
    if status == NODE_STATUS_IN_PROGRESS and previous_status != NODE_STATUS_IN_PROGRESS:
        doc.started_at = _utcnow()
    if status == NODE_STATUS_COMPLETED and previous_status != NODE_STATUS_COMPLETED:
        doc.completed_at = _utcnow()
    elif status != NODE_STATUS_COMPLETED and previous_status == NODE_STATUS_COMPLETED:
        doc.completed_at = None
    doc.status = status
    doc.responsible_user = responsible_user or doc.responsible_user
    doc.last_action_by = actor
    if deadline:
        doc.deadline_start_at = deadline.get("start_at")
        doc.deadline_due_at = deadline.get("due_at")
        doc.deadline_days = deadline.get("deadline_days")
    doc.flags.ignore_permissions = True
    if doc.name:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    return doc.name


def _log(event_type: str, actor: str, *, project: str = "", trainer_item: str = "", node_id: str = "", message: str = "", target_user: str = "") -> None:
    log_security_event(
        event_type,
        user=actor,
        target_user=target_user or None,
        project=project or None,
        trainer_item=trainer_item or None,
        workflow_type=SRS_WORKFLOW_TYPE if trainer_item or node_id else None,
        node_id=node_id or None,
        status="Success",
        message=message,
    )


def _log_workflow(
    event_type: str,
    actor: str,
    *,
    workflow_type: str,
    project: str = "",
    trainer_item: str = "",
    node_id: str = "",
    message: str = "",
    target_user: str = "",
) -> None:
    log_security_event(
        event_type,
        user=actor,
        target_user=target_user or None,
        project=project or None,
        trainer_item=trainer_item or None,
        workflow_type=workflow_type,
        node_id=node_id or None,
        status="Success",
        message=message,
    )


def _audit_invalid_transition_attempt(actor: str, workflow, node_id: str, message: str) -> None:
    log_security_event(
        "invalid_srs_transition_attempt",
        user=actor,
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        workflow_type=SRS_WORKFLOW_TYPE,
        node_id=node_id,
        status="Failure",
        message=message,
    )


def _node_display_label(node_id: str) -> str:
    definition = next((node for node in SRS_FLOWCHART_NODE_DEFINITIONS if node["id"] == node_id), None)
    if definition:
        return str(definition.get("label") or node_id)
    return node_id.replace("_", " ").title()


def _node_status(workflow, node_id: str) -> str:
    state = _node_state(workflow.name, node_id)
    return state.status if state else NODE_STATUS_LOCKED


def _node_completed(workflow, node_id: str) -> bool:
    return _node_status(workflow, node_id) == NODE_STATUS_COMPLETED


def _backfill_completed_srs_terminal_nodes(workflow) -> None:
    if not workflow or workflow.status != STATE_COMPLETE or not _node_completed(workflow, SRS_NODE_BMDP):
        return
    actor = workflow.get("gm_approved_by") or workflow.get("srs_manager_approved_by") or workflow.get("project_owner") or "Administrator"
    if workflow.current_node in {SRS_NODE_COMMAND_CENTER_APPROVAL, SRS_NODE_FINAL_GM_APPROVAL}:
        import frappe

        workflow.current_node = SRS_NODE_BMDP
        workflow.updated_at = _utcnow()
        workflow.flags.ignore_permissions = True
        workflow.save(ignore_permissions=True)
        frappe.db.set_value(
            "BEDO Trainer Item",
            workflow.trainer_item,
            {"current_node": SRS_NODE_BMDP, "status": ITEM_STATUS_SRS_COMPLETE},
        )
    _ensure_command_center_handoff(workflow, actor=actor, notify=False)


def _assert_node_completed(workflow, node_id: str, actor: str, target_node: str) -> None:
    import frappe

    if not _node_completed(workflow, node_id):
        message = f"{_node_display_label(node_id)} must be complete before {_node_display_label(target_node)}."
        _audit_invalid_transition_attempt(actor, workflow, target_node, message)
        frappe.throw(message, frappe.PermissionError)


def _assert_node_status(workflow, node_id: str, statuses: set[str], actor: str) -> None:
    import frappe

    current = _node_status(workflow, node_id)
    if current not in statuses:
        message = f"{_node_display_label(node_id)} is not available for this action."
        _audit_invalid_transition_attempt(actor, workflow, node_id, message)
        frappe.throw(message, frappe.PermissionError)


def _assert_current_node(workflow, node_id: str, actor: str) -> None:
    import frappe

    if workflow.current_node != node_id:
        message = f"{_node_display_label(node_id)} is not the active SRS step."
        _audit_invalid_transition_attempt(actor, workflow, node_id, message)
        frappe.throw(message, frappe.PermissionError)


def _case_node_id(case_classification: str) -> str:
    return {
        CASE_1: SRS_NODE_CASE_1,
        CASE_2: SRS_NODE_CASE_2,
        CASE_3: SRS_NODE_CASE_3,
        CASE_4: SRS_NODE_CASE_4,
    }.get(case_classification, "")


def _case_group_node_id(case_classification: str) -> str:
    return SRS_NODE_CASES_3_4 if case_classification in {CASE_3, CASE_4} else SRS_NODE_CASES_1_2


def _case_path_statuses(
    case_classification: str,
    status: str = NODE_STATUS_IN_PROGRESS,
    *,
    path_group_case_classification: str | None = None,
    include_gm_not_applicable: bool = True,
) -> dict[str, str]:
    selected_group = _case_group_node_id(path_group_case_classification or case_classification)
    selected_case = _case_node_id(case_classification)
    statuses = {
        node_id: NODE_STATUS_NOT_APPLICABLE
        for node_id in [
            SRS_NODE_CASES_1_2,
            SRS_NODE_CASES_3_4,
            SRS_NODE_CASE_1,
            SRS_NODE_CASE_2,
            SRS_NODE_CASE_3,
            SRS_NODE_CASE_4,
        ]
    }
    for node_id in {selected_group, selected_case}:
        if node_id:
            statuses[node_id] = status
    if include_gm_not_applicable and case_classification not in GM_APPROVAL_CASES:
        statuses[SRS_NODE_GM_APPROVAL] = NODE_STATUS_NOT_APPLICABLE
    return statuses


def _set_post_deadline_case_states(workflow, case_classification: str, actor: str) -> None:
    path_group_case = _existing_case_path_group_case(workflow, case_classification)
    selected_group = _case_group_node_id(path_group_case)
    selected_case = _case_node_id(case_classification)
    for node_id in [SRS_NODE_CASES_1_2, SRS_NODE_CASES_3_4, SRS_NODE_CASE_1, SRS_NODE_CASE_2, SRS_NODE_CASE_3, SRS_NODE_CASE_4]:
        status = NODE_STATUS_NOT_APPLICABLE
        if node_id == selected_group:
            status = NODE_STATUS_COMPLETED
        elif node_id == selected_case:
            status = NODE_STATUS_IN_PROGRESS
        _set_node_state(workflow, node_id, status, actor=actor)


def _set_completed_case_states(workflow, case_classification: str, actor: str) -> None:
    path_group_case = _existing_case_path_group_case(workflow, case_classification)
    selected_group = _case_group_node_id(path_group_case)
    selected_case = _case_node_id(case_classification)
    for node_id in [SRS_NODE_CASES_1_2, SRS_NODE_CASES_3_4, SRS_NODE_CASE_1, SRS_NODE_CASE_2, SRS_NODE_CASE_3, SRS_NODE_CASE_4]:
        status = NODE_STATUS_NOT_APPLICABLE
        if node_id in {selected_group, selected_case}:
            status = NODE_STATUS_COMPLETED
        _set_node_state(workflow, node_id, status, actor=actor)


def _set_single_case_state(workflow, case_classification: str, actor: str, status: str) -> None:
    selected_case = _case_node_id(case_classification)
    for node_id in [SRS_NODE_CASE_1, SRS_NODE_CASE_2, SRS_NODE_CASE_3, SRS_NODE_CASE_4]:
        _set_node_state(workflow, node_id, status if node_id == selected_case else NODE_STATUS_NOT_APPLICABLE, actor=actor)


def _start_post_dual_gate_path(workflow, actor: str, deadline_units: int) -> None:
    import frappe

    _set_node_state(workflow, SRS_NODE_DUAL_GATE_APPROVAL, NODE_STATUS_COMPLETED, actor=actor)
    _set_node_state(workflow, SRS_NODE_DEADLINE_LOCKED, NODE_STATUS_COMPLETED, actor=actor)
    _set_node_state(workflow, SRS_NODE_ACTION_PATHS, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_single_case_state(workflow, workflow.case_classification, actor, NODE_STATUS_IN_PROGRESS)

    workflow.deadline_locked_at = _utcnow()
    workflow.updated_at = workflow.deadline_locked_at
    next_node = SRS_NODE_BMDP
    responsible = workflow.project_owner
    if workflow.case_classification == CASE_3:
        deadline = create_deadline(
            project=workflow.project,
            trainer_item=workflow.trainer_item,
            workflow_type=SRS_WORKFLOW_TYPE,
            node_id=SRS_NODE_CASE_3,
            triggered_by=actor,
            deadline_days=deadline_units,
        )
        _set_node_state(workflow, SRS_NODE_CASE_3, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner, deadline=deadline)
        _set_node_state(workflow, SRS_NODE_GATE_2_PMDP, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner)
        _set_node_state(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, NODE_STATUS_LOCKED, actor=actor)
        _set_node_state(workflow, SRS_NODE_PHYSICAL_BUILD_TEST, NODE_STATUS_LOCKED, actor=actor)
        _set_node_state(workflow, SRS_NODE_EXTENSION_DEADLINE, NODE_STATUS_LOCKED, actor=actor)
        _set_node_state(workflow, SRS_NODE_SRS_DIRECTOR_APPROVAL, NODE_STATUS_LOCKED, actor=actor)
        _set_node_state(workflow, SRS_NODE_PMDP, NODE_STATUS_LOCKED, actor=actor)
        _set_node_state(workflow, SRS_NODE_BMDP, NODE_STATUS_LOCKED, actor=actor, responsible_user=workflow.project_owner)
        workflow.status = STATE_GATE_2_PMDP
        next_node = SRS_NODE_GATE_2_PMDP
    else:
        deadline = create_deadline(
            project=workflow.project,
            trainer_item=workflow.trainer_item,
            workflow_type=SRS_WORKFLOW_TYPE,
            node_id=SRS_NODE_BMDP,
            triggered_by=actor,
            deadline_days=deadline_units,
        )
        _set_node_state(workflow, SRS_NODE_BMDP, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner, deadline=deadline)
        for node_id in [
            SRS_NODE_GATE_2_PMDP,
            SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
            SRS_NODE_PHYSICAL_BUILD_TEST,
            SRS_NODE_EXTENSION_DEADLINE,
            SRS_NODE_SRS_DIRECTOR_APPROVAL,
            SRS_NODE_PMDP,
        ]:
            _set_node_state(workflow, node_id, NODE_STATUS_NOT_APPLICABLE, actor=actor)
        workflow.status = STATE_ACTION_PATHS

    workflow.current_node = next_node
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value(
        "BEDO Trainer Item",
        workflow.trainer_item,
        {"current_node": next_node, "current_responsible_user": responsible},
    )
    notify_many(
        [workflow.project_owner],
        title="Case 3 deadline locked" if workflow.case_classification == CASE_3 else "BMDP deadline locked",
        message=f"The approved deadline is locked at {deadline_quantity_label(deadline_units)}.",
        notification_type="DEADLINE_LOCKED",
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        node_id=next_node,
        action_url=project_action_url("srs", workflow.project, workflow.trainer_item),
        priority="High",
    )


def _reset_pmdp_gate_for_denial(workflow, actor: str, message: str = "") -> None:
    import frappe

    workflow.pmdp_gate_path = ""
    workflow.pmdp_gate_submitted_by = ""
    workflow.pmdp_gate_submitted_at = None
    workflow.status = STATE_GATE_2_PMDP
    workflow.current_node = SRS_NODE_GATE_2_PMDP
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_GATE_2_PMDP, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner)
    _set_node_state(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, NODE_STATUS_LOCKED, actor=actor)
    frappe.db.set_value(
        "BEDO Trainer Item",
        workflow.trainer_item,
        {"current_node": SRS_NODE_GATE_2_PMDP, "current_responsible_user": workflow.project_owner},
    )
    notify_many(
        [workflow.project_owner],
        title="PMDP gate denied",
        message=message or "The PMDP path was denied. Submit the updated PMDP path again.",
        notification_type="PMDP_GATE_DENIED",
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        node_id=SRS_NODE_GATE_2_PMDP,
        action_url=project_action_url("srs", workflow.project, workflow.trainer_item),
        priority="High",
    )


def _existing_case_path_group_case(workflow, default_case_classification: str) -> str:
    cases_1_2_status = _node_status(workflow, SRS_NODE_CASES_1_2)
    cases_3_4_status = _node_status(workflow, SRS_NODE_CASES_3_4)
    if cases_1_2_status != NODE_STATUS_NOT_APPLICABLE and cases_3_4_status == NODE_STATUS_NOT_APPLICABLE:
        return CASE_1
    if cases_3_4_status != NODE_STATUS_NOT_APPLICABLE and cases_1_2_status == NODE_STATUS_NOT_APPLICABLE:
        return CASE_3
    return default_case_classification


def _set_case_path_states(
    workflow,
    case_classification: str,
    actor: str,
    status: str = NODE_STATUS_IN_PROGRESS,
    *,
    path_group_case_classification: str | None = None,
    include_gm_not_applicable: bool = True,
) -> None:
    for node_id, next_status in _case_path_statuses(
        case_classification,
        status,
        path_group_case_classification=path_group_case_classification,
        include_gm_not_applicable=include_gm_not_applicable,
    ).items():
        _set_node_state(workflow, node_id, next_status, actor=actor)


def _assert_transition_prerequisites(action: str, workflow, actor: str) -> None:
    import frappe

    if action == "assign_owner":
        _assert_node_completed(workflow, SRS_NODE_PRODUCT_DIGITAL_RELEASE, actor, SRS_NODE_GATEWAY)
        _assert_current_node(workflow, SRS_NODE_GATEWAY, actor)
        _assert_node_status(workflow, SRS_NODE_GATEWAY, {NODE_STATUS_IN_PROGRESS}, actor)
        return

    if action == "select_team":
        _assert_node_completed(workflow, SRS_NODE_GATEWAY, actor, SRS_NODE_COORDINATION)
        _assert_current_node(workflow, SRS_NODE_COORDINATION, actor)
        _assert_node_status(workflow, SRS_NODE_COORDINATION, {NODE_STATUS_IN_PROGRESS}, actor)
        return

    if action == "submit_deliverables":
        _assert_node_completed(workflow, SRS_NODE_COORDINATION, actor, SRS_NODE_DELIVERABLES)
        _assert_current_node(workflow, SRS_NODE_DELIVERABLES, actor)
        _assert_node_status(workflow, SRS_NODE_DELIVERABLES, {NODE_STATUS_IN_PROGRESS}, actor)
        return

    if action == "gm_approve":
        _assert_node_completed(workflow, SRS_NODE_DELIVERABLES, actor, SRS_NODE_DUAL_GATE_APPROVAL)
        if not workflow.srs_manager_approved_at:
            message = "SRS Manager approval must be complete before GM dual gate approval."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_DUAL_GATE_APPROVAL, message)
            frappe.throw(message, frappe.PermissionError)
        if workflow.case_classification not in GM_APPROVAL_CASES:
            message = "GM dual gate approval is only required for Case 3 or Case 4."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_DUAL_GATE_APPROVAL, message)
            frappe.throw(message, frappe.PermissionError)
        _assert_current_node(workflow, SRS_NODE_DUAL_GATE_APPROVAL, actor)
        _assert_node_status(workflow, SRS_NODE_DUAL_GATE_APPROVAL, {NODE_STATUS_WAITING_APPROVAL}, actor)
        return

    if action == "manager_approve":
        _assert_node_completed(workflow, SRS_NODE_DELIVERABLES, actor, SRS_NODE_DUAL_GATE_APPROVAL)
        _assert_current_node(workflow, SRS_NODE_DUAL_GATE_APPROVAL, actor)
        _assert_node_status(workflow, SRS_NODE_DUAL_GATE_APPROVAL, {NODE_STATUS_WAITING_APPROVAL}, actor)
        return

    if action == "submit_pmdp_gate":
        _assert_node_completed(workflow, SRS_NODE_DUAL_GATE_APPROVAL, actor, SRS_NODE_GATE_2_PMDP)
        if workflow.case_classification != CASE_3:
            message = "Gate 2 PMDP is only available for Case 3."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_GATE_2_PMDP, message)
            frappe.throw(message, frappe.PermissionError)
        _assert_current_node(workflow, SRS_NODE_GATE_2_PMDP, actor)
        _assert_node_status(workflow, SRS_NODE_GATE_2_PMDP, {NODE_STATUS_IN_PROGRESS}, actor)
        return

    if action == "pmdp_dual_gate_approve":
        _assert_node_completed(workflow, SRS_NODE_GATE_2_PMDP, actor, SRS_NODE_PMDP_DUAL_GATE_APPROVAL)
        _assert_current_node(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, actor)
        _assert_node_status(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, {NODE_STATUS_WAITING_APPROVAL}, actor)
        return

    if action == "request_pmdp_extension":
        if workflow.case_classification != CASE_3:
            message = "Extension requests are only available for Case 3 physical build."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_EXTENSION_DEADLINE, message)
            frappe.throw(message, frappe.PermissionError)
        _assert_node_completed(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, actor, SRS_NODE_EXTENSION_DEADLINE)
        _assert_node_status(workflow, SRS_NODE_PHYSICAL_BUILD_TEST, {NODE_STATUS_IN_PROGRESS}, actor)
        _assert_node_status(workflow, SRS_NODE_PMDP, {NODE_STATUS_IN_PROGRESS}, actor)
        return

    if action == "extension_approve":
        _assert_node_status(workflow, SRS_NODE_EXTENSION_DEADLINE, {NODE_STATUS_IN_PROGRESS}, actor)
        _assert_current_node(workflow, SRS_NODE_SRS_DIRECTOR_APPROVAL, actor)
        _assert_node_status(workflow, SRS_NODE_SRS_DIRECTOR_APPROVAL, {NODE_STATUS_WAITING_APPROVAL}, actor)
        return

    if action == "submit_pmdp":
        if workflow.case_classification != CASE_3:
            message = "PMDP submission is only available for Case 3."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_PMDP, message)
            frappe.throw(message, frappe.PermissionError)
        _assert_node_completed(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, actor, SRS_NODE_PMDP)
        _assert_node_status(workflow, SRS_NODE_PHYSICAL_BUILD_TEST, {NODE_STATUS_IN_PROGRESS}, actor)
        _assert_current_node(workflow, SRS_NODE_PMDP, actor)
        _assert_node_status(workflow, SRS_NODE_PMDP, {NODE_STATUS_IN_PROGRESS}, actor)
        return

    if action == "submit_bmdp":
        _assert_node_completed(workflow, SRS_NODE_DUAL_GATE_APPROVAL, actor, SRS_NODE_BMDP)
        _assert_node_completed(workflow, SRS_NODE_DEADLINE_LOCKED, actor, SRS_NODE_BMDP)
        _assert_node_completed(workflow, SRS_NODE_ACTION_PATHS, actor, SRS_NODE_BMDP)
        if workflow.case_classification == CASE_3:
            _assert_node_completed(workflow, SRS_NODE_PMDP, actor, SRS_NODE_BMDP)
        _assert_node_status(workflow, SRS_NODE_BMDP, {NODE_STATUS_IN_PROGRESS}, actor)
        if workflow.current_node != SRS_NODE_BMDP:
            message = "BMDP is not the active SRS step."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_BMDP, message)
            frappe.throw(message, frappe.PermissionError)
        return

    if action == "submit_command_center":
        _assert_node_completed(workflow, SRS_NODE_BMDP, actor, SRS_NODE_COMMAND_CENTER_APPROVAL)
        _assert_current_node(workflow, SRS_NODE_COMMAND_CENTER_APPROVAL, actor)
        _assert_node_status(workflow, SRS_NODE_COMMAND_CENTER_APPROVAL, {NODE_STATUS_IN_PROGRESS}, actor)
        return


def _item_assignments_for_user(user: str) -> set[str]:
    import frappe

    assigned = set(
        frappe.get_all(
            "SRS Workflow Instance",
            filters={"project_owner": user},
            pluck="trainer_item",
        )
    )
    team_items = frappe.get_all(
        "SRS Item Team Member",
        filters={"user": user},
        pluck="trainer_item",
    )
    assigned.update(team_items)
    return assigned


def can_view_project(user: str, project: str) -> bool:
    if _is_gm(user) or _is_global_viewer(user) or _is_command_center_representative(user):
        return True
    if _is_ard_user(user):
        from bedo_platform.services.ard_workflow_service import ard_visible_project_names

        return project in set(ard_visible_project_names(user))
    if _is_srs_manager(user):
        import frappe

        return bool(frappe.db.exists("BEDO Trainer Item", {"project": project, "status": ["!=", ITEM_STATUS_DRAFT], "is_deleted": 0}))
    import frappe
    return bool(frappe.db.exists("SRS Item Team Member", {"user": user, "project": project}))


def can_view_trainer_item(user: str, trainer_item: str) -> bool:
    import frappe

    item = frappe.db.get_value("BEDO Trainer Item", trainer_item, ["project", "status"], as_dict=True)
    if not item:
        return False
    if _is_gm(user) or _is_global_viewer(user) or _is_command_center_representative(user):
        return True
    if _is_ard_user(user):
        from bedo_platform.services.ard_workflow_service import ard_visible_trainer_item_names

        return trainer_item in set(ard_visible_trainer_item_names(user))
    if _is_srs_manager(user):
        return item.status != ITEM_STATUS_DRAFT
    return trainer_item in _item_assignments_for_user(user)


def _assert_project_access(user: str, project: str) -> None:
    import frappe

    if not can_view_project(user, project):
        _log("unauthorized_access_attempt", user, project=project, message="Project API access denied")
        frappe.throw("You do not have access to this project.", frappe.PermissionError)


def _assert_item_access(user: str, trainer_item: str) -> None:
    import frappe

    if not can_view_trainer_item(user, trainer_item):
        project = frappe.db.get_value("BEDO Trainer Item", trainer_item, "project") or ""
        _log("unauthorized_access_attempt", user, project=project, trainer_item=trainer_item, message="Trainer item API access denied")
        frappe.throw("You do not have access to this trainer item.", frappe.PermissionError)


def _project_fallback_code() -> str:
    return f"PRJ-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"


def _project_date_or_default(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return datetime.now(UTC).date().isoformat()
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        raise ValueError("PO deadline date must be a valid date.") from None


def _required_text(value: Any, field_label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_label} is required.")
    if "<" in text or ">" in text:
        raise ValueError(f"{field_label} cannot contain HTML markup.")
    return text


def _required_int_for_storage(value: Any, field_label: str) -> int:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_label} is required.")
    if not text.isdigit():
        raise ValueError(f"{field_label} must be a positive whole number.")
    number = int(text)
    if number <= 0:
        raise ValueError(f"{field_label} must be greater than zero.")
    return number


def _validate_project_payload(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "project_name": _required_text(payload.get("project_name"), "Project name"),
        "project_code": _required_text(payload.get("project_code"), "Project code"),
        "end_user": _required_text(payload.get("end_user"), "End user"),
        "po_deadline_date": _project_date_or_default(payload.get("po_deadline_date")),
    }


def create_project(payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    data = _validate_project_payload(payload)
    doc = frappe.get_doc(
        {
            "doctype": "BEDO Project",
            **data,
            "status": PROJECT_STATUS_DETAILS_FINALIZED,
            "created_by_user": actor,
            "created_at": _utcnow(),
            "is_deleted": 0,
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    _log("project_created", actor, project=doc.name, message=f"Project {doc.project_code} created")
    return {"success": True, "project": doc.name}


def update_project_details(project: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    doc = _project_or_throw(project)
    data = _validate_project_payload(payload)
    for key, value in data.items():
        setattr(doc, key, value)
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    _log("project_details_updated", actor, project=project)
    return {"success": True, "project": project}


def finalize_project_details(project: str, actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    doc = _project_or_throw(project)
    _validate_project_payload(doc.as_dict())
    if doc.status not in {PROJECT_STATUS_DRAFT, PROJECT_STATUS_DETAILS_FINALIZED}:
        frappe.throw("Project details are already locked by release.", frappe.PermissionError)
    doc.status = PROJECT_STATUS_DETAILS_FINALIZED
    doc.finalized_at = _utcnow()
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    _log("project_details_finalized", actor, project=project)
    return {"success": True, "project": project}


def _validate_report_to_users(users: list[str]) -> list[str]:
    result = []
    for user in users:
        if user and assert_user_can_login(user) and _primary_department_key(user) == "GM_SUPPORT":
            result.append(user)
        elif user:
            raise ValueError("Report To users must be active GM Support Office users.")
    return sorted(set(result))


def _replace_report_to(trainer_item: str, users: list[str], actor: str) -> None:
    import frappe

    for existing in frappe.get_all("BEDO Trainer Item Report To", filters={"trainer_item": trainer_item}, pluck="name"):
        frappe.delete_doc("BEDO Trainer Item Report To", existing, ignore_permissions=True)
    for user in _validate_report_to_users(users):
        doc = frappe.get_doc(
            {
                "doctype": "BEDO Trainer Item Report To",
                "trainer_item": trainer_item,
                "user": user,
                "added_by": actor,
                "added_at": _utcnow(),
            }
        )
        doc.flags.ignore_permissions = True
        doc.insert(ignore_permissions=True)


def _positive_int_or_default(value: Any, default: int | None = 1) -> int:
    text = str(value if value is not None else "").strip()
    if not text:
        if default is None:
            raise ValueError("Quantity is required.")
        text = str(default)
    if not text.isdigit():
        raise ValueError("Quantity must be a positive whole number.")
    number = int(text)
    if number <= 0:
        raise ValueError("Quantity must be greater than zero.")
    return number


def _positive_money_required(value: Any, field_label: str) -> float:
    text = str(value if value is not None else "").strip()
    if not text:
        raise ValueError(f"{field_label} is required.")
    try:
        number = float(text)
    except ValueError:
        raise ValueError(f"{field_label} must be a valid amount.") from None
    if number <= 0:
        raise ValueError(f"{field_label} must be greater than zero.")
    return round(number, 2)


def _trainer_name_or_default(value: Any) -> str:
    return _required_text(value, "Trainer name")


def _create_trainer_item(project_doc, trainer_name: str, quantity: int, price_egp: float, original_quantity: int, separation_mode: str, sequence_no: int, actor: str, report_to_users: list[str]) -> str:
    import frappe

    trainer_item_name = trainer_name if separation_mode != "SEPARATED" else f"{trainer_name}_{sequence_no}"
    doc = frappe.get_doc(
        {
            "doctype": "BEDO Trainer Item",
            "project": project_doc.name,
            "trainer_name": trainer_name,
            "trainer_item_name": trainer_item_name,
            "quantity": quantity,
            "price_egp": price_egp,
            "original_quantity": original_quantity,
            "separation_mode": separation_mode,
            "sequence_no": sequence_no,
            "status": ITEM_STATUS_DRAFT,
            "current_pillar": "",
            "current_workflow": "",
            "current_node": "",
            "created_by_user": actor,
            "created_at": _utcnow(),
            "is_deleted": 0,
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    _replace_report_to(doc.name, report_to_users, actor)
    return doc.name


def add_trainer_item(project: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    project_doc = _project_or_throw(project)
    if project_doc.status != PROJECT_STATUS_DETAILS_FINALIZED:
        frappe.throw("Finalize project details before adding trainer items.", frappe.PermissionError)
    trainer_name = _trainer_name_or_default(payload.get("trainer_name"))
    quantity = _positive_int_or_default(payload.get("quantity"), default=None)
    price_egp = _positive_money_required(payload.get("price_egp"), "Price (EGP)")
    report_to_users = list(payload.get("report_to_users") or [])
    mode = str(payload.get("separation_mode") or ("SINGLE" if quantity == 1 else "")).strip().upper()
    if quantity == 1:
        mode = "SINGLE"
    if quantity > 1 and mode not in {"COMBINED", "SEPARATED"}:
        mode = "COMBINED"
    created = []
    if mode == "SEPARATED":
        for index in range(1, quantity + 1):
            created.append(_create_trainer_item(project_doc, trainer_name, 1, price_egp, quantity, mode, index, actor, report_to_users))
    else:
        created.append(_create_trainer_item(project_doc, trainer_name, quantity, price_egp, quantity, mode, 1, actor, report_to_users))
    _log("trainer_item_added", actor, project=project, message=f"{len(created)} trainer item(s) added")
    return {"success": True, "project": project, "trainer_items": created}


def update_trainer_item(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    doc = _item_or_throw(trainer_item)
    project = _project_or_throw(doc.project)
    if project.status not in {PROJECT_STATUS_DRAFT, PROJECT_STATUS_DETAILS_FINALIZED}:
        frappe.throw("Trainer items cannot be edited after release to SRS.", frappe.PermissionError)
    trainer_name = _trainer_name_or_default(payload.get("trainer_name"))
    quantity = _positive_int_or_default(payload.get("quantity"), default=None)
    price_egp = _positive_money_required(payload.get("price_egp"), "Price (EGP)")
    doc.trainer_name = trainer_name
    doc.trainer_item_name = trainer_name if doc.separation_mode != "SEPARATED" else f"{trainer_name}_{doc.sequence_no or 1}"
    doc.quantity = quantity
    doc.price_egp = price_egp
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    _replace_report_to(trainer_item, list(payload.get("report_to_users") or []), actor)
    _log("trainer_item_edited", actor, project=doc.project, trainer_item=trainer_item)
    return {"success": True, "trainer_item": trainer_item}


def delete_trainer_item(trainer_item: str, actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    doc = _item_or_throw(trainer_item)
    project = _project_or_throw(doc.project)
    if project.status not in {PROJECT_STATUS_DRAFT, PROJECT_STATUS_DETAILS_FINALIZED}:
        frappe.throw("Trainer items cannot be deleted after release to SRS.", frappe.PermissionError)
    doc.is_deleted = 1
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    _log("trainer_item_deleted", actor, project=doc.project, trainer_item=trainer_item)
    return {"success": True, "trainer_item": trainer_item}


def delete_project_cascade(project: str, actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    project_doc = _project_or_throw(project)
    snapshot = f"{project_doc.project_code} - {project_doc.project_name}"
    trainer_items = frappe.get_all("BEDO Trainer Item", filters={"project": project}, pluck="name")
    workflows = frappe.get_all("SRS Workflow Instance", filters={"project": project}, pluck="name")

    log_security_event(
        "project_deleted",
        user=actor,
        status="Success",
        message=f"Project deleted: {snapshot}",
    )

    try:
        for doctype in [
            "BEDO Notification",
            "BEDO Deadline",
            "SRS Approval",
            "SRS BMDP Submission",
            "SRS Deliverables Matrix",
            "SRS Item Team Member",
            "SRS Workflow Node State",
            "BEDO Project Assignment",
        ]:
            frappe.db.delete(doctype, {"project": project})

        for trainer_item in trainer_items:
            frappe.db.delete("BEDO Trainer Item Report To", {"trainer_item": trainer_item})

        for workflow in workflows:
            if frappe.db.exists("SRS Workflow Instance", workflow):
                frappe.delete_doc("SRS Workflow Instance", workflow, ignore_permissions=True)

        for trainer_item in trainer_items:
            if frappe.db.exists("BEDO Trainer Item", trainer_item):
                frappe.delete_doc("BEDO Trainer Item", trainer_item, ignore_permissions=True)

        frappe.delete_doc("BEDO Project", project, ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise

    return {"success": True, "project": project}


def _create_initial_workflow(item, actor: str) -> str:
    import frappe

    existing = frappe.db.get_value("SRS Workflow Instance", {"trainer_item": item.name}, "name")
    if existing:
        return existing
    workflow = frappe.get_doc(
        {
            "doctype": "SRS Workflow Instance",
            "project": item.project,
            "trainer_item": item.name,
            "status": STATE_GATEWAY,
            "current_node": SRS_NODE_GATEWAY,
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
    )
    workflow.flags.ignore_permissions = True
    workflow.insert(ignore_permissions=True)
    for node_id in [*SRS_FUNCTIONAL_NODES, *SRS_PLACEHOLDER_NODES]:
        _set_node_state(workflow, node_id, NODE_STATUS_LOCKED, actor=actor)
    _set_node_state(workflow, SRS_NODE_PRODUCT_DIGITAL_RELEASE, NODE_STATUS_COMPLETED, actor=actor)
    deadline = create_deadline(
        project=item.project,
        trainer_item=item.name,
        workflow_type=SRS_WORKFLOW_TYPE,
        node_id=SRS_NODE_GATEWAY,
        triggered_by=actor,
        deadline_days=1,
    )
    _set_node_state(workflow, SRS_NODE_GATEWAY, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user="", deadline=deadline)
    _log("srs_workflow_instance_created", actor, project=item.project, trainer_item=item.name, node_id=SRS_NODE_GATEWAY)
    return workflow.name


def release_project_to_srs(project: str, actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    project_doc = _project_or_throw(project)
    if project_doc.status != PROJECT_STATUS_DETAILS_FINALIZED:
        frappe.throw("Project details must be finalized before release to SRS.", frappe.PermissionError)
    items = frappe.get_all("BEDO Trainer Item", filters={"project": project, "is_deleted": 0}, fields=["name"])
    if not items:
        raise ValueError("At least one trainer item is required before release to SRS.")
    now = _utcnow()
    for row in items:
        item = frappe.get_doc("BEDO Trainer Item", row.name)
        workflow = _create_initial_workflow(item, actor)
        item.status = ITEM_STATUS_RELEASED
        item.current_pillar = "SRS"
        item.current_workflow = SRS_WORKFLOW_TYPE
        item.current_node = SRS_NODE_GATEWAY
        item.released_to_srs_at = now
        item.flags.ignore_permissions = True
        item.save(ignore_permissions=True)
    project_doc.status = PROJECT_STATUS_RELEASED_TO_SRS
    project_doc.released_to_srs_at = now
    project_doc.flags.ignore_permissions = True
    project_doc.save(ignore_permissions=True)
    srs_managers = _active_users_with_role("SRS Manager")
    notify_many(
        srs_managers,
        title="Project released to SRS",
        message=f"{project_doc.project_code} is ready for SRS owner assignment.",
        notification_type="PROJECT_RELEASED_TO_SRS",
        project=project,
        action_url=project_action_url("srs", project),
        priority="High",
    )
    _log("project_released_to_srs", actor, project=project, message=f"{len(items)} trainer item(s) released")
    return {"success": True, "project": project, "released_items": len(items)}


def _project_counts(project_names: list[str]) -> dict[str, dict[str, int]]:
    import frappe

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    if not project_names:
        return {}
    items = frappe.get_all(
        "BEDO Trainer Item",
        filters={"project": ["in", project_names], "is_deleted": 0},
        fields=["project", "status", "current_node"],
    )
    workflows = frappe.get_all(
        "SRS Workflow Instance",
        filters={"project": ["in", project_names]},
        fields=["project", "status", "current_node"],
    )
    for item in items:
        counts[item.project]["trainer_items"] += 1
        if item.status in {ITEM_STATUS_RELEASED, ITEM_STATUS_SRS_IN_PROGRESS}:
            counts[item.project]["srs_in_progress"] += 1
    for workflow in workflows:
        if workflow.current_node == SRS_NODE_GATEWAY:
            counts[workflow.project]["awaiting_owner_assignment"] += 1
        if workflow.current_node in {SRS_NODE_COORDINATION, SRS_NODE_DELIVERABLES}:
            counts[workflow.project]["in_coordination"] += 1
        if workflow.current_node in {SRS_NODE_DUAL_GATE_APPROVAL, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, SRS_NODE_SRS_DIRECTOR_APPROVAL}:
            counts[workflow.project]["waiting_approval"] += 1
        if workflow.current_node in {SRS_NODE_ACTION_PATHS, SRS_NODE_GATE_2_PMDP, SRS_NODE_PHYSICAL_BUILD_TEST, SRS_NODE_PMDP, SRS_NODE_BMDP}:
            counts[workflow.project]["in_action_paths"] += 1
        if workflow.status == STATE_COMPLETE:
            counts[workflow.project]["completed"] += 1
    return {project: dict(values) for project, values in counts.items()}


def list_visible_projects(actor: str, page: int = 1, page_size: int = 25) -> dict[str, Any]:
    import frappe

    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 25), 1), 100)
    start = (page - 1) * page_size
    filters: dict[str, Any] = {"is_deleted": 0}
    if _is_gm(actor) or _is_global_viewer(actor) or _is_command_center_representative(actor):
        pass
    elif _is_ard_user(actor):
        from bedo_platform.services.ard_workflow_service import ard_visible_project_names

        filters["name"] = ["in", ard_visible_project_names(actor) or ["__none__"]]
    elif _is_srs_manager(actor):
        project_names = frappe.get_all(
            "BEDO Trainer Item",
            filters={"status": ["!=", ITEM_STATUS_DRAFT], "is_deleted": 0},
            pluck="project",
        )
        filters["name"] = ["in", sorted(set(project_names)) or ["__none__"]]
    else:
        project_names = frappe.get_all(
            "SRS Item Team Member",
            filters={"user": actor},
            pluck="project",
        )
        filters["name"] = ["in", sorted(set(project_names)) or ["__none__"]]
    total = frappe.db.count("BEDO Project", filters)
    projects = frappe.get_all(
        "BEDO Project",
        filters=filters,
        fields=["name", "project_code", "project_name", "end_user", "po_deadline_date", "status", "created_at", "released_to_srs_at", "modified"],
        order_by="modified desc",
        start=start,
        page_length=page_size,
    )
    counts = _project_counts([row.name for row in projects])
    return {
        "projects": [{**dict(project), "counts": counts.get(project.name, {})} for project in projects],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def get_project_detail(project: str, actor: str) -> dict[str, Any]:
    _assert_project_access(actor, project)
    doc = _project_or_throw(project)
    return {"project": _safe_project(doc)}


def _safe_project(doc) -> dict[str, Any]:
    return {
        "name": doc.name,
        "project_code": doc.project_code,
        "project_name": doc.project_name,
        "end_user": doc.end_user,
        "po_deadline_date": str(doc.po_deadline_date or ""),
        "status": doc.status,
        "created_by_user": doc.created_by_user,
        "created_at": to_cairo_iso(doc.created_at),
        "finalized_at": to_cairo_iso(doc.finalized_at),
        "released_to_srs_at": to_cairo_iso(doc.released_to_srs_at),
    }


def _safe_item(row, *, include_price: bool = False) -> dict[str, Any]:
    item = {
        "name": row.name,
        "project": row.project,
        "trainer_name": row.trainer_name,
        "trainer_item_name": row.trainer_item_name,
        "quantity": row.quantity,
        "original_quantity": row.original_quantity,
        "separation_mode": row.separation_mode,
        "sequence_no": row.sequence_no,
        "status": row.status,
        "current_node": row.current_node,
        "current_responsible_user": row.current_responsible_user,
        "current_responsible_name": _user_full_name(row.current_responsible_user),
        "released_to_srs_at": to_cairo_iso(row.released_to_srs_at),
    }
    if include_price:
        item["price_egp"] = float(row.get("price_egp") or 0)
    return item


def _safe_node_state(row, display_data: dict[str, Any] | None = None) -> dict[str, Any]:
    last_action_by = row.get("last_action_by") if hasattr(row, "get") else getattr(row, "last_action_by", None)
    return {
        "node_id": row.node_id,
        "status": row.status,
        "started_at": to_cairo_iso(row.started_at),
        "completed_at": to_cairo_iso(row.completed_at),
        "deadline_start_at": to_cairo_iso(row.deadline_start_at),
        "deadline_due_at": to_cairo_iso(row.deadline_due_at),
        "deadline_days": row.deadline_days,
        "responsible_user": row.responsible_user,
        "responsible_name": _user_full_name(row.responsible_user),
        "last_action_by": last_action_by,
        "last_action_by_name": _user_full_name(last_action_by),
        "display_data": display_data or {},
    }


def _safe_deadline(deadline_name: str) -> dict[str, Any]:
    import frappe

    if not deadline_name:
        return {}
    row = frappe.db.get_value(
        "BEDO Deadline",
        deadline_name,
        ["name", "workflow_type", "node_id", "start_at", "due_at", "deadline_days", "status"],
        as_dict=True,
    )
    if not row:
        return {}
    return {
        **dict(row),
        "start_at": to_cairo_iso(row.start_at),
        "due_at": to_cairo_iso(row.due_at),
        "server_now": server_now_iso(),
    }


def _safe_command_center_handoff(handoff, actor: str) -> dict[str, Any] | None:
    if not handoff:
        return None
    deadline = _safe_deadline(handoff.deadline)
    return {
        "name": handoff.name,
        "project": handoff.project,
        "trainer_item": handoff.trainer_item,
        "srs_workflow_instance": handoff.srs_workflow_instance,
        "handoff_type": handoff.handoff_type,
        "status": handoff.status,
        "command_center_case": handoff.command_center_case or "",
        "deadline_days": handoff.deadline_days or 0,
        "approved_deadline_days": handoff.approved_deadline_days or 0,
        "deadline": handoff.deadline or "",
        "deadline_detail": deadline,
        "responsible_user": handoff.responsible_user or "",
        "responsible_name": _user_full_name(handoff.responsible_user),
        "submitted_by": handoff.submitted_by or "",
        "submitted_by_name": _user_full_name(handoff.submitted_by),
        "submitted_at": to_cairo_iso(handoff.submitted_at),
        "gm_approval": handoff.gm_approval or "",
        "gm_approved_by": handoff.gm_approved_by or "",
        "gm_approved_by_name": _user_full_name(handoff.gm_approved_by),
        "gm_approved_at": to_cairo_iso(handoff.gm_approved_at),
        "generation": getattr(handoff, "generation", 1) or 1,
        "case3_cleared_at": to_cairo_iso(getattr(handoff, "case3_cleared_at", None)),
        "handover_meeting": getattr(handoff, "handover_meeting", "") or "",
        "handover_confirmation_status": getattr(handoff, "handover_confirmation_status", "") or "NOT_STARTED",
        "handover_confirmed_by": getattr(handoff, "handover_confirmed_by", "") or "",
        "handover_confirmed_by_name": _user_full_name(getattr(handoff, "handover_confirmed_by", "")),
        "handover_confirmed_at": to_cairo_iso(getattr(handoff, "handover_confirmed_at", None)),
        "handover_failure_description": getattr(handoff, "handover_failure_description", "") or "",
        "handover_failed_by": getattr(handoff, "handover_failed_by", "") or "",
        "handover_failed_by_name": _user_full_name(getattr(handoff, "handover_failed_by", "")),
        "handover_failed_at": to_cairo_iso(getattr(handoff, "handover_failed_at", None)),
        "completed_by": handoff.completed_by or "",
        "completed_by_name": _user_full_name(handoff.completed_by),
        "completed_at": to_cairo_iso(handoff.completed_at),
        "notes": handoff.notes or "",
        "can_submit_decision": _is_command_center_representative(actor) and handoff.status == COMMAND_CENTER_HANDOFF_PENDING,
        "can_complete_case_1": handoff.responsible_user == actor and handoff.command_center_case == COMMAND_CENTER_CASE_1 and handoff.status == COMMAND_CENTER_HANDOFF_IN_PROGRESS,
        "can_schedule_handover_meeting": handoff.responsible_user == actor and handoff.command_center_case == COMMAND_CENTER_CASE_3 and handoff.status == COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_PENDING,
        "can_submit_handover_confirmation": handoff.responsible_user == actor and handoff.command_center_case == COMMAND_CENTER_CASE_3 and handoff.status == COMMAND_CENTER_HANDOFF_HANDOVER_CONFIRMATION_PENDING,
    }


def _safe_supplier_file(row, actor: str) -> dict[str, Any]:
    deadline = _safe_deadline(row.deadline)
    return {
        "name": row.name,
        "project": row.project,
        "trainer_item": row.trainer_item,
        "source_type": row.source_type,
        "source_handoff": row.source_handoff,
        "status": row.status,
        "responsible_user": row.responsible_user,
        "responsible_name": _user_full_name(row.responsible_user),
        "deadline": row.deadline or "",
        "deadline_detail": deadline,
        "deadline_days": row.deadline_days or 0,
        "started_at": to_cairo_iso(row.started_at),
        "completed_by": row.completed_by or "",
        "completed_by_name": _user_full_name(row.completed_by),
        "completed_at": to_cairo_iso(row.completed_at),
        "details": row.details or "",
        "latest_extension_approval": row.latest_extension_approval or "",
        "can_deliver": row.responsible_user == actor and row.status != SUPPLIER_FILE_COMPLETED,
        "can_request_extension": row.responsible_user == actor and row.status not in {SUPPLIER_FILE_COMPLETED, SUPPLIER_FILE_WAITING_EXTENSION},
    }


def _supplier_files_for_item(trainer_item: str) -> list[Any]:
    import frappe

    return frappe.get_all(
        "BEDO Supplier File",
        filters={"trainer_item": trainer_item, "is_active": 1},
        fields=[
            "name",
            "project",
            "trainer_item",
            "source_type",
            "source_handoff",
            "status",
            "responsible_user",
            "deadline",
            "deadline_days",
            "started_at",
            "completed_by",
            "completed_at",
            "details",
            "latest_extension_approval",
        ],
        order_by="creation asc",
    )


def get_command_center_handoff_workspace(trainer_item: str, actor: str) -> dict[str, Any]:
    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    handoff = _handoff_for_item(trainer_item)
    if not handoff and workflow.status == STATE_COMPLETE and workflow.current_node == SRS_NODE_BMDP:
        handoff = _ensure_command_center_handoff(workflow, actor=actor)
    return {"handoff": _safe_command_center_handoff(handoff, actor)}


def get_supplier_files_for_trainer_item(trainer_item: str, actor: str) -> dict[str, Any]:
    _assert_item_access(actor, trainer_item)
    return {"supplier_files": [_safe_supplier_file(row, actor) for row in _supplier_files_for_item(trainer_item)]}


def _node_display_data(workflow, team_members: list[dict[str, Any]], approvals: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not workflow:
        return {}
    gm_approval = approvals.get("GM_CASE_APPROVAL") or {}
    manager_approval = approvals.get("SRS_MANAGER_DEADLINE_APPROVAL") or {}
    pmdp_srs_approval = approvals.get("PMDP_DUAL_GATE_SRS_APPROVAL") or {}
    pmdp_gm_approval = approvals.get("PMDP_DUAL_GATE_GM_APPROVAL") or {}
    extension_approval = approvals.get("PMDP_EXTENSION_APPROVAL") or {}
    command_center_approval = approvals.get("COMMAND_CENTER_GM_APPROVAL") or {}
    approved_deadline = workflow.approved_deadline_days or gm_approval.get("edited_deadline_proposal_days") or manager_approval.get("edited_deadline_proposal_days") or workflow.deadline_proposal_days
    approved_case = workflow.case_classification or gm_approval.get("edited_case_classification") or manager_approval.get("edited_case_classification")
    command_center_case = command_center_approval.get("edited_case_classification") or command_center_approval.get("original_case_classification", "")
    command_center_deadline = command_center_approval.get("edited_deadline_proposal_days") or command_center_approval.get("original_deadline_proposal_days")
    extension_units = extension_approval.get("edited_deadline_proposal_days") or extension_approval.get("original_deadline_proposal_days")
    team_names = [
        str(member.get("full_name") or _user_full_name(member.get("user")) or member.get("user") or "")
        for member in team_members
        if not member.get("is_project_owner")
    ]
    visible_team_names = ", ".join(team_names[:3])
    if len(team_names) > 3:
        visible_team_names = f"{visible_team_names}, +{len(team_names) - 3} more"
    return {
        SRS_NODE_GATEWAY: {
            "Owner": _user_full_name(workflow.project_owner) or "Not assigned",
        },
        SRS_NODE_COORDINATION: {
            "Team": visible_team_names or "Not selected",
        },
        SRS_NODE_DELIVERABLES: {
            "Case": approved_case or "Not selected",
            "Deadline": deadline_quantity_label(approved_deadline) if approved_deadline else "Not proposed",
        },
        SRS_NODE_DUAL_GATE_APPROVAL: {
            "Status": "Approved" if _node_completed(workflow, SRS_NODE_DUAL_GATE_APPROVAL) else "Waiting approval",
            "Case": workflow.case_classification or "",
            "Deadline": deadline_quantity_label(approved_deadline) if approved_deadline else "",
            "SRS Decision": manager_approval.get("status", ""),
            "GM Decision": gm_approval.get("status", ""),
        },
        SRS_NODE_GM_APPROVAL: {
            "Status": "Approved by General Manager" if workflow.gm_approved_at else "Pending GM Approval",
            "Case": workflow.case_classification or "",
            "Deadline": deadline_quantity_label(workflow.deadline_proposal_days) if workflow.deadline_proposal_days else "",
            "Decision": gm_approval.get("status", ""),
        },
        SRS_NODE_MANAGER_APPROVAL: {
            "Status": "Approved by SRS Manager" if workflow.srs_manager_approved_at else "Pending SRS Manager Approval",
            "Case": workflow.case_classification or "",
            "Deadline": deadline_quantity_label(approved_deadline) if approved_deadline else "",
            "Decision": manager_approval.get("status", ""),
        },
        SRS_NODE_DEADLINE_LOCKED: {
            "Locked Deadline": deadline_quantity_label(approved_deadline) if approved_deadline else "Not locked",
            "Approved Case": workflow.case_classification or "",
        },
        SRS_NODE_ACTION_PATHS: {
            "Active Case": workflow.case_classification or "",
            "BMDP Deadline": deadline_quantity_label(approved_deadline) if approved_deadline else "",
        },
        SRS_NODE_GATE_2_PMDP: {
            "Status": "Gate 2 PMDP submitted" if workflow.pmdp_gate_path else "PMDP path required",
            "Path": str(workflow.pmdp_gate_path or ""),
            "Submitted By": _user_full_name(workflow.pmdp_gate_submitted_by) or workflow.pmdp_gate_submitted_by or "",
        },
        SRS_NODE_PMDP_DUAL_GATE_APPROVAL: {
            "Status": "Approved" if _node_completed(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL) else "Waiting approval",
            "SRS Decision": pmdp_srs_approval.get("status", ""),
            "GM Decision": pmdp_gm_approval.get("status", ""),
        },
        SRS_NODE_PHYSICAL_BUILD_TEST: {
            "Status": "Physical build complete" if workflow.pmdp_path else "Physical build in progress",
            "Started": to_cairo_iso(workflow.physical_build_started_at),
        },
        SRS_NODE_EXTENSION_DEADLINE: {
            "Requested Extension": deadline_quantity_label(extension_units) if extension_units else "",
            "Comment": extension_approval.get("comments", ""),
            "Decision": extension_approval.get("status", ""),
        },
        SRS_NODE_SRS_DIRECTOR_APPROVAL: {
            "Status": "Approved by SRS Manager" if extension_approval.get("approved_at") else "Pending SRS Manager approval",
            "Requested Extension": deadline_quantity_label(extension_units) if extension_units else "",
            "Comment": extension_approval.get("comments", ""),
        },
        SRS_NODE_PMDP: {
            "Status": "PMDP submitted" if workflow.pmdp_path else "PMDP path required",
            "Path": str(workflow.pmdp_path or ""),
            "Submitted By": _user_full_name(workflow.pmdp_submitted_by) or workflow.pmdp_submitted_by or "",
        },
        SRS_NODE_BMDP: {
            "Status": "BMDP submitted" if workflow.bmdp_path else "BMDP path required",
            "Path": str(workflow.bmdp_path or ""),
            "Deadline": deadline_quantity_label(approved_deadline) if approved_deadline else "",
        },
        SRS_NODE_COMMAND_CENTER_APPROVAL: {
            "Case": command_center_case or "Not selected",
            "Deadline": deadline_quantity_label(command_center_deadline) if command_center_deadline else "Not proposed",
            "Submitted By": _user_full_name(command_center_approval.get("approved_by") or command_center_approval.get("assigned_to_user")) or "",
        },
        SRS_NODE_FINAL_GM_APPROVAL: {
            "Status": "Approved by General Manager" if command_center_approval.get("approved_at") else "Pending GM Approval",
            "Case": command_center_case,
            "Deadline": deadline_quantity_label(command_center_deadline) if command_center_deadline else "",
        },
    }


def list_trainer_items_for_project(project: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_project_access(actor, project)
    filters: dict[str, Any] = {"project": project, "is_deleted": 0}
    if _is_ard_user(actor):
        from bedo_platform.services.ard_workflow_service import ard_visible_trainer_item_names

        allowed_items = ard_visible_trainer_item_names(actor)
        filters["name"] = ["in", sorted(allowed_items) or ["__none__"]]
    elif not (_is_gm(actor) or _is_srs_manager(actor) or _is_command_center_representative(actor)):
        allowed_items = _item_assignments_for_user(actor)
        filters["name"] = ["in", sorted(allowed_items) or ["__none__"]]
    rows = frappe.get_all(
        "BEDO Trainer Item",
        filters=filters,
        fields=["name", "project", "trainer_name", "trainer_item_name", "quantity", "price_egp", "original_quantity", "separation_mode", "sequence_no", "status", "current_node", "current_responsible_user", "released_to_srs_at"],
        order_by="creation asc",
    )
    workflows = {}
    for row in frappe.get_all(
        "SRS Workflow Instance",
        filters={"project": project},
        fields=["name", "trainer_item", "status", "current_node", "project_owner", "case_classification", "approved_deadline_days"],
    ):
        workflows[row.trainer_item] = {**dict(row), "project_owner_full_name": _user_full_name(row.project_owner)}
    deadlines = {
        row.trainer_item: {**dict(row), "start_at": to_cairo_iso(row.start_at), "due_at": to_cairo_iso(row.due_at), "deadline_status": "ACTIVE", "server_now": server_now_iso()}
        for row in frappe.get_all(
            "BEDO Deadline",
            filters={"project": project, "status": "ACTIVE"},
            fields=["trainer_item", "node_id", "start_at", "due_at", "status"],
            order_by="due_at asc",
        )
    }
    return {
        "trainer_items": [
            {**_safe_item(row, include_price=_is_gm(actor)), "workflow": workflows.get(row.name), "deadline": deadlines.get(row.name)}
            for row in rows
        ]
    }


def get_trainer_item_workspace(trainer_item: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    item = _item_or_throw(trainer_item)
    project = _project_or_throw(item.project)
    workflow_name = frappe.db.get_value("SRS Workflow Instance", {"trainer_item": trainer_item}, "name")
    workflow = frappe.get_doc("SRS Workflow Instance", workflow_name) if workflow_name else None
    node_states = []
    if workflow:
        _backfill_completed_srs_terminal_nodes(workflow)
        node_states = frappe.get_all(
            "SRS Workflow Node State",
            filters={"workflow_instance": workflow.name},
            fields=["node_id", "status", "started_at", "completed_at", "deadline_start_at", "deadline_due_at", "deadline_days", "responsible_user", "last_action_by"],
            order_by="creation asc",
        )
    team_members = []
    approvals = {}
    if workflow:
        team_members = [
            {**dict(row), "full_name": _user_full_name(row.user)}
            for row in frappe.get_all(
                "SRS Item Team Member",
                filters={"workflow_instance": workflow.name},
                fields=["user", "is_project_owner", "selected_by", "selected_at"],
                order_by="selected_at asc",
            )
        ]
        approvals = {
            row.approval_type: dict(row)
            for row in frappe.get_all(
                "SRS Approval",
                filters={"workflow_instance": workflow.name},
                fields=[
                    "name",
                    "approval_type",
                    "status",
                    "required_role",
                    "assigned_to_user",
                    "approved_by",
                    "approved_at",
                    "original_case_classification",
                    "edited_case_classification",
                    "original_deadline_proposal_days",
                    "edited_deadline_proposal_days",
                    "comments",
                ],
                order_by="creation asc",
            )
        }
    display_data = _node_display_data(workflow, team_members, approvals)
    report_to = frappe.get_all("BEDO Trainer Item Report To", filters={"trainer_item": trainer_item}, fields=["user"])
    audit = frappe.get_all(
        "BEDO Security Event",
        filters={"trainer_item": trainer_item, **({"workflow_type": SRS_WORKFLOW_TYPE} if _is_srs_manager(actor) and not _is_gm(actor) else {})},
        fields=["event_type", "user", "target_user", "project", "trainer_item", "node_id", "status", "message", "created_at"],
        order_by="created_at desc",
        page_length=50,
    )
    handoff = _handoff_for_item(trainer_item)
    if not handoff and workflow and workflow.status == STATE_COMPLETE and workflow.current_node == SRS_NODE_BMDP:
        handoff = _ensure_command_center_handoff(workflow, actor=actor)
    supplier_files = [_safe_supplier_file(row, actor) for row in _supplier_files_for_item(trainer_item)]
    if _is_gm(actor):
        tabs = ["SRS", "ARD", "Production", "QC", "Operations", "Command Center"]
        if supplier_files:
            tabs.append("Suppliers")
        tabs.append("Audit Log")
    elif _is_command_center_representative(actor):
        tabs = ["Command Center"]
        if supplier_files or any(row.get("responsible_user") == actor for row in supplier_files):
            tabs.append("Suppliers")
        tabs.append("SRS")
    elif _is_srs_manager(actor):
        tabs = ["SRS", "Audit Log"]
    else:
        tabs = ["SRS"]
        if any(row.get("responsible_user") == actor for row in supplier_files):
            tabs.append("Suppliers")
    return {
        "project": _safe_project(project),
        "trainer_item": _safe_item(item, include_price=_is_gm(actor)),
        "workflow": dict(workflow.as_dict()) if workflow else None,
        "node_states": [_safe_node_state(row, display_data.get(row.node_id)) for row in node_states],
        "deadlines": get_deadlines_for_trainer_item(trainer_item),
        "node_availability": _node_availability(actor, workflow) if workflow else [],
        "server_now": server_now_iso(),
        "report_to_users": [row.user for row in report_to],
        "team_members": team_members,
        "approvals": list(approvals.values()),
        "command_center_handoff": _safe_command_center_handoff(handoff, actor),
        "supplier_files": supplier_files,
        "audit_events": [dict(row) for row in audit],
        "tabs": tabs,
        "deadline_unit_label": deadline_unit_label(),
        "can_edit_before_release": _is_gm(actor) and project.status in {PROJECT_STATUS_DRAFT, PROJECT_STATUS_DETAILS_FINALIZED},
    }


def get_srs_flowchart_definition() -> dict[str, Any]:
    return {
        "lanes": [
            {"id": "operations", "label": "Operations"},
            {"id": "srs_entry", "label": "SRS Entry & Assignment"},
            {"id": "study_phase", "label": "Multidisciplinary Study Phase"},
        ],
        "deadline_columns": [
            {"id": "deadline_1", "label": "Deadline 1", "detail": deadline_quantity_label(1)},
            {"id": "deadline_2", "label": "Deadline 2", "detail": deadline_quantity_label(2)},
            {"id": "deadline_3", "label": "Deadline 3", "detail": "Set by Dual Gate Approval"},
            {"id": "deadline_4", "label": "Deadline 4", "detail": "Case 3 PMDP / final approvals"},
        ],
        "nodes": [dict(node) for node in SRS_FLOWCHART_NODE_DEFINITIONS],
        "edges": [{"from": source, "to": target} for source, target in SRS_FLOWCHART_EDGES],
        "case_classifications": CASE_CLASSIFICATIONS,
        "deadline_unit_label": deadline_unit_label(),
    }


def _node_definition(node_id: str) -> dict[str, Any]:
    return next((node for node in SRS_FLOWCHART_NODE_DEFINITIONS if node["id"] == node_id), {})


def _can_user_open_node(actor: str, workflow, node_id: str) -> bool:
    if node_id == SRS_NODE_GATEWAY:
        return _is_srs_manager(actor)
    if node_id == SRS_NODE_COORDINATION:
        return workflow.project_owner == actor
    if node_id == SRS_NODE_DELIVERABLES:
        return workflow.project_owner == actor
    if node_id in {SRS_NODE_GATE_2_PMDP, SRS_NODE_PHYSICAL_BUILD_TEST, SRS_NODE_PMDP, SRS_NODE_BMDP}:
        return workflow.project_owner == actor or _is_selected_srs_team_member(workflow, actor)
    if node_id == SRS_NODE_COMMAND_CENTER_APPROVAL:
        return _is_command_center_representative(actor)
    return False


def _node_disabled_reason(actor: str, workflow, node_id: str) -> str:
    definition = _node_definition(node_id)
    if not definition.get("clickable"):
        return "Display-only step."
    if not _can_user_open_node(actor, workflow, node_id):
        return "You do not have permission for this step."
    for previous in definition.get("requiredPreviousNodes") or []:
        if node_id == SRS_NODE_BMDP and workflow.case_classification != CASE_3 and previous == SRS_NODE_PMDP:
            continue
        if (
            node_id == SRS_NODE_GATE_2_PMDP
            and previous == SRS_NODE_CASE_3
            and workflow.case_classification == CASE_3
            and _node_status(workflow, SRS_NODE_CASE_3) in {NODE_STATUS_IN_PROGRESS, NODE_STATUS_COMPLETED}
        ):
            continue
        if (
            node_id == SRS_NODE_PMDP
            and previous == SRS_NODE_PHYSICAL_BUILD_TEST
            and workflow.case_classification == CASE_3
            and _node_status(workflow, SRS_NODE_PHYSICAL_BUILD_TEST) in {NODE_STATUS_IN_PROGRESS, NODE_STATUS_COMPLETED}
        ):
            continue
        if not _node_completed(workflow, previous):
            return "Complete the previous step first."
    if node_id in {SRS_NODE_GATE_2_PMDP, SRS_NODE_PMDP, SRS_NODE_PHYSICAL_BUILD_TEST} and workflow.case_classification != CASE_3:
        return "This step is only used for Case 3."
    if node_id == SRS_NODE_GATE_2_PMDP and workflow.pmdp_gate_path:
        return "Gate 2 PMDP has already been submitted."
    if node_id == SRS_NODE_PMDP and workflow.pmdp_path:
        return "PMDP has already been submitted."
    if node_id == SRS_NODE_BMDP and workflow.bmdp_path:
        return "BMDP has already been submitted."
    state = _node_status(workflow, node_id)
    if state not in {NODE_STATUS_IN_PROGRESS, NODE_STATUS_WAITING_APPROVAL, NODE_STATUS_READY}:
        return "This step is not active."
    if node_id == SRS_NODE_PHYSICAL_BUILD_TEST and workflow.current_node == SRS_NODE_PMDP and not workflow.pmdp_path:
        return ""
    if node_id != workflow.current_node:
        return "This is not the active step."
    return ""


def _node_availability(actor: str, workflow) -> list[dict[str, Any]]:
    availability = []
    for definition in SRS_FLOWCHART_NODE_DEFINITIONS:
        node_id = definition["id"]
        reason = _node_disabled_reason(actor, workflow, node_id)
        can_open = bool(definition.get("clickable")) and not reason
        availability.append(
            {
                "nodeId": node_id,
                "canView": True,
                "canOpen": can_open,
                "canAct": can_open,
                "disabledReason": reason,
            }
        )
    return availability


def _authorized_for_workflow_action(actor: str, workflow, *, allow_gm: bool = True, allow_manager: bool = True, allow_owner: bool = True) -> bool:
    if allow_gm and _is_gm(actor):
        return True
    if allow_manager and _is_srs_manager(actor):
        return True
    if allow_owner and workflow.project_owner == actor:
        return True
    return False


def _is_selected_srs_team_member(workflow, actor: str) -> bool:
    import frappe

    return bool(
        frappe.db.exists(
            "SRS Item Team Member",
            {"workflow_instance": workflow.name, "user": actor},
        )
    )


def _assert_workflow_action(actor: str, workflow, node_id: str, *, allow_gm: bool = True, allow_manager: bool = True, allow_owner: bool = True) -> None:
    import frappe

    if not _authorized_for_workflow_action(actor, workflow, allow_gm=allow_gm, allow_manager=allow_manager, allow_owner=allow_owner):
        _log("unauthorized_access_attempt", actor, project=workflow.project, trainer_item=workflow.trainer_item, node_id=node_id)
        frappe.throw("You are not authorized for this SRS workflow action.", frappe.PermissionError)


def list_report_to_candidates(actor: str) -> dict[str, Any]:
    return {"users": [_safe_user_row(user) for user in _active_users_in_departments({"GM_SUPPORT"})]}


def list_eligible_project_owners(actor: str) -> dict[str, Any]:
    _require_role(actor, "SRS Manager") if not _is_gm(actor) else None
    users = _active_users_in_departments({"GM_SUPPORT", "SRS"})
    grouped: dict[str, list[dict[str, str]]] = {"GM Support Office": [], "SRS Department": []}
    for user in users:
        row = _safe_user_row(user)
        if row["department_key"] == "GM_SUPPORT" or row["department_key"] == "SRS":
            group = "GM Support Office" if row["department_key"] == "GM_SUPPORT" else "SRS Department"
            grouped[group].append(row)
    return {"groups": grouped}


def list_eligible_srs_team_members(actor: str, workflow_instance: str | None = None) -> dict[str, Any]:
    users = set()
    for role in SRS_ROLES:
        users.update(_active_users_with_role(role))
    return {"users": [_safe_user_row(user) for user in sorted(users)]}


def assign_srs_project_owner(trainer_item: str, project_owner: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_workflow_action(actor, workflow, SRS_NODE_GATEWAY, allow_gm=False, allow_manager=True, allow_owner=False)
    _assert_transition_prerequisites("assign_owner", workflow, actor)
    if workflow.project_owner:
        frappe.throw("Project Owner has already been assigned.", frappe.PermissionError)
    if not assert_user_can_login(project_owner) or _primary_department_key(project_owner) not in {"GM_SUPPORT", "SRS"}:
        raise ValueError("Project Owner must be an active GM Support Office or SRS user.")
    workflow.project_owner = project_owner
    workflow.status = STATE_OWNER_ASSIGNED
    workflow.current_node = SRS_NODE_COORDINATION
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    complete_deadlines(trainer_item, SRS_NODE_GATEWAY)
    _set_node_state(workflow, SRS_NODE_GATEWAY, NODE_STATUS_COMPLETED, actor=actor, responsible_user=project_owner)
    deadline = create_deadline(
        project=workflow.project,
        trainer_item=trainer_item,
        workflow_type=SRS_WORKFLOW_TYPE,
        node_id=SRS_NODE_COORDINATION,
        triggered_by=actor,
        deadline_days=2,
    )
    _set_node_state(workflow, SRS_NODE_COORDINATION, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=project_owner, deadline=deadline)
    _ensure_item_team_member(workflow, project_owner, actor, is_project_owner=True)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_COORDINATION, "current_responsible_user": project_owner, "status": ITEM_STATUS_SRS_IN_PROGRESS})
    notify_many(
        [project_owner],
        title="SRS project ownership assigned",
        message="You have been assigned as Project Owner for an SRS trainer item.",
        notification_type="PROJECT_OWNER_ASSIGNED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_COORDINATION,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    _log("srs_owner_assigned", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_GATEWAY, target_user=project_owner)
    return {"success": True, "trainer_item": trainer_item}


def _ensure_item_team_member(workflow, user: str, selected_by: str, *, is_project_owner: bool = False) -> None:
    import frappe

    existing = frappe.db.get_value(
        "SRS Item Team Member",
        {"workflow_instance": workflow.name, "user": user},
        "name",
    )
    if existing:
        if is_project_owner:
            frappe.db.set_value("SRS Item Team Member", existing, "is_project_owner", 1, update_modified=False)
        return
    doc = frappe.get_doc(
        {
            "doctype": "SRS Item Team Member",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": workflow.trainer_item,
            "user": user,
            "selected_by": selected_by,
            "selected_at": _utcnow(),
            "is_project_owner": 1 if is_project_owner else 0,
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)


def select_srs_team(trainer_item: str, users: list[str], actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_workflow_action(actor, workflow, SRS_NODE_COORDINATION, allow_gm=False, allow_manager=False, allow_owner=True)
    _assert_transition_prerequisites("select_team", workflow, actor)
    if frappe.db.exists("SRS Item Team Member", {"workflow_instance": workflow.name, "is_project_owner": 0}):
        frappe.throw("SRS team has already been selected.", frappe.PermissionError)
    additional = sorted(set(users or []) - {workflow.project_owner})
    if not additional:
        raise ValueError("Select at least one additional SRS team member.")
    for user in additional:
        if not assert_user_can_login(user) or not (_roles(user) & SRS_ROLES):
            raise ValueError("Additional team members must be active SRS users.")
    _ensure_item_team_member(workflow, workflow.project_owner, actor, is_project_owner=True)
    for user in additional:
        _ensure_item_team_member(workflow, user, actor)
    notify_many(
        additional,
        title="SRS team assignment",
        message="You have been assigned as an SRS team member for this trainer item.",
        notification_type="SRS_TEAM_ASSIGNED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_DELIVERABLES,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    complete_deadlines(trainer_item, SRS_NODE_COORDINATION)
    _set_node_state(workflow, SRS_NODE_COORDINATION, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_node_state(workflow, SRS_NODE_DELIVERABLES, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner)
    workflow.status = STATE_COORDINATION
    workflow.current_node = SRS_NODE_DELIVERABLES
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_DELIVERABLES, "current_responsible_user": workflow.project_owner})
    _log("srs_team_selected", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_COORDINATION)
    return {"success": True, "trainer_item": trainer_item}


def submit_mandatory_coordination(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    return select_srs_team(trainer_item, list(payload.get("users") or []), actor)


def submit_srs_deliverables_matrix(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_workflow_action(actor, workflow, SRS_NODE_DELIVERABLES, allow_gm=False, allow_manager=False, allow_owner=True)
    _assert_transition_prerequisites("submit_deliverables", workflow, actor)
    if frappe.db.exists("SRS Deliverables Matrix", {"workflow_instance": workflow.name}):
        frappe.throw("Deliverables Matrix has already been submitted.", frappe.PermissionError)
    case_classification = str(payload.get("case_classification") or "").strip()
    deadline_days = _required_int_for_storage(payload.get("deadline_proposal_days"), "Deadline")
    if case_classification not in CASE_CLASSIFICATIONS:
        raise ValueError("A valid case classification is required.")
    doc = frappe.get_doc(
        {
            "doctype": "SRS Deliverables Matrix",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": trainer_item,
            "submitted_by": actor,
            "submitted_at": _utcnow(),
            "case_classification": case_classification,
            "deadline_proposal_days": deadline_days,
            "status": "SUBMITTED",
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    workflow.case_classification = case_classification
    workflow.deadline_proposal_days = deadline_days
    workflow.status = STATE_WAITING_MANAGER
    workflow.current_node = SRS_NODE_DUAL_GATE_APPROVAL
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_DELIVERABLES, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_node_state(workflow, SRS_NODE_DUAL_GATE_APPROVAL, NODE_STATUS_WAITING_APPROVAL, actor=actor)
    _create_approval(workflow, "SRS_MANAGER_DEADLINE_APPROVAL", actor)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, "current_node", SRS_NODE_DUAL_GATE_APPROVAL)
    recipients = _active_users_with_role("SRS Manager")
    notify_many(
        recipients,
        title="Dual gate approval required",
        message=f"{case_classification} requires SRS Manager approval.",
        notification_type="SRS_MANAGER_APPROVAL_REQUIRED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_DUAL_GATE_APPROVAL,
        action_url="/approvals",
        priority="High",
    )
    _log("srs_deliverables_submitted", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_DELIVERABLES)
    return {"success": True, "trainer_item": trainer_item}


def _create_approval(
    workflow,
    approval_type: str,
    actor: str,
    *,
    deadline_units: int | None = None,
    comments: str = "",
    assigned_to_user: str = "",
) -> None:
    import frappe

    if frappe.db.exists("SRS Approval", {"workflow_instance": workflow.name, "approval_type": approval_type, "status": "WAITING"}):
        return
    required_role = (
        "General Manager"
        if approval_type
        in {
            "GM_CASE_APPROVAL",
            "PMDP_DUAL_GATE_GM_APPROVAL",
            "COMMAND_CENTER_GM_APPROVAL",
            COMMAND_CENTER_SRS_ARD_GM_APPROVAL,
            SUPPLIER_DEADLINE_EXTENSION_APPROVAL,
            GLOBAL_DEADLINE_EXTENSION_APPROVAL,
        }
        else "SRS Manager"
    )
    doc = frappe.get_doc(
        {
            "doctype": "SRS Approval",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": workflow.trainer_item,
            "approval_department": _approval_department_for_type(approval_type),
            "approval_type": approval_type,
            "status": "WAITING",
            "required_role": required_role,
            "assigned_to_user": assigned_to_user,
            "original_case_classification": workflow.case_classification,
            "original_deadline_proposal_days": deadline_units if deadline_units is not None else workflow.deadline_proposal_days,
            "comments": comments[:500],
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)


def approve_srs_case_as_gm(trainer_item: str, payload: dict[str, Any], actor: str, approval_name: str | None = None) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_transition_prerequisites("gm_approve", workflow, actor)
    approval_name = approval_name or frappe.db.get_value("SRS Approval", {"workflow_instance": workflow.name, "approval_type": "GM_CASE_APPROVAL", "status": "WAITING"}, "name")
    if not approval_name or workflow.gm_approved_at:
        frappe.throw("GM approval is not available or has already been completed.", frappe.PermissionError)
    case_classification, deadline_days = _edited_case_and_deadline(workflow, payload)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    approval.status = "APPROVED_WITH_EDITS" if payload.get("case_classification") or payload.get("deadline_proposal_days") else "APPROVED"
    approval.edited_case_classification = case_classification
    approval.edited_deadline_proposal_days = deadline_days
    approval.comments = str(payload.get("comments") or "")[:500]
    approval.approved_by = actor
    approval.approved_at = _utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    workflow.case_classification = case_classification
    workflow.deadline_proposal_days = deadline_days
    workflow.approved_deadline_days = deadline_days
    workflow.gm_approved_by = actor
    workflow.gm_approved_at = approval.approved_at
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _start_post_dual_gate_path(workflow, actor, deadline_days)
    _log("srs_gm_approved", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_DUAL_GATE_APPROVAL)
    return {"success": True, "trainer_item": trainer_item}


def _edited_case_and_deadline(workflow, payload: dict[str, Any]) -> tuple[str, int]:
    case_classification = str(payload.get("case_classification") or workflow.case_classification or "").strip()
    deadline_days = _required_int_for_storage(payload.get("deadline_proposal_days") or workflow.deadline_proposal_days, "Deadline")
    if case_classification not in CASE_CLASSIFICATIONS:
        raise ValueError("A valid case classification is required.")
    return case_classification, deadline_days


def approve_srs_deadline_as_srs_manager(trainer_item: str, payload: dict[str, Any], actor: str, approval_name: str | None = None) -> dict[str, Any]:
    import frappe

    _require_role(actor, "SRS Manager")
    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_transition_prerequisites("manager_approve", workflow, actor)
    approval_name = approval_name or frappe.db.get_value("SRS Approval", {"workflow_instance": workflow.name, "approval_type": "SRS_MANAGER_DEADLINE_APPROVAL", "status": "WAITING"}, "name")
    if not approval_name or workflow.srs_manager_approved_at:
        frappe.throw("SRS Manager approval is not available or has already been completed.", frappe.PermissionError)
    case_classification, deadline_days = _edited_case_and_deadline(workflow, payload)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    approval.status = "APPROVED_WITH_EDITS" if payload.get("case_classification") or payload.get("deadline_proposal_days") else "APPROVED"
    approval.edited_case_classification = case_classification
    approval.edited_deadline_proposal_days = deadline_days
    approval.comments = str(payload.get("comments") or "")[:500]
    approval.approved_by = actor
    approval.approved_at = _utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    workflow.case_classification = case_classification
    workflow.deadline_proposal_days = deadline_days
    workflow.approved_deadline_days = deadline_days
    workflow.srs_manager_approved_by = actor
    workflow.srs_manager_approved_at = approval.approved_at
    workflow.updated_at = _utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    if case_classification in GM_APPROVAL_CASES:
        _set_node_state(workflow, SRS_NODE_DUAL_GATE_APPROVAL, NODE_STATUS_WAITING_APPROVAL, actor=actor)
        workflow.status = STATE_WAITING_GM
        workflow.current_node = SRS_NODE_DUAL_GATE_APPROVAL
        workflow.flags.ignore_permissions = True
        workflow.save(ignore_permissions=True)
        _create_approval(workflow, "GM_CASE_APPROVAL", actor)
        frappe.db.set_value("BEDO Trainer Item", trainer_item, "current_node", SRS_NODE_DUAL_GATE_APPROVAL)
        notify_many(
            _active_users_with_role("General Manager"),
            title="Dual gate GM approval required",
            message=f"{case_classification} requires GM approval.",
            notification_type="GM_APPROVAL_REQUIRED",
            project=workflow.project,
            trainer_item=trainer_item,
            node_id=SRS_NODE_DUAL_GATE_APPROVAL,
            action_url="/approvals",
            priority="High",
        )
    else:
        _start_post_dual_gate_path(workflow, actor, deadline_days)
    _log("srs_manager_approved", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_DUAL_GATE_APPROVAL)
    return {"success": True, "trainer_item": trainer_item}


def _assert_owner_or_team_member(workflow, actor: str, node_id: str) -> None:
    import frappe

    if workflow.project_owner == actor or _is_selected_srs_team_member(workflow, actor):
        return
    _log("unauthorized_access_attempt", actor, project=workflow.project, trainer_item=workflow.trainer_item, node_id=node_id)
    frappe.throw("Only the Project Owner or a selected SRS team member can complete this step.", frappe.PermissionError)


def submit_pmdp_gate_path(trainer_item: str, pmdp_path: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_owner_or_team_member(workflow, actor, SRS_NODE_GATE_2_PMDP)
    _assert_transition_prerequisites("submit_pmdp_gate", workflow, actor)
    if workflow.pmdp_gate_path:
        frappe.throw("Gate 2 PMDP path has already been submitted.", frappe.PermissionError)
    path = str(pmdp_path or "").strip()
    if not path:
        raise ValueError("Gate 2 PMDP path is required.")
    now = _utcnow()
    workflow.pmdp_gate_path = path
    workflow.pmdp_gate_submitted_by = actor
    workflow.pmdp_gate_submitted_at = now
    workflow.status = STATE_WAITING_PMDP_DUAL_GATE
    workflow.current_node = SRS_NODE_PMDP_DUAL_GATE_APPROVAL
    workflow.updated_at = now
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_GATE_2_PMDP, NODE_STATUS_COMPLETED, actor=actor, responsible_user=actor)
    _set_node_state(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, NODE_STATUS_WAITING_APPROVAL, actor=actor)
    _create_approval(workflow, "PMDP_DUAL_GATE_SRS_APPROVAL", actor, assigned_to_user=actor)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_PMDP_DUAL_GATE_APPROVAL, "current_responsible_user": ""})
    notify_many(
        _active_users_with_role("SRS Manager"),
        title="PMDP dual gate approval required",
        message="Gate 2 PMDP path is ready for SRS approval.",
        notification_type="PMDP_DUAL_GATE_APPROVAL_REQUIRED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
        action_url="/approvals",
        priority="High",
    )
    _log("srs_pmdp_gate_submitted", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_GATE_2_PMDP)
    return {"success": True, "trainer_item": trainer_item}


def _deny_pmdp_dual_gate(approval, workflow, actor: str, comments: str = "") -> dict[str, Any]:
    approval.status = "DENIED"
    approval.comments = str(comments or approval.comments or "")[:500]
    approval.approved_by = actor
    approval.approved_at = _utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    _reset_pmdp_gate_for_denial(workflow, actor, approval.comments)
    _log("srs_pmdp_gate_denied", actor, project=workflow.project, trainer_item=workflow.trainer_item, node_id=SRS_NODE_PMDP_DUAL_GATE_APPROVAL, message=approval.comments)
    return {"success": True, "trainer_item": workflow.trainer_item}


def approve_pmdp_dual_gate_as_srs_manager(trainer_item: str, payload: dict[str, Any], actor: str, approval_name: str | None = None) -> dict[str, Any]:
    import frappe

    _require_role(actor, "SRS Manager")
    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_transition_prerequisites("pmdp_dual_gate_approve", workflow, actor)
    approval_name = approval_name or frappe.db.get_value("SRS Approval", {"workflow_instance": workflow.name, "approval_type": "PMDP_DUAL_GATE_SRS_APPROVAL", "status": "WAITING"}, "name")
    if not approval_name:
        frappe.throw("PMDP SRS approval is not available.", frappe.PermissionError)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    if str(payload.get("action") or "").lower() == "deny":
        return _deny_pmdp_dual_gate(approval, workflow, actor, str(payload.get("comments") or ""))
    approval.status = "APPROVED"
    approval.comments = str(payload.get("comments") or approval.comments or "")[:500]
    approval.approved_by = actor
    approval.approved_at = _utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, NODE_STATUS_WAITING_APPROVAL, actor=actor)
    workflow.status = STATE_WAITING_PMDP_DUAL_GATE
    workflow.current_node = SRS_NODE_PMDP_DUAL_GATE_APPROVAL
    workflow.updated_at = approval.approved_at
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _create_approval(workflow, "PMDP_DUAL_GATE_GM_APPROVAL", actor)
    notify_many(
        _active_users_with_role("General Manager"),
        title="PMDP dual gate GM approval required",
        message="Gate 2 PMDP path is ready for GM approval.",
        notification_type="PMDP_DUAL_GATE_APPROVAL_REQUIRED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
        action_url="/approvals",
        priority="High",
    )
    _log("srs_pmdp_gate_srs_approved", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_PMDP_DUAL_GATE_APPROVAL)
    return {"success": True, "trainer_item": trainer_item}


def approve_pmdp_dual_gate_as_gm(trainer_item: str, payload: dict[str, Any], actor: str, approval_name: str | None = None) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_transition_prerequisites("pmdp_dual_gate_approve", workflow, actor)
    approval_name = approval_name or frappe.db.get_value("SRS Approval", {"workflow_instance": workflow.name, "approval_type": "PMDP_DUAL_GATE_GM_APPROVAL", "status": "WAITING"}, "name")
    if not approval_name:
        frappe.throw("PMDP GM approval is not available.", frappe.PermissionError)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    if str(payload.get("action") or "").lower() == "deny":
        return _deny_pmdp_dual_gate(approval, workflow, actor, str(payload.get("comments") or ""))
    now = _utcnow()
    approval.status = "APPROVED"
    approval.comments = str(payload.get("comments") or approval.comments or "")[:500]
    approval.approved_by = actor
    approval.approved_at = now
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    workflow.physical_build_started_at = workflow.physical_build_started_at or now
    workflow.status = STATE_PMDP_READY
    workflow.current_node = SRS_NODE_PMDP
    workflow.updated_at = now
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_PMDP_DUAL_GATE_APPROVAL, NODE_STATUS_COMPLETED, actor=actor)
    _set_node_state(workflow, SRS_NODE_PHYSICAL_BUILD_TEST, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner)
    _set_node_state(workflow, SRS_NODE_PMDP, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_PMDP, "current_responsible_user": workflow.project_owner})
    notify_many(
        [workflow.project_owner],
        title="Physical build and PMDP active",
        message="PMDP dual gate approval is complete. Physical build and PMDP submission are active.",
        notification_type="PMDP_DUAL_GATE_APPROVED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_PMDP,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    _log("srs_pmdp_gate_gm_approved", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_PMDP_DUAL_GATE_APPROVAL)
    return {"success": True, "trainer_item": trainer_item}


def request_pmdp_extension(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_owner_or_team_member(workflow, actor, SRS_NODE_EXTENSION_DEADLINE)
    _assert_transition_prerequisites("request_pmdp_extension", workflow, actor)
    if frappe.db.exists("SRS Approval", {"workflow_instance": workflow.name, "approval_type": "PMDP_EXTENSION_APPROVAL", "status": "WAITING"}):
        frappe.throw("An extension request is already waiting for approval.", frappe.PermissionError)
    extension_units = _required_int_for_storage(payload.get("extension_days"), "Extension")
    comment = _required_text(payload.get("comment"), "Extension comment")
    now = _utcnow()
    workflow.status = STATE_WAITING_EXTENSION_APPROVAL
    workflow.current_node = SRS_NODE_SRS_DIRECTOR_APPROVAL
    workflow.updated_at = now
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_EXTENSION_DEADLINE, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=actor)
    _set_node_state(workflow, SRS_NODE_SRS_DIRECTOR_APPROVAL, NODE_STATUS_WAITING_APPROVAL, actor=actor)
    _create_approval(workflow, "PMDP_EXTENSION_APPROVAL", actor, deadline_units=extension_units, comments=comment, assigned_to_user=actor)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_SRS_DIRECTOR_APPROVAL, "current_responsible_user": ""})
    notify_many(
        _active_users_with_role("SRS Manager"),
        title="PMDP extension approval required",
        message="A Case 3 physical build extension request is waiting for approval.",
        notification_type="PMDP_EXTENSION_APPROVAL_REQUIRED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_SRS_DIRECTOR_APPROVAL,
        action_url="/approvals",
        priority="High",
    )
    _log("srs_pmdp_extension_requested", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_EXTENSION_DEADLINE, message=comment)
    return {"success": True, "trainer_item": trainer_item}


def approve_pmdp_extension_as_srs_manager(trainer_item: str, payload: dict[str, Any], actor: str, approval_name: str | None = None) -> dict[str, Any]:
    import frappe

    _require_role(actor, "SRS Manager")
    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_transition_prerequisites("extension_approve", workflow, actor)
    approval_name = approval_name or frappe.db.get_value("SRS Approval", {"workflow_instance": workflow.name, "approval_type": "PMDP_EXTENSION_APPROVAL", "status": "WAITING"}, "name")
    if not approval_name:
        frappe.throw("Extension approval is not available.", frappe.PermissionError)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    extension_units = _required_int_for_storage(payload.get("deadline_proposal_days") or approval.original_deadline_proposal_days, "Extension")
    result = extend_active_deadline(trainer_item, SRS_NODE_CASE_3, extension_units)
    approval.status = "APPROVED_WITH_EDITS" if payload.get("deadline_proposal_days") else "APPROVED"
    approval.edited_deadline_proposal_days = extension_units
    approval.comments = str(approval.comments or "")[:500]
    approval.approved_by = actor
    approval.approved_at = _utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    workflow.status = STATE_PMDP_READY
    workflow.current_node = SRS_NODE_PMDP
    workflow.updated_at = approval.approved_at
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_EXTENSION_DEADLINE, NODE_STATUS_COMPLETED, actor=actor)
    _set_node_state(workflow, SRS_NODE_SRS_DIRECTOR_APPROVAL, NODE_STATUS_COMPLETED, actor=actor)
    _set_node_state(workflow, SRS_NODE_CASE_3, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner, deadline=result)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_PMDP, "current_responsible_user": workflow.project_owner})
    notify_many(
        [workflow.project_owner],
        title="PMDP extension approved",
        message=f"{deadline_quantity_label(result.get('effective_units'))} remain after the approved extension.",
        notification_type="PMDP_EXTENSION_APPROVED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_PMDP,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    _log("srs_pmdp_extension_approved", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_SRS_DIRECTOR_APPROVAL)
    return {"success": True, "trainer_item": trainer_item}


def submit_pmdp_path(trainer_item: str, pmdp_path: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_owner_or_team_member(workflow, actor, SRS_NODE_PMDP)
    _assert_transition_prerequisites("submit_pmdp", workflow, actor)
    if workflow.pmdp_path:
        frappe.throw("PMDP path has already been submitted.", frappe.PermissionError)
    path = str(pmdp_path or "").strip()
    if not path:
        raise ValueError("PMDP path is required.")
    now = _utcnow()
    complete_deadlines(trainer_item, SRS_NODE_CASE_3)
    workflow.pmdp_path = path
    workflow.pmdp_submitted_by = actor
    workflow.pmdp_submitted_at = now
    workflow.status = STATE_ACTION_PATHS
    workflow.current_node = SRS_NODE_BMDP
    workflow.updated_at = now
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_PHYSICAL_BUILD_TEST, NODE_STATUS_COMPLETED, actor=actor, responsible_user=actor)
    _set_node_state(workflow, SRS_NODE_PMDP, NODE_STATUS_COMPLETED, actor=actor, responsible_user=actor)
    if _node_status(workflow, SRS_NODE_EXTENSION_DEADLINE) != NODE_STATUS_COMPLETED:
        _set_node_state(workflow, SRS_NODE_EXTENSION_DEADLINE, NODE_STATUS_NOT_APPLICABLE, actor=actor)
    if _node_status(workflow, SRS_NODE_SRS_DIRECTOR_APPROVAL) != NODE_STATUS_COMPLETED:
        _set_node_state(workflow, SRS_NODE_SRS_DIRECTOR_APPROVAL, NODE_STATUS_NOT_APPLICABLE, actor=actor)
    _set_node_state(workflow, SRS_NODE_BMDP, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_BMDP, "current_responsible_user": workflow.project_owner})
    notify_many(
        [workflow.project_owner],
        title="BMDP active",
        message="PMDP is submitted. Submit the final BMDP path to complete Case 3.",
        notification_type="PMDP_SUBMITTED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_BMDP,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    _log("srs_pmdp_path_submitted", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_PMDP)
    return {"success": True, "trainer_item": trainer_item}


def submit_srs_bmdp_path(trainer_item: str, bmdp_path: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    if not (workflow.project_owner == actor or _is_selected_srs_team_member(workflow, actor)):
        frappe.throw("Only the Project Owner or a selected SRS team member can submit the BMDP path.", frappe.PermissionError)
    _assert_transition_prerequisites("submit_bmdp", workflow, actor)
    if workflow.bmdp_path:
        frappe.throw("BMDP path has already been submitted.", frappe.PermissionError)
    path = str(bmdp_path or "").strip()
    if not path:
        raise ValueError("BMDP path is required.")
    doc = frappe.get_doc(
        {
            "doctype": "SRS BMDP Submission",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": trainer_item,
            "bmdp_path": path,
            "submitted_by": actor,
            "submitted_at": _utcnow(),
            "status": "SUBMITTED",
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    complete_deadlines(trainer_item, SRS_NODE_BMDP)
    _set_completed_case_states(workflow, workflow.case_classification, actor)
    _set_node_state(workflow, SRS_NODE_BMDP, NODE_STATUS_COMPLETED, actor=actor, responsible_user=actor)
    workflow.bmdp_path = path
    workflow.status = STATE_COMPLETE
    workflow.current_node = SRS_NODE_BMDP
    workflow.completed_at = _utcnow()
    workflow.updated_at = workflow.completed_at
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value(
        "BEDO Trainer Item",
        trainer_item,
        {"status": ITEM_STATUS_SRS_COMPLETE, "current_node": SRS_NODE_BMDP, "current_responsible_user": ""},
    )
    _ensure_command_center_handoff(workflow, actor=actor, notify=True)
    report_to = frappe.get_all("BEDO Trainer Item Report To", filters={"trainer_item": trainer_item}, pluck="user")
    notify_many(
        report_to,
        title="SRS complete",
        message="BMDP is submitted. SRS is complete and the Command Center handoff is ready.",
        notification_type="SRS_WORKFLOW_COMPLETED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_BMDP,
        action_url=project_action_url("gm", workflow.project, trainer_item),
        priority="Normal",
    )
    _log("srs_bmdp_path_submitted", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_BMDP)
    return {"success": True, "trainer_item": trainer_item}


def _command_center_case_and_deadline(payload: dict[str, Any], *, fallback_case: str = "", fallback_deadline: Any = None) -> tuple[str, int]:
    command_case = str(payload.get("command_center_case") or payload.get("case_classification") or fallback_case or "").strip()
    if command_case not in COMMAND_CENTER_CASES:
        raise ValueError("Select a valid Command Center Case.")
    if command_case == COMMAND_CENTER_CASE_3:
        return command_case, 0
    deadline_source = payload.get("deadline_days") or payload.get("deadline_proposal_days") or fallback_deadline
    return command_case, _required_int_for_storage(deadline_source, "Deadline")


def _handoff_status_after_command_center_gm_approval(command_case: str) -> str:
    if command_case == COMMAND_CENTER_CASE_1:
        return COMMAND_CENTER_HANDOFF_IN_PROGRESS
    if command_case == COMMAND_CENTER_CASE_2:
        return COMMAND_CENTER_HANDOFF_ROUTED_TO_SUPPLIERS
    if command_case == COMMAND_CENTER_CASE_3:
        return COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_PENDING
    return COMMAND_CENTER_HANDOFF_PENDING


def submit_command_center_srs_ard_decision(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    if not _is_command_center_representative(actor):
        frappe.throw("Command Center Representative access is required.", frappe.PermissionError)
    if workflow.status != STATE_COMPLETE or workflow.current_node != SRS_NODE_BMDP:
        frappe.throw("SRS must be complete at BMDP before Command Center handoff decisions.", frappe.PermissionError)
    handoff = _handoff_for_item(trainer_item) or _ensure_command_center_handoff(workflow, actor=actor)
    if handoff.status != COMMAND_CENTER_HANDOFF_PENDING:
        frappe.throw("Command Center decision is not available for this handoff.", frappe.PermissionError)
    if frappe.db.exists(
        "SRS Approval",
        {
            "command_center_handoff": handoff.name,
            "approval_type": COMMAND_CENTER_SRS_ARD_GM_APPROVAL,
            "status": "WAITING",
        },
    ):
        frappe.throw("A GM approval is already waiting for this handoff.", frappe.PermissionError)

    command_case, deadline_days = _command_center_case_and_deadline(payload)
    notes = str(payload.get("notes") or payload.get("comments") or "")[:500]
    now = _utcnow()
    approval = frappe.get_doc(
        {
            "doctype": "SRS Approval",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": trainer_item,
            "command_center_handoff": handoff.name,
            "approval_department": _approval_department_for_type(COMMAND_CENTER_SRS_ARD_GM_APPROVAL),
            "approval_type": COMMAND_CENTER_SRS_ARD_GM_APPROVAL,
            "status": "WAITING",
            "required_role": "General Manager",
            "assigned_to_user": actor,
            "original_case_classification": command_case,
            "original_deadline_proposal_days": deadline_days,
            "comments": notes or "Command Center SRS to ARD handoff decision.",
        }
    )
    approval.flags.ignore_permissions = True
    approval.insert(ignore_permissions=True)

    handoff.command_center_case = command_case
    handoff.deadline_days = deadline_days
    handoff.responsible_user = actor
    handoff.submitted_by = actor
    handoff.submitted_at = now
    handoff.gm_approval = approval.name
    handoff.status = COMMAND_CENTER_HANDOFF_WAITING_GM
    handoff.notes = notes
    handoff.flags.ignore_permissions = True
    handoff.save(ignore_permissions=True)

    notify_many(
        _active_users_with_role("General Manager"),
        title="Command Center handoff approval required",
        message="A Command Center SRS to ARD handoff decision is waiting for GM approval.",
        notification_type="GM_APPROVAL_REQUIRED",
        project=workflow.project,
        trainer_item=trainer_item,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
        action_url="/approvals",
        priority="High",
    )
    _log_workflow(
        "command_center_srs_ard_decision_submitted",
        actor,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
        message=command_case,
    )
    return {"success": True, "trainer_item": trainer_item, "handoff": handoff.name}


def submit_command_center_approval(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    return submit_command_center_srs_ard_decision(trainer_item, payload, actor)


def _payload_datetime(value: Any, label: str) -> datetime:
    if isinstance(value, datetime):
        return value
    text = _required_text(value, label)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{label} must be a valid date and time.")


def _payload_user_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(part).strip() for part in value if str(part).strip()]
    return []


def schedule_case3_handover_meeting(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe
    from bedo_platform.services.meeting_service import schedule_case3_handover_meeting as schedule_meeting

    _assert_item_access(actor, trainer_item)
    if not _is_command_center_representative(actor):
        frappe.throw("Command Center Representative access is required.", frappe.PermissionError)
    handoff = _handoff_for_item(trainer_item)
    if not handoff:
        frappe.throw("Command Center handoff not found.", frappe.DoesNotExistError)
    if handoff.responsible_user != actor:
        frappe.throw("Only the responsible Command Center user can schedule this handover meeting.", frappe.PermissionError)
    if handoff.command_center_case != COMMAND_CENTER_CASE_3:
        frappe.throw("Handover meetings are only available for Case 3.", frappe.PermissionError)
    if handoff.status not in {
        COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_PENDING,
        COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_SCHEDULED,
    }:
        frappe.throw("Case 3 handover meeting scheduling is not available for this handoff.", frappe.PermissionError)

    scheduled_at = _payload_datetime(payload.get("scheduled_at"), "Meeting date and time")
    colleagues = _payload_user_list(payload.get("command_center_colleagues") or payload.get("colleagues"))
    result = schedule_meeting(
        handoff=handoff,
        scheduled_at=scheduled_at,
        actor=actor,
        command_center_colleagues=colleagues,
    )
    handoff.handover_meeting = result["meeting"]
    handoff.status = COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_SCHEDULED
    handoff.flags.ignore_permissions = True
    handoff.save(ignore_permissions=True)
    _log_workflow(
        "handover_meeting_scheduled",
        actor,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
        message=str(result.get("meeting_id") or ""),
    )
    return {"success": True, "trainer_item": trainer_item, "handoff": handoff.name, **result}


def confirm_case3_handover_meeting(meeting: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe
    from bedo_platform.services.meeting_service import confirm_meeting_attendance

    selected_users = _payload_user_list(payload.get("selected_users") or payload.get("users"))
    result = confirm_meeting_attendance(meeting, selected_users, actor)
    if result.get("all_required_confirmed"):
        handoff_name = frappe.db.get_value(
            "BEDO Command Center Handoff",
            {"handover_meeting": meeting, "is_active": 1},
            "name",
        )
        if handoff_name:
            handoff = frappe.get_doc("BEDO Command Center Handoff", handoff_name)
            if handoff.status == COMMAND_CENTER_HANDOFF_HANDOVER_MEETING_SCHEDULED:
                handoff.status = COMMAND_CENTER_HANDOFF_HANDOVER_CONFIRMATION_PENDING
                handoff.flags.ignore_permissions = True
                handoff.save(ignore_permissions=True)
    return result


def submit_case3_handover_confirmation(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    if not _is_command_center_representative(actor):
        frappe.throw("Command Center Representative access is required.", frappe.PermissionError)
    handoff = _handoff_for_item(trainer_item)
    if not handoff:
        frappe.throw("Command Center handoff not found.", frappe.DoesNotExistError)
    if handoff.responsible_user != actor:
        frappe.throw("Only the responsible Command Center user can submit the handover confirmation.", frappe.PermissionError)
    if handoff.command_center_case != COMMAND_CENTER_CASE_3 or handoff.status != COMMAND_CENTER_HANDOFF_HANDOVER_CONFIRMATION_PENDING:
        frappe.throw("Handover confirmation is not available for this handoff.", frappe.PermissionError)

    action = str(payload.get("action") or payload.get("outcome") or "").strip().lower().replace("-", "_")
    now = _utcnow()
    if action in {"success", "successful", "handover_successful"}:
        handoff.status = COMMAND_CENTER_HANDOFF_READY_FOR_ARD
        handoff.handover_confirmation_status = "SUCCESSFUL"
        handoff.handover_confirmed_by = actor
        handoff.handover_confirmed_at = now
        handoff.completed_by = actor
        handoff.completed_at = now
        handoff.flags.ignore_permissions = True
        handoff.save(ignore_permissions=True)
        from bedo_platform.services.ard_workflow_service import start_ard_workflow_from_handoff

        start_ard_workflow_from_handoff(handoff, actor)
        notify_many(
            _active_users_with_role("ARD Manager"),
            title="Handover successful",
            message="Command Center confirmed the Case 3 handover was successful.",
            notification_type="HANDOVER_SUCCESSFUL",
            project=handoff.project,
            trainer_item=handoff.trainer_item,
            workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
            node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
            action_url=project_action_url("ard", handoff.project, handoff.trainer_item),
            priority="High",
        )
        _log_workflow("handover_successful", actor, workflow_type=COMMAND_CENTER_WORKFLOW_TYPE, project=handoff.project, trainer_item=trainer_item, node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD)
        return {"success": True, "trainer_item": trainer_item, "handoff": handoff.name}

    if action in {"failed", "failure", "handover_failed"}:
        description = _required_text(payload.get("description") or payload.get("reason") or payload.get("comments"), "Failure description")
        approval_name = frappe.db.get_value(
            "SRS Approval",
            {
                "command_center_handoff": handoff.name,
                "approval_type": HANDOVER_FAILURE_GM_APPROVAL,
                "status": "WAITING",
            },
            "name",
        )
        if not approval_name:
            approval = frappe.get_doc(
                {
                    "doctype": "SRS Approval",
                    "workflow_instance": handoff.srs_workflow_instance,
                    "project": handoff.project,
                    "trainer_item": handoff.trainer_item,
                    "command_center_handoff": handoff.name,
                    "approval_department": _approval_department_for_type(HANDOVER_FAILURE_GM_APPROVAL),
                    "approval_type": HANDOVER_FAILURE_GM_APPROVAL,
                    "status": "WAITING",
                    "required_role": "General Manager",
                    "assigned_to_user": actor,
                    "original_case_classification": handoff.command_center_case,
                    "original_deadline_proposal_days": 0,
                    "comments": description[:500],
                }
            )
            approval.flags.ignore_permissions = True
            approval.insert(ignore_permissions=True)
            approval_name = approval.name
        handoff.status = COMMAND_CENTER_HANDOFF_HANDOVER_FAILED_WAITING_GM
        handoff.handover_confirmation_status = "WAITING_GM_DECISION"
        handoff.handover_failure_description = description[:500]
        handoff.handover_failed_by = actor
        handoff.handover_failed_at = now
        handoff.gm_approval = approval_name
        handoff.flags.ignore_permissions = True
        handoff.save(ignore_permissions=True)
        notify_many(
            _active_users_with_role("General Manager"),
            title="Handover failed",
            message="Command Center reported a failed Case 3 handover. GM decision is required.",
            notification_type="HANDOVER_FAILURE_APPROVAL_REQUIRED",
            project=handoff.project,
            trainer_item=handoff.trainer_item,
            workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
            node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
            action_url="/approvals",
            priority="High",
        )
        _log_workflow("handover_failed", actor, workflow_type=COMMAND_CENTER_WORKFLOW_TYPE, project=handoff.project, trainer_item=trainer_item, node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD, message=description)
        return {"success": True, "trainer_item": trainer_item, "handoff": handoff.name, "approval": approval_name}

    frappe.throw("Select Handover Successful or Handover Failed.", frappe.PermissionError)


def _create_command_center_deadline(handoff, actor: str, deadline_days: int) -> dict[str, Any]:
    deadline = create_deadline(
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        node_id=COMMAND_CENTER_CASE_1_NODE,
        triggered_by=actor,
        deadline_days=deadline_days,
    )
    handoff.deadline = deadline["name"]
    handoff.approved_deadline_days = deadline_days
    handoff.status = COMMAND_CENTER_HANDOFF_IN_PROGRESS
    handoff.flags.ignore_permissions = True
    handoff.save(ignore_permissions=True)
    return deadline


def _create_supplier_file_for_handoff(handoff, actor: str, deadline_days: int):
    import frappe

    deadline = create_deadline(
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        workflow_type=SUPPLIERS_WORKFLOW_TYPE,
        node_id=SUPPLIER_CASE_2_NODE,
        triggered_by=actor,
        deadline_days=deadline_days,
    )
    existing = frappe.db.get_value("BEDO Supplier File", {"source_handoff": handoff.name, "is_active": 1}, "name")
    supplier = frappe.get_doc("BEDO Supplier File", existing) if existing else frappe.new_doc("BEDO Supplier File")
    supplier.project = handoff.project
    supplier.trainer_item = handoff.trainer_item
    supplier.source_type = "COMMAND_CENTER_SRS_TO_ARD"
    supplier.source_handoff = handoff.name
    supplier.status = SUPPLIER_FILE_IN_PROGRESS
    supplier.responsible_user = handoff.responsible_user
    supplier.deadline = deadline["name"]
    supplier.deadline_days = deadline_days
    supplier.started_at = supplier.started_at or _utcnow()
    supplier.details = handoff.notes or ""
    supplier.is_active = 1
    supplier.flags.ignore_permissions = True
    if existing:
        supplier.save(ignore_permissions=True)
    else:
        supplier.insert(ignore_permissions=True)

    handoff.deadline = deadline["name"]
    handoff.approved_deadline_days = deadline_days
    handoff.status = COMMAND_CENTER_HANDOFF_ROUTED_TO_SUPPLIERS
    handoff.flags.ignore_permissions = True
    handoff.save(ignore_permissions=True)
    return supplier, deadline


def approve_command_center_srs_ard_gm_approval(approval_name: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.approval_type not in {COMMAND_CENTER_SRS_ARD_GM_APPROVAL, "COMMAND_CENTER_GM_APPROVAL"}:
        frappe.throw("Unsupported approval type.", frappe.PermissionError)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    _assert_item_access(actor, approval.trainer_item)
    workflow = _workflow_for_item(approval.trainer_item)
    handoff_name = getattr(approval, "command_center_handoff", "") or frappe.db.get_value(
        "BEDO Command Center Handoff",
        {"trainer_item": approval.trainer_item, "is_active": 1},
        "name",
    )
    handoff = frappe.get_doc("BEDO Command Center Handoff", handoff_name) if handoff_name else _ensure_command_center_handoff(workflow, actor=actor)
    if handoff.status not in {COMMAND_CENTER_HANDOFF_WAITING_GM, COMMAND_CENTER_HANDOFF_PENDING}:
        frappe.throw("This handoff is not waiting for GM approval.", frappe.PermissionError)

    command_case, deadline_days = _command_center_case_and_deadline(
        payload,
        fallback_case=approval.original_case_classification or handoff.command_center_case,
        fallback_deadline=approval.original_deadline_proposal_days or handoff.deadline_days,
    )
    now = _utcnow()
    approval.status = "APPROVED_WITH_EDITS" if payload.get("case_classification") or payload.get("command_center_case") or payload.get("deadline_proposal_days") or payload.get("deadline_days") else "APPROVED"
    approval.edited_case_classification = command_case
    approval.edited_deadline_proposal_days = deadline_days
    approval.comments = str(payload.get("comments") or approval.comments or "")[:500]
    approval.approved_by = actor
    approval.approved_at = now
    approval.command_center_handoff = handoff.name
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)

    handoff.command_center_case = command_case
    handoff.deadline_days = handoff.deadline_days or int(approval.original_deadline_proposal_days or 0)
    handoff.approved_deadline_days = deadline_days
    handoff.gm_approval = approval.name
    handoff.gm_approved_by = actor
    handoff.gm_approved_at = now
    handoff.flags.ignore_permissions = True
    handoff.save(ignore_permissions=True)

    if command_case == COMMAND_CENTER_CASE_1:
        _create_command_center_deadline(handoff, actor, deadline_days)
        title = "Command Center execution approved"
        message = f"GM approved Case 1 with {deadline_quantity_label(deadline_days)}."
    elif command_case == COMMAND_CENTER_CASE_2:
        supplier, _deadline = _create_supplier_file_for_handoff(handoff, actor, deadline_days)
        approval.supplier_file = supplier.name
        approval.flags.ignore_permissions = True
        approval.save(ignore_permissions=True)
        title = "Supplier delivery file opened"
        message = f"GM approved Case 2 with {deadline_quantity_label(deadline_days)}. Supplier tracking is active."
    else:
        handoff.status = _handoff_status_after_command_center_gm_approval(command_case)
        handoff.case3_cleared_at = now
        handoff.handover_confirmation_status = "NOT_STARTED"
        handoff.completed_by = ""
        handoff.completed_at = None
        handoff.deadline = ""
        handoff.approved_deadline_days = 0
        handoff.flags.ignore_permissions = True
        handoff.save(ignore_permissions=True)
        title = "Handover meeting required"
        message = "GM approved direct delivery to ARD. Schedule the Case 3 Handover Meeting before ARD starts."

    notify_many(
        [handoff.responsible_user],
        title=title,
        message=message,
        notification_type="COMMAND_CENTER_GM_APPROVED",
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
        action_url=project_action_url("command-center", handoff.project, handoff.trainer_item),
        priority="High",
    )
    _log_workflow(
        "command_center_srs_ard_gm_approved",
        actor,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD,
        message=f"{command_case}; deadline={deadline_days}",
        target_user=handoff.responsible_user,
    )
    return {"success": True, "trainer_item": handoff.trainer_item, "handoff": handoff.name}


def approve_srs_final_gm_approval(trainer_item: str, payload: dict[str, Any], actor: str, approval_name: str | None = None) -> dict[str, Any]:
    import frappe

    workflow = _workflow_for_item(trainer_item)
    approval_name = approval_name or frappe.db.get_value(
        "SRS Approval",
        {"workflow_instance": workflow.name, "approval_type": "COMMAND_CENTER_GM_APPROVAL", "status": "WAITING"},
        "name",
    )
    if not approval_name:
        frappe.throw("Final GM approval is not available or has already been completed.", frappe.PermissionError)
    return approve_command_center_srs_ard_gm_approval(approval_name, payload, actor)


def complete_command_center_case_1(trainer_item: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    handoff = _handoff_for_item(trainer_item)
    if not handoff:
        frappe.throw("Command Center handoff not found.", frappe.DoesNotExistError)
    if handoff.responsible_user != actor:
        frappe.throw("Only the responsible Command Center user can complete this handoff.", frappe.PermissionError)
    if handoff.command_center_case != COMMAND_CENTER_CASE_1 or handoff.status != COMMAND_CENTER_HANDOFF_IN_PROGRESS:
        frappe.throw("Case 1 completion is not available for this handoff.", frappe.PermissionError)
    if handoff.deadline:
        complete_deadlines(trainer_item, COMMAND_CENTER_CASE_1_NODE)
    now = _utcnow()
    handoff.status = COMMAND_CENTER_HANDOFF_COMPLETED
    handoff.completed_by = actor
    handoff.completed_at = now
    handoff.flags.ignore_permissions = True
    handoff.save(ignore_permissions=True)
    from bedo_platform.services.ard_workflow_service import start_ard_workflow_from_handoff

    start_ard_workflow_from_handoff(handoff, actor)
    notify_many(
        _active_users_with_role("General Manager"),
        title="Command Center Case 1 complete",
        message="Command Center completed the Case 1 SRS to ARD handoff.",
        notification_type="COMMAND_CENTER_CASE_COMPLETE",
        project=handoff.project,
        trainer_item=trainer_item,
        workflow_type=COMMAND_CENTER_WORKFLOW_TYPE,
        node_id=COMMAND_CENTER_CASE_1_NODE,
        action_url=project_action_url("gm", handoff.project, trainer_item),
        priority="Normal",
    )
    _log_workflow("command_center_case_1_completed", actor, workflow_type=COMMAND_CENTER_WORKFLOW_TYPE, project=handoff.project, trainer_item=trainer_item, node_id=COMMAND_CENTER_CASE_1_NODE)
    return {"success": True, "trainer_item": trainer_item, "handoff": handoff.name}


def deliver_supplier_file(supplier_file: str, actor: str) -> dict[str, Any]:
    import frappe

    doc = _supplier_file_or_throw(supplier_file)
    _assert_item_access(actor, doc.trainer_item)
    if doc.responsible_user != actor:
        frappe.throw("Only the responsible user can deliver this Supplier file.", frappe.PermissionError)
    if doc.status == SUPPLIER_FILE_COMPLETED:
        frappe.throw("Supplier file has already been delivered.", frappe.PermissionError)
    now = _utcnow()
    if doc.deadline:
        complete_deadlines(doc.trainer_item, SUPPLIER_CASE_2_NODE)
    doc.status = SUPPLIER_FILE_COMPLETED
    doc.completed_by = actor
    doc.completed_at = now
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    if doc.source_handoff:
        handoff = _handoff_or_throw(doc.source_handoff)
        handoff.status = COMMAND_CENTER_HANDOFF_READY_FOR_ARD
        handoff.completed_by = actor
        handoff.completed_at = now
        handoff.flags.ignore_permissions = True
        handoff.save(ignore_permissions=True)
        from bedo_platform.services.ard_workflow_service import start_ard_workflow_from_handoff

        start_ard_workflow_from_handoff(handoff, actor)
    notify_many(
        _active_users_with_role("General Manager"),
        title="Supplier delivery complete",
        message="Supplier delivery for the SRS to ARD handoff has been completed.",
        notification_type="SUPPLIER_FILE_DELIVERED",
        project=doc.project,
        trainer_item=doc.trainer_item,
        workflow_type=SUPPLIERS_WORKFLOW_TYPE,
        node_id=SUPPLIER_CASE_2_NODE,
        action_url=project_action_url("gm", doc.project, doc.trainer_item),
        priority="Normal",
    )
    _log_workflow("supplier_file_delivered", actor, workflow_type=SUPPLIERS_WORKFLOW_TYPE, project=doc.project, trainer_item=doc.trainer_item, node_id=SUPPLIER_CASE_2_NODE)
    return {"success": True, "trainer_item": doc.trainer_item, "supplier_file": doc.name}


def request_supplier_deadline_extension(supplier_file: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    doc = _supplier_file_or_throw(supplier_file)
    _assert_item_access(actor, doc.trainer_item)
    if doc.responsible_user != actor:
        frappe.throw("Only the responsible user can request a Supplier deadline extension.", frappe.PermissionError)
    if doc.status == SUPPLIER_FILE_COMPLETED:
        frappe.throw("Completed Supplier files cannot request extensions.", frappe.PermissionError)
    if not doc.deadline:
        frappe.throw("This Supplier file does not have an active deadline.", frappe.PermissionError)
    if frappe.db.exists(
        "SRS Approval",
        {
            "supplier_file": doc.name,
            "deadline": doc.deadline,
            "approval_type": SUPPLIER_DEADLINE_EXTENSION_APPROVAL,
            "status": "WAITING",
        },
    ):
        frappe.throw("A Supplier extension request is already waiting for approval.", frappe.PermissionError)
    extension_units = _required_int_for_storage(payload.get("extension_days") or payload.get("deadline_proposal_days"), "Extension")
    reason = _required_text(payload.get("reason") or payload.get("comment"), "Extension reason")
    workflow = _workflow_for_item(doc.trainer_item)
    approval = frappe.get_doc(
        {
            "doctype": "SRS Approval",
            "workflow_instance": workflow.name,
            "project": doc.project,
            "trainer_item": doc.trainer_item,
            "supplier_file": doc.name,
            "deadline": doc.deadline,
            "node_id": SUPPLIER_CASE_2_NODE,
            "approval_department": _approval_department_for_type(SUPPLIER_DEADLINE_EXTENSION_APPROVAL),
            "approval_type": SUPPLIER_DEADLINE_EXTENSION_APPROVAL,
            "status": "WAITING",
            "required_role": "General Manager",
            "assigned_to_user": actor,
            "original_deadline_proposal_days": extension_units,
            "comments": reason[:500],
        }
    )
    approval.flags.ignore_permissions = True
    approval.insert(ignore_permissions=True)
    doc.status = SUPPLIER_FILE_WAITING_EXTENSION
    doc.latest_extension_approval = approval.name
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    notify_many(
        _active_users_with_role("General Manager"),
        title="Supplier deadline extension requested",
        message="A Supplier deadline extension request is waiting for GM approval.",
        notification_type="SUPPLIER_EXTENSION_APPROVAL_REQUIRED",
        project=doc.project,
        trainer_item=doc.trainer_item,
        workflow_type=SUPPLIERS_WORKFLOW_TYPE,
        node_id=SUPPLIER_CASE_2_NODE,
        action_url="/approvals",
        priority="High",
    )
    _log_workflow("supplier_extension_requested", actor, workflow_type=SUPPLIERS_WORKFLOW_TYPE, project=doc.project, trainer_item=doc.trainer_item, node_id=SUPPLIER_CASE_2_NODE, message=reason)
    return {"success": True, "trainer_item": doc.trainer_item, "supplier_file": doc.name, "approval": approval.name}


def approve_supplier_deadline_extension(approval_name: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.approval_type != SUPPLIER_DEADLINE_EXTENSION_APPROVAL:
        frappe.throw("Unsupported approval type.", frappe.PermissionError)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    supplier = _supplier_file_or_throw(getattr(approval, "supplier_file", ""))
    _assert_item_access(actor, supplier.trainer_item)
    if str(payload.get("action") or "").lower() == "deny":
        approval.status = "DENIED"
        approval.approved_by = actor
        approval.approved_at = _utcnow()
        approval.comments = str(payload.get("comments") or approval.comments or "")[:500]
        approval.flags.ignore_permissions = True
        approval.save(ignore_permissions=True)
        deadline_status = frappe.db.get_value("BEDO Deadline", supplier.deadline, "status") if supplier.deadline else ""
        supplier.status = SUPPLIER_FILE_OVERDUE if deadline_status == "OVERDUE" else SUPPLIER_FILE_IN_PROGRESS
        supplier.flags.ignore_permissions = True
        supplier.save(ignore_permissions=True)
        notify_many(
            [supplier.responsible_user],
            title="Supplier extension denied",
            message="GM denied the Supplier deadline extension request.",
            notification_type="SUPPLIER_EXTENSION_DENIED",
            project=supplier.project,
            trainer_item=supplier.trainer_item,
            workflow_type=SUPPLIERS_WORKFLOW_TYPE,
            node_id=SUPPLIER_CASE_2_NODE,
            action_url=project_action_url("command-center", supplier.project, supplier.trainer_item),
            priority="High",
        )
        _log_workflow("supplier_extension_denied", actor, workflow_type=SUPPLIERS_WORKFLOW_TYPE, project=supplier.project, trainer_item=supplier.trainer_item, node_id=SUPPLIER_CASE_2_NODE, target_user=supplier.responsible_user)
        return {"success": True, "trainer_item": supplier.trainer_item, "supplier_file": supplier.name}

    extension_units = _required_int_for_storage(payload.get("deadline_proposal_days") or payload.get("extension_units") or approval.original_deadline_proposal_days, "Extension")
    result = extend_deadline_by_name(approval.deadline, extension_units)
    approval.status = "APPROVED_WITH_EDITS" if payload.get("deadline_proposal_days") or payload.get("extension_units") else "APPROVED"
    approval.edited_deadline_proposal_days = extension_units
    approval.approved_by = actor
    approval.approved_at = _utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    supplier.status = SUPPLIER_FILE_IN_PROGRESS
    supplier.deadline_days = int(supplier.deadline_days or 0) + extension_units
    supplier.flags.ignore_permissions = True
    supplier.save(ignore_permissions=True)
    notify_many(
        [supplier.responsible_user],
        title="Supplier extension approved",
        message=f"GM approved {deadline_quantity_label(extension_units)}. {deadline_quantity_label(result.get('effective_units')) or 'No time'} remain.",
        notification_type="SUPPLIER_EXTENSION_APPROVED",
        project=supplier.project,
        trainer_item=supplier.trainer_item,
        workflow_type=SUPPLIERS_WORKFLOW_TYPE,
        node_id=SUPPLIER_CASE_2_NODE,
        action_url=project_action_url("command-center", supplier.project, supplier.trainer_item),
        priority="High",
    )
    _log_workflow("supplier_extension_approved", actor, workflow_type=SUPPLIERS_WORKFLOW_TYPE, project=supplier.project, trainer_item=supplier.trainer_item, node_id=SUPPLIER_CASE_2_NODE, message=f"Approved {deadline_quantity_label(extension_units)}", target_user=supplier.responsible_user)
    return {"success": True, "trainer_item": supplier.trainer_item, "supplier_file": supplier.name, "deadline": approval.deadline}


def approve_global_deadline_extension(approval_name: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.approval_type != GLOBAL_DEADLINE_EXTENSION_APPROVAL:
        frappe.throw("Unsupported approval type.", frappe.PermissionError)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    _assert_item_access(actor, approval.trainer_item)
    if not approval.deadline:
        frappe.throw("This approval is not linked to a deadline.", frappe.PermissionError)
    extension_units = _required_int_for_storage(payload.get("deadline_proposal_days") or payload.get("extension_units"), "Extension")
    result = extend_deadline_by_name(approval.deadline, extension_units)
    workflow = _workflow_for_item(approval.trainer_item)
    node_id = approval.node_id or frappe.db.get_value("BEDO Deadline", approval.deadline, "node_id") or ""
    state = _node_state(workflow.name, node_id) if node_id else None
    responsible = (state.responsible_user if state else "") or approval.assigned_to_user or workflow.project_owner or ""

    approval.status = "APPROVED"
    approval.edited_deadline_proposal_days = extension_units
    approval.approved_by = actor
    approval.approved_at = _utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)

    if state:
        _set_node_state(
            workflow,
            node_id,
            state.status or NODE_STATUS_IN_PROGRESS,
            actor=actor,
            responsible_user=responsible,
            deadline=result,
        )
        frappe.db.set_value("SRS Workflow Node State", state.name, "overdue_at", None, update_modified=False)

    recipients = {responsible, workflow.project_owner}
    recipients.update(frappe.get_all("SRS Item Team Member", filters={"trainer_item": approval.trainer_item}, pluck="user"))
    notify_many(
        sorted(user for user in recipients if user),
        title="Deadline extension approved",
        message=(
            f"GM approved a {deadline_quantity_label(extension_units)} extension for {_node_display_label(node_id)}. "
            f"{deadline_quantity_label(result.get('effective_units')) or 'No time'} remain."
        ),
        notification_type="DEADLINE_EXTENSION_APPROVED",
        project=workflow.project,
        trainer_item=approval.trainer_item,
        node_id=node_id,
        action_url=project_action_url("srs", workflow.project, approval.trainer_item),
        priority="High",
    )
    _log(
        "global_deadline_extension_approved",
        actor,
        project=workflow.project,
        trainer_item=approval.trainer_item,
        node_id=node_id,
        message=f"Approved {deadline_quantity_label(extension_units)} for deadline {approval.deadline}",
        target_user=responsible,
    )
    return {
        "success": True,
        "trainer_item": approval.trainer_item,
        "deadline": approval.deadline,
        "extension_units": extension_units,
        "effective_units": result.get("effective_units"),
    }


def resolve_handover_failure_gm_approval(approval_name: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.approval_type != HANDOVER_FAILURE_GM_APPROVAL:
        frappe.throw("Unsupported approval type.", frappe.PermissionError)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    _assert_item_access(actor, approval.trainer_item)
    handoff_name = getattr(approval, "command_center_handoff", "") or frappe.db.get_value(
        "BEDO Command Center Handoff",
        {"trainer_item": approval.trainer_item, "is_active": 1},
        "name",
    )
    if not handoff_name:
        frappe.throw("Command Center handoff not found.", frappe.DoesNotExistError)
    handoff = frappe.get_doc("BEDO Command Center Handoff", handoff_name)
    if handoff.status != COMMAND_CENTER_HANDOFF_HANDOVER_FAILED_WAITING_GM:
        frappe.throw("This handover failure is not waiting for GM decision.", frappe.PermissionError)

    action = str(payload.get("action") or payload.get("decision") or "continue_anyway").strip().lower().replace("-", "_")
    now = _utcnow()
    approval.approved_by = actor
    approval.approved_at = now
    approval.flags.ignore_permissions = True
    if action in {"continue", "continue_anyway", "approve", "approved"}:
        approval.status = "APPROVED"
        approval.comments = str(payload.get("comments") or approval.comments or "GM continued the handover anyway.")[:500]
        approval.save(ignore_permissions=True)
        handoff.status = COMMAND_CENTER_HANDOFF_READY_FOR_ARD
        handoff.handover_confirmation_status = "CONTINUED_ANYWAY"
        handoff.handover_confirmed_by = actor
        handoff.handover_confirmed_at = now
        handoff.completed_by = actor
        handoff.completed_at = now
        handoff.flags.ignore_permissions = True
        handoff.save(ignore_permissions=True)
        from bedo_platform.services.ard_workflow_service import start_ard_workflow_from_handoff

        start_ard_workflow_from_handoff(handoff, actor)
        _log_workflow("handover_failure_continue_anyway", actor, workflow_type=COMMAND_CENTER_WORKFLOW_TYPE, project=handoff.project, trainer_item=handoff.trainer_item, node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD)
        return {"success": True, "trainer_item": handoff.trainer_item, "handoff": handoff.name}

    if action in {"reset", "reset_command_center"}:
        from bedo_platform.services.workflow_reset_service import reset_command_center

        approval.status = "APPROVED"
        approval.comments = str(payload.get("comments") or approval.comments or "GM reset the Command Center handoff.")[:500]
        approval.save(ignore_permissions=True)
        _log_workflow("handover_failure_reset_command_center", actor, workflow_type=COMMAND_CENTER_WORKFLOW_TYPE, project=handoff.project, trainer_item=handoff.trainer_item, node_id=COMMAND_CENTER_HANDOFF_TYPE_SRS_TO_ARD)
        return reset_command_center(handoff.trainer_item, actor, reason=approval.comments or "Handover failure reset")

    frappe.throw("Select Continue Anyway or Reset Command Center.", frappe.PermissionError)


def _approval_roles_for_actor(actor: str) -> set[str]:
    roles = set()
    if _is_gm(actor):
        roles.add("General Manager")
    if _is_srs_manager(actor):
        roles.add("SRS Manager")
    return roles


def _approval_node_for_type(approval_type: str) -> str:
    if approval_type == GLOBAL_DEADLINE_EXTENSION_APPROVAL:
        return ""
    if approval_type in {COMMAND_CENTER_SRS_ARD_GM_APPROVAL, SUPPLIER_DEADLINE_EXTENSION_APPROVAL, HANDOVER_FAILURE_GM_APPROVAL}:
        return ""
    if approval_type in {"GM_CASE_APPROVAL", "SRS_MANAGER_DEADLINE_APPROVAL"}:
        return SRS_NODE_DUAL_GATE_APPROVAL
    if approval_type in {"PMDP_DUAL_GATE_SRS_APPROVAL", "PMDP_DUAL_GATE_GM_APPROVAL"}:
        return SRS_NODE_PMDP_DUAL_GATE_APPROVAL
    if approval_type == "PMDP_EXTENSION_APPROVAL":
        return SRS_NODE_SRS_DIRECTOR_APPROVAL
    if approval_type == "COMMAND_CENTER_GM_APPROVAL":
        return SRS_NODE_FINAL_GM_APPROVAL
    return ""


def _approval_department_for_type(approval_type: str) -> str:
    if approval_type in {
        "COMMAND_CENTER_GM_APPROVAL",
        COMMAND_CENTER_SRS_ARD_GM_APPROVAL,
        "HANDOVER_FAILURE_GM_APPROVAL",
    }:
        return "Command Center"
    if approval_type == SUPPLIER_DEADLINE_EXTENSION_APPROVAL:
        return "Suppliers"
    if str(approval_type or "").startswith("ARD_"):
        return "ARD"
    return "SRS"


def _approval_is_actionable(row) -> bool:
    import frappe

    if row.status != "WAITING":
        return False
    if row.approval_type == COMMAND_CENTER_SRS_ARD_GM_APPROVAL:
        handoff_name = getattr(row, "command_center_handoff", "") or frappe.db.get_value(
            "BEDO Command Center Handoff",
            {"trainer_item": row.trainer_item, "is_active": 1},
            "name",
        )
        if not handoff_name:
            return False
        status = frappe.db.get_value("BEDO Command Center Handoff", handoff_name, "status")
        return status == COMMAND_CENTER_HANDOFF_WAITING_GM
    if row.approval_type == HANDOVER_FAILURE_GM_APPROVAL:
        handoff_name = getattr(row, "command_center_handoff", "") or frappe.db.get_value(
            "BEDO Command Center Handoff",
            {"trainer_item": row.trainer_item, "is_active": 1},
            "name",
        )
        if not handoff_name:
            return False
        status = frappe.db.get_value("BEDO Command Center Handoff", handoff_name, "status")
        return status == COMMAND_CENTER_HANDOFF_HANDOVER_FAILED_WAITING_GM
    if row.approval_type == ARD_INTERRUPTION_GM_APPROVAL:
        status = frappe.db.get_value("ARD Interruption Request", {"approval": row.name, "is_superseded": 0}, "status")
        return status == "WAITING_GM_APPROVAL"
    if row.approval_type == SUPPLIER_DEADLINE_EXTENSION_APPROVAL:
        supplier_file = getattr(row, "supplier_file", "")
        if not supplier_file:
            return False
        status = frappe.db.get_value("BEDO Supplier File", supplier_file, "status")
        return status == SUPPLIER_FILE_WAITING_EXTENSION
    if row.approval_type == GLOBAL_DEADLINE_EXTENSION_APPROVAL:
        deadline_name = getattr(row, "deadline", None)
        if not deadline_name:
            return False
        deadline = frappe.db.get_value("BEDO Deadline", deadline_name, ["status", "node_id"], as_dict=True)
        if not deadline or deadline.status != "OVERDUE":
            return False
        target_node = getattr(row, "node_id", None) or deadline.node_id
        node_status = frappe.db.get_value(
            "SRS Workflow Node State",
            {"workflow_instance": row.workflow_instance, "node_id": target_node},
            "status",
        )
        return node_status not in {NODE_STATUS_COMPLETED, NODE_STATUS_NOT_APPLICABLE}
    target_node = _approval_node_for_type(row.approval_type)
    if not target_node:
        return False
    workflow = frappe.db.get_value("SRS Workflow Instance", row.workflow_instance, ["current_node", "case_classification"], as_dict=True)
    if not workflow or workflow.current_node != target_node:
        return False
    node_status = frappe.db.get_value(
        "SRS Workflow Node State",
        {"workflow_instance": row.workflow_instance, "node_id": target_node},
        "status",
    )
    if node_status != NODE_STATUS_WAITING_APPROVAL:
        return False
    if row.approval_type == "GM_CASE_APPROVAL":
        srs_manager_approved_at = frappe.db.get_value("SRS Workflow Instance", row.workflow_instance, "srs_manager_approved_at")
        if not srs_manager_approved_at:
            return False
    if row.approval_type == "PMDP_DUAL_GATE_GM_APPROVAL":
        srs_rows = frappe.get_all(
            "SRS Approval",
            filters={"workflow_instance": row.workflow_instance, "approval_type": "PMDP_DUAL_GATE_SRS_APPROVAL"},
            fields=["status"],
            order_by="creation desc",
            page_length=1,
        )
        srs_status = srs_rows[0].status if srs_rows else ""
        if srs_status != "APPROVED":
            return False
    return True


def _approval_label(approval_type: str) -> str:
    if approval_type == "GM_CASE_APPROVAL":
        return "Dual Gate Approval"
    if approval_type == "SRS_MANAGER_DEADLINE_APPROVAL":
        return "Dual Gate Approval"
    if approval_type in {"PMDP_DUAL_GATE_SRS_APPROVAL", "PMDP_DUAL_GATE_GM_APPROVAL"}:
        return "PMDP Dual Gate Approval"
    if approval_type == "PMDP_EXTENSION_APPROVAL":
        return "Extension Deadline Approval"
    if approval_type == "COMMAND_CENTER_GM_APPROVAL":
        return "Command Center Decision Approval"
    if approval_type == COMMAND_CENTER_SRS_ARD_GM_APPROVAL:
        return "Command Center SRS to ARD Approval"
    if approval_type == HANDOVER_FAILURE_GM_APPROVAL:
        return "Handover Failure GM Decision"
    if approval_type == SUPPLIER_DEADLINE_EXTENSION_APPROVAL:
        return "Supplier Deadline Extension Approval"
    if approval_type == GLOBAL_DEADLINE_EXTENSION_APPROVAL:
        return "Overdue Deadline Extension"
    if approval_type == ARD_INTERRUPTION_GM_APPROVAL:
        return "ARD Interruption Approval"
    return approval_type.replace("_", " ").title()


def _approval_display_row(row) -> dict[str, Any]:
    import frappe

    project = frappe.db.get_value("BEDO Project", row.project, ["project_code", "project_name", "end_user", "po_deadline_date"], as_dict=True) or {}
    item = frappe.db.get_value("BEDO Trainer Item", row.trainer_item, ["trainer_item_name"], as_dict=True) or {}
    workflow = frappe.db.get_value(
        "SRS Workflow Instance",
        row.workflow_instance,
        ["current_node", "project_owner", "case_classification", "deadline_proposal_days", "approved_deadline_days", "pmdp_gate_submitted_by", "pmdp_gate_submitted_at"],
        as_dict=True,
    ) or {}
    submitted = frappe.db.get_value("SRS Deliverables Matrix", {"workflow_instance": row.workflow_instance}, ["submitted_by", "submitted_at"], as_dict=True) or {}
    submitted_by = submitted.get("submitted_by") or ""
    submitted_at = submitted.get("submitted_at")
    if row.approval_type in {"COMMAND_CENTER_GM_APPROVAL", COMMAND_CENTER_SRS_ARD_GM_APPROVAL, HANDOVER_FAILURE_GM_APPROVAL}:
        submitted_by = row.assigned_to_user or ""
        submitted_at = row.creation
    if row.approval_type == SUPPLIER_DEADLINE_EXTENSION_APPROVAL:
        submitted_by = row.assigned_to_user or ""
        submitted_at = row.creation
    if row.approval_type in {"PMDP_DUAL_GATE_SRS_APPROVAL", "PMDP_DUAL_GATE_GM_APPROVAL"}:
        submitted_by = workflow.get("pmdp_gate_submitted_by") or workflow.get("project_owner") or ""
        submitted_at = workflow.get("pmdp_gate_submitted_at") or row.creation
    if row.approval_type == "PMDP_EXTENSION_APPROVAL":
        submitted_by = row.assigned_to_user or workflow.get("project_owner") or ""
        submitted_at = row.creation
    deadline = {}
    target_node = ""
    responsible_user = ""
    if row.approval_type == GLOBAL_DEADLINE_EXTENSION_APPROVAL:
        deadline_name = getattr(row, "deadline", "")
        deadline = frappe.db.get_value("BEDO Deadline", deadline_name, ["node_id", "due_at", "status", "deadline_days"], as_dict=True) if deadline_name else {}
        target_node = getattr(row, "node_id", "") or (deadline or {}).get("node_id") or ""
        state = frappe.db.get_value(
            "SRS Workflow Node State",
            {"workflow_instance": row.workflow_instance, "node_id": target_node},
            ["responsible_user"],
            as_dict=True,
        ) or {}
        responsible_user = state.get("responsible_user") or row.assigned_to_user or workflow.get("project_owner") or ""
        submitted_by = responsible_user
        submitted_at = row.creation
    if row.approval_type == SUPPLIER_DEADLINE_EXTENSION_APPROVAL:
        deadline_name = getattr(row, "deadline", "")
        deadline = frappe.db.get_value("BEDO Deadline", deadline_name, ["node_id", "due_at", "status", "deadline_days"], as_dict=True) if deadline_name else {}
        target_node = getattr(row, "node_id", "") or (deadline or {}).get("node_id") or SUPPLIER_CASE_2_NODE
        responsible_user = row.assigned_to_user or ""
    return {
        "name": row.name,
        "approval_type": row.approval_type,
        "approval_department": getattr(row, "approval_department", "") or _approval_department_for_type(row.approval_type),
        "approval_label": _approval_label(row.approval_type),
        "status": row.status,
        "required_role": row.required_role,
        "project": row.project,
        "project_code": project.get("project_code") or "",
        "project_name": project.get("project_name") or "",
        "end_user": project.get("end_user") or "",
        "po_deadline_date": str(project.get("po_deadline_date") or ""),
        "trainer_item": row.trainer_item,
        "trainer_item_name": item.get("trainer_item_name") or "",
        "command_center_handoff": getattr(row, "command_center_handoff", "") or "",
        "supplier_file": getattr(row, "supplier_file", "") or "",
        "submitted_by": submitted_by,
        "submitted_by_name": _user_full_name(submitted_by),
        "submitted_at": to_cairo_iso(submitted_at),
        "project_owner": workflow.get("project_owner") or "",
        "project_owner_name": _user_full_name(workflow.get("project_owner")),
        "current_node": workflow.get("current_node") or "",
        "deadline": getattr(row, "deadline", "") or "",
        "target_node": target_node,
        "target_node_label": _node_display_label(target_node) if target_node else "",
        "responsible_user": responsible_user,
        "responsible_user_name": _user_full_name(responsible_user),
        "deadline_due_at": to_cairo_iso((deadline or {}).get("due_at")),
        "case_classification": row.edited_case_classification or (row.original_case_classification if row.approval_type in {"COMMAND_CENTER_GM_APPROVAL", COMMAND_CENTER_SRS_ARD_GM_APPROVAL, HANDOVER_FAILURE_GM_APPROVAL} else workflow.get("case_classification")) or row.original_case_classification or "",
        "deadline_proposal_days": 0 if row.approval_type == GLOBAL_DEADLINE_EXTENSION_APPROVAL else row.edited_deadline_proposal_days or (row.original_deadline_proposal_days if row.approval_type in {"COMMAND_CENTER_GM_APPROVAL", COMMAND_CENTER_SRS_ARD_GM_APPROVAL, HANDOVER_FAILURE_GM_APPROVAL, "PMDP_EXTENSION_APPROVAL", SUPPLIER_DEADLINE_EXTENSION_APPROVAL} else workflow.get("approved_deadline_days") or workflow.get("deadline_proposal_days")) or row.original_deadline_proposal_days or 0,
        "deadline_unit_label": deadline_unit_label(),
        "priority": "High" if row.approval_type in {"GM_CASE_APPROVAL", "PMDP_DUAL_GATE_GM_APPROVAL", "COMMAND_CENTER_GM_APPROVAL", COMMAND_CENTER_SRS_ARD_GM_APPROVAL, HANDOVER_FAILURE_GM_APPROVAL, ARD_INTERRUPTION_GM_APPROVAL, SUPPLIER_DEADLINE_EXTENSION_APPROVAL, GLOBAL_DEADLINE_EXTENSION_APPROVAL} else "Normal",
        "comments": row.comments or "",
        "created_at": to_cairo_iso(row.creation),
    }


def list_my_pending_approvals(actor: str, status: str = "WAITING") -> dict[str, Any]:
    import frappe

    roles = _approval_roles_for_actor(actor)
    if not roles:
        return {"approvals": [], "count": 0}
    filters: dict[str, Any] = {"required_role": ["in", sorted(roles)]}
    if status:
        filters["status"] = status
    rows = frappe.get_all(
        "SRS Approval",
        filters=filters,
        fields=[
            "name",
            "workflow_instance",
            "project",
            "trainer_item",
            "command_center_handoff",
            "supplier_file",
            "deadline",
            "node_id",
            "approval_department",
            "approval_type",
            "status",
            "required_role",
            "assigned_to_user",
            "original_case_classification",
            "edited_case_classification",
            "original_deadline_proposal_days",
            "edited_deadline_proposal_days",
            "comments",
            "creation",
        ],
        order_by="creation desc",
        page_length=100,
    )
    approvals = [_approval_display_row(row) for row in rows if can_view_trainer_item(actor, row.trainer_item) and _approval_is_actionable(row)]
    return {"approvals": approvals, "count": len(approvals)}


def get_pending_approval_count(actor: str) -> dict[str, int]:
    return {"count": int(list_my_pending_approvals(actor).get("count") or 0)}


def get_approval_detail(approval: str, actor: str) -> dict[str, Any]:
    import frappe

    if not frappe.db.exists("SRS Approval", approval):
        frappe.throw("Approval not found.", frappe.DoesNotExistError)
    doc = frappe.get_doc("SRS Approval", approval)
    if doc.required_role not in _approval_roles_for_actor(actor) or not can_view_trainer_item(actor, doc.trainer_item):
        frappe.throw("You do not have access to this approval.", frappe.PermissionError)
    if not _approval_is_actionable(doc):
        frappe.throw("Approval is not currently actionable.", frappe.PermissionError)
    return {"approval": _approval_display_row(doc)}


def approve_srs_approval(approval: str, actor: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    import frappe

    detail = get_approval_detail(approval, actor)["approval"]
    if detail["status"] != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    payload = payload or {}
    if detail["approval_type"] == "GM_CASE_APPROVAL":
        return approve_srs_case_as_gm(detail["trainer_item"], payload, actor, approval_name=approval)
    if detail["approval_type"] == "SRS_MANAGER_DEADLINE_APPROVAL":
        return approve_srs_deadline_as_srs_manager(detail["trainer_item"], payload, actor, approval_name=approval)
    if detail["approval_type"] == "PMDP_DUAL_GATE_SRS_APPROVAL":
        return approve_pmdp_dual_gate_as_srs_manager(detail["trainer_item"], payload, actor, approval_name=approval)
    if detail["approval_type"] == "PMDP_DUAL_GATE_GM_APPROVAL":
        return approve_pmdp_dual_gate_as_gm(detail["trainer_item"], payload, actor, approval_name=approval)
    if detail["approval_type"] == "PMDP_EXTENSION_APPROVAL":
        return approve_pmdp_extension_as_srs_manager(detail["trainer_item"], payload, actor, approval_name=approval)
    if detail["approval_type"] == "COMMAND_CENTER_GM_APPROVAL":
        return approve_srs_final_gm_approval(detail["trainer_item"], payload, actor, approval_name=approval)
    if detail["approval_type"] == COMMAND_CENTER_SRS_ARD_GM_APPROVAL:
        return approve_command_center_srs_ard_gm_approval(approval, payload, actor)
    if detail["approval_type"] == SUPPLIER_DEADLINE_EXTENSION_APPROVAL:
        return approve_supplier_deadline_extension(approval, payload, actor)
    if detail["approval_type"] == GLOBAL_DEADLINE_EXTENSION_APPROVAL:
        return approve_global_deadline_extension(approval, payload, actor)
    if detail["approval_type"] == HANDOVER_FAILURE_GM_APPROVAL:
        return resolve_handover_failure_gm_approval(approval, payload, actor)
    if detail["approval_type"] == ARD_INTERRUPTION_GM_APPROVAL:
        from bedo_platform.services.ard_workflow_service import resolve_ard_interruption_approval

        return resolve_ard_interruption_approval(approval, payload, actor)
    frappe.throw("Unsupported approval type.", frappe.PermissionError)


def approve_srs_approval_with_edits(approval: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    return approve_srs_approval(approval, actor, payload)


def get_srs_trainer_item_audit_trail(trainer_item: str, actor: str) -> dict[str, Any]:
    _assert_item_access(actor, trainer_item)
    import frappe

    rows = frappe.get_all(
        "BEDO Security Event",
        filters={"trainer_item": trainer_item},
        fields=["event_type", "user", "target_user", "node_id", "status", "message", "created_at"],
        order_by="created_at desc",
        page_length=100,
    )
    return {"events": rows}


list_projects = list_visible_projects
assign_project = assign_srs_project_owner
list_assignable_users = list_eligible_project_owners
