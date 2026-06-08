from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from bedo_platform.constants import (
    CASE_CLASSIFICATIONS,
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
    SRS_NODE_COORDINATION,
    SRS_NODE_DEADLINE_LOCKED,
    SRS_NODE_DELIVERABLES,
    SRS_NODE_GATEWAY,
    SRS_NODE_GM_APPROVAL,
    SRS_NODE_MANAGER_APPROVAL,
    SRS_NODE_PRODUCT_DIGITAL_RELEASE,
    SRS_PLACEHOLDER_NODES,
    SRS_ROLES,
    SRS_WORKFLOW_TYPE,
)
from bedo_platform.services.deadline_service import complete_deadlines, create_deadline, get_deadlines_for_trainer_item, server_now_iso, to_cairo_iso
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
STATE_COMPLETE = "SRS_COMPLETE"

CASE_1 = "Case 1 - Legacy Validation"
CASE_2 = "Case 2 - Standard Innovation"
CASE_3 = "Case 3 - Experimental Prototyping"
CASE_4 = "Case 4 - Vanguard Manufacturing"

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
        "label": "Deliverables Matrix",
        "lane": "study_phase",
        "column": "deadline_2",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_COORDINATION],
    },
    {
        "id": SRS_NODE_CASES_1_2,
        "label": "Cases 1,2",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_DELIVERABLES],
    },
    {
        "id": SRS_NODE_CASES_3_4,
        "label": "Cases 3,4",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_DELIVERABLES],
    },
    {
        "id": SRS_NODE_GM_APPROVAL,
        "label": "GM Approval",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "approval",
        "clickable": False,
        "requiredRoles": ["General Manager"],
        "requiredPreviousNodes": [SRS_NODE_DELIVERABLES],
    },
    {
        "id": SRS_NODE_MANAGER_APPROVAL,
        "label": "Gate 1: SRS Manager Deadline Approval",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "approval",
        "clickable": False,
        "requiredRoles": ["SRS Manager"],
        "requiredPreviousNodes": [SRS_NODE_DELIVERABLES],
    },
    {
        "id": SRS_NODE_DEADLINE_LOCKED,
        "label": "Deadline Locked in ERP",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "display",
        "clickable": False,
        "requiredPreviousNodes": [SRS_NODE_MANAGER_APPROVAL],
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
        "id": SRS_NODE_BMDP,
        "label": "BMDP",
        "lane": "study_phase",
        "column": "deadline_3",
        "kind": "input",
        "clickable": True,
        "requiredPreviousNodes": [SRS_NODE_MANAGER_APPROVAL, SRS_NODE_DEADLINE_LOCKED, SRS_NODE_ACTION_PATHS],
        "isTerminal": True,
    },
]

SRS_FLOWCHART_EDGES = [
    [SRS_NODE_PRODUCT_DIGITAL_RELEASE, SRS_NODE_GATEWAY],
    [SRS_NODE_GATEWAY, SRS_NODE_COORDINATION],
    [SRS_NODE_COORDINATION, SRS_NODE_DELIVERABLES],
    [SRS_NODE_DELIVERABLES, SRS_NODE_CASES_1_2],
    [SRS_NODE_DELIVERABLES, SRS_NODE_CASES_3_4],
    [SRS_NODE_CASES_1_2, SRS_NODE_MANAGER_APPROVAL],
    [SRS_NODE_CASES_3_4, SRS_NODE_GM_APPROVAL],
    [SRS_NODE_GM_APPROVAL, SRS_NODE_MANAGER_APPROVAL],
    [SRS_NODE_MANAGER_APPROVAL, SRS_NODE_DEADLINE_LOCKED],
    [SRS_NODE_DEADLINE_LOCKED, SRS_NODE_ACTION_PATHS],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_1],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_2],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_3],
    [SRS_NODE_ACTION_PATHS, SRS_NODE_CASE_4],
    [SRS_NODE_CASE_1, SRS_NODE_BMDP],
    [SRS_NODE_CASE_2, SRS_NODE_BMDP],
    [SRS_NODE_CASE_3, SRS_NODE_BMDP],
    [SRS_NODE_CASE_4, SRS_NODE_BMDP],
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


def _is_srs_manager(user: str) -> bool:
    return "SRS Manager" in _roles(user)


def _is_srs_user(user: str) -> bool:
    return bool(_roles(user) & SRS_ROLES)


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
    if status == NODE_STATUS_IN_PROGRESS and not doc.started_at:
        doc.started_at = datetime.utcnow()
    if status == NODE_STATUS_COMPLETED and not doc.completed_at:
        doc.completed_at = datetime.utcnow()
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
        _assert_node_completed(workflow, SRS_NODE_DELIVERABLES, actor, SRS_NODE_GM_APPROVAL)
        if workflow.case_classification not in GM_APPROVAL_CASES:
            message = "GM approval is only available for Case 3 or Case 4."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_GM_APPROVAL, message)
            frappe.throw(message, frappe.PermissionError)
        _assert_current_node(workflow, SRS_NODE_GM_APPROVAL, actor)
        _assert_node_status(workflow, SRS_NODE_GM_APPROVAL, {NODE_STATUS_WAITING_APPROVAL}, actor)
        return

    if action == "manager_approve":
        _assert_node_completed(workflow, SRS_NODE_DELIVERABLES, actor, SRS_NODE_MANAGER_APPROVAL)
        if workflow.case_classification in GM_APPROVAL_CASES:
            _assert_node_completed(workflow, SRS_NODE_GM_APPROVAL, actor, SRS_NODE_MANAGER_APPROVAL)
        _assert_current_node(workflow, SRS_NODE_MANAGER_APPROVAL, actor)
        _assert_node_status(workflow, SRS_NODE_MANAGER_APPROVAL, {NODE_STATUS_WAITING_APPROVAL}, actor)
        return

    if action == "submit_bmdp":
        _assert_node_completed(workflow, SRS_NODE_MANAGER_APPROVAL, actor, SRS_NODE_BMDP)
        _assert_node_completed(workflow, SRS_NODE_DEADLINE_LOCKED, actor, SRS_NODE_BMDP)
        _assert_node_status(workflow, SRS_NODE_ACTION_PATHS, {NODE_STATUS_IN_PROGRESS, NODE_STATUS_COMPLETED}, actor)
        if workflow.current_node not in {SRS_NODE_ACTION_PATHS, SRS_NODE_BMDP}:
            message = "BMDP is not available until Action Paths is active."
            _audit_invalid_transition_attempt(actor, workflow, SRS_NODE_BMDP, message)
            frappe.throw(message, frappe.PermissionError)
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
    if _is_gm(user):
        return True
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
    if _is_gm(user):
        return True
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
        return datetime.now(UTC).date().isoformat()


def _validate_project_payload(payload: dict[str, Any]) -> dict[str, str]:
    project_code = str(payload.get("project_code") or "").strip() or _project_fallback_code()
    return {
        "project_name": str(payload.get("project_name") or "").strip() or "Untitled Project",
        "project_code": project_code,
        "end_user": str(payload.get("end_user") or "").strip() or "Unspecified",
        "po_deadline_date": _project_date_or_default(payload.get("po_deadline_date")),
    }


def _unique_project_code(project_code: str, current_project: str = "") -> str:
    import frappe

    candidate = project_code
    suffix = 2
    while True:
        existing = frappe.db.get_value("BEDO Project", {"project_code": candidate}, "name")
        if not existing or existing == current_project:
            return candidate
        candidate = f"{project_code}-{suffix}"
        suffix += 1


def create_project(payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_gm(actor)
    data = _validate_project_payload(payload)
    data["project_code"] = _unique_project_code(data["project_code"])
    doc = frappe.get_doc(
        {
            "doctype": "BEDO Project",
            **data,
            "status": PROJECT_STATUS_DETAILS_FINALIZED,
            "created_by_user": actor,
            "created_at": datetime.utcnow(),
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
    data["project_code"] = _unique_project_code(data["project_code"], current_project=project)
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
    doc.finalized_at = datetime.utcnow()
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
                "added_at": datetime.utcnow(),
            }
        )
        doc.flags.ignore_permissions = True
        doc.insert(ignore_permissions=True)


def _positive_int_or_default(value: Any, default: int = 1) -> int:
    try:
        result = int(value or default)
    except (TypeError, ValueError):
        return default
    return result if result >= 1 else default


def _trainer_name_or_default(value: Any) -> str:
    return str(value or "").strip() or "Untitled Trainer"


def _create_trainer_item(project_doc, trainer_name: str, quantity: int, original_quantity: int, separation_mode: str, sequence_no: int, actor: str, report_to_users: list[str]) -> str:
    import frappe

    trainer_item_name = trainer_name if separation_mode != "SEPARATED" else f"{trainer_name}_{sequence_no}"
    doc = frappe.get_doc(
        {
            "doctype": "BEDO Trainer Item",
            "project": project_doc.name,
            "trainer_name": trainer_name,
            "trainer_item_name": trainer_item_name,
            "quantity": quantity,
            "original_quantity": original_quantity,
            "separation_mode": separation_mode,
            "sequence_no": sequence_no,
            "status": ITEM_STATUS_DRAFT,
            "current_pillar": "",
            "current_workflow": "",
            "current_node": "",
            "created_by_user": actor,
            "created_at": datetime.utcnow(),
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
    quantity = _positive_int_or_default(payload.get("quantity"))
    report_to_users = list(payload.get("report_to_users") or [])
    mode = str(payload.get("separation_mode") or ("SINGLE" if quantity == 1 else "")).strip().upper()
    if quantity == 1:
        mode = "SINGLE"
    if quantity > 1 and mode not in {"COMBINED", "SEPARATED"}:
        mode = "COMBINED"
    created = []
    if mode == "SEPARATED":
        for index in range(1, quantity + 1):
            created.append(_create_trainer_item(project_doc, trainer_name, 1, quantity, mode, index, actor, report_to_users))
    else:
        created.append(_create_trainer_item(project_doc, trainer_name, quantity, quantity, mode, 1, actor, report_to_users))
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
    quantity = _positive_int_or_default(payload.get("quantity"))
    doc.trainer_name = trainer_name
    doc.trainer_item_name = trainer_name if doc.separation_mode != "SEPARATED" else f"{trainer_name}_{doc.sequence_no or 1}"
    doc.quantity = quantity
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
            "BEDO Security Event",
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
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
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
    now = datetime.utcnow()
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
        if workflow.current_node in {SRS_NODE_GM_APPROVAL, SRS_NODE_MANAGER_APPROVAL}:
            counts[workflow.project]["waiting_approval"] += 1
        if workflow.current_node in {SRS_NODE_ACTION_PATHS, SRS_NODE_BMDP}:
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
    if _is_gm(actor):
        pass
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


def _safe_item(row) -> dict[str, Any]:
    return {
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


def _safe_node_state(row, display_data: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "display_data": display_data or {},
    }


def _node_display_data(workflow, team_members: list[dict[str, Any]], approvals: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not workflow:
        return {}
    gm_approval = approvals.get("GM_CASE_APPROVAL") or {}
    manager_approval = approvals.get("SRS_MANAGER_DEADLINE_APPROVAL") or {}
    team_count = len([member for member in team_members if not member.get("is_project_owner")])
    return {
        SRS_NODE_GATEWAY: {
            "Owner": _user_full_name(workflow.project_owner) or "Not assigned",
        },
        SRS_NODE_COORDINATION: {
            "Team": f"{team_count} additional member{'s' if team_count != 1 else ''}",
            "Case": workflow.case_classification or "Not selected",
            "Deadline": f"{workflow.deadline_proposal_days} working day(s)" if workflow.deadline_proposal_days else "Not proposed",
        },
        SRS_NODE_DELIVERABLES: {
            "Case": workflow.case_classification or "Not selected",
            "Deadline": f"{workflow.deadline_proposal_days} working day(s)" if workflow.deadline_proposal_days else "Not proposed",
        },
        SRS_NODE_GM_APPROVAL: {
            "Status": "Approved by General Manager" if workflow.gm_approved_at else "Pending GM Approval",
            "Case": workflow.case_classification or "",
            "Deadline": f"{workflow.deadline_proposal_days} working day(s)" if workflow.deadline_proposal_days else "",
            "Decision": gm_approval.get("status", ""),
        },
        SRS_NODE_MANAGER_APPROVAL: {
            "Status": "Approved by SRS Manager" if workflow.srs_manager_approved_at else "Pending SRS Manager Approval",
            "Case": workflow.case_classification or "",
            "Deadline": f"{workflow.approved_deadline_days or workflow.deadline_proposal_days or ''} working day(s)" if (workflow.approved_deadline_days or workflow.deadline_proposal_days) else "",
            "Decision": manager_approval.get("status", ""),
        },
        SRS_NODE_BMDP: {
            "Status": "BMDP submitted" if workflow.bmdp_path else "BMDP path required",
            "Path": str(workflow.bmdp_path or "")[:72],
        },
    }


def list_trainer_items_for_project(project: str, actor: str) -> dict[str, Any]:
    import frappe

    _assert_project_access(actor, project)
    filters: dict[str, Any] = {"project": project, "is_deleted": 0}
    if not (_is_gm(actor) or _is_srs_manager(actor)):
        allowed_items = _item_assignments_for_user(actor)
        filters["name"] = ["in", sorted(allowed_items) or ["__none__"]]
    rows = frappe.get_all(
        "BEDO Trainer Item",
        filters=filters,
        fields=["name", "project", "trainer_name", "trainer_item_name", "quantity", "original_quantity", "separation_mode", "sequence_no", "status", "current_node", "current_responsible_user", "released_to_srs_at"],
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
            {**_safe_item(row), "workflow": workflows.get(row.name), "deadline": deadlines.get(row.name)}
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
        node_states = frappe.get_all(
            "SRS Workflow Node State",
            filters={"workflow_instance": workflow.name},
            fields=["node_id", "status", "started_at", "completed_at", "deadline_start_at", "deadline_due_at", "deadline_days", "responsible_user"],
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
                fields=["name", "approval_type", "status", "required_role", "approved_by", "approved_at", "edited_case_classification", "edited_deadline_proposal_days"],
            )
        }
    display_data = _node_display_data(workflow, team_members, approvals)
    report_to = frappe.get_all("BEDO Trainer Item Report To", filters={"trainer_item": trainer_item}, fields=["user"])
    audit = frappe.get_all(
        "BEDO Security Event",
        filters={"trainer_item": trainer_item},
        fields=["event_type", "user", "target_user", "project", "trainer_item", "node_id", "status", "message", "created_at"],
        order_by="created_at desc",
        page_length=50,
    )
    tabs = ["Overview", "SRS", "ARD", "Command Center", "Production", "QC", "Operations", "Audit Log"] if _is_gm(actor) else ["SRS"]
    return {
        "project": _safe_project(project),
        "trainer_item": _safe_item(item),
        "workflow": dict(workflow.as_dict()) if workflow else None,
        "node_states": [_safe_node_state(row, display_data.get(row.node_id)) for row in node_states],
        "deadlines": get_deadlines_for_trainer_item(trainer_item),
        "node_availability": _node_availability(actor, workflow) if workflow else [],
        "server_now": server_now_iso(),
        "report_to_users": [row.user for row in report_to],
        "team_members": team_members,
        "approvals": list(approvals.values()),
        "audit_events": [dict(row) for row in audit],
        "tabs": tabs,
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
            {"id": "deadline_1", "label": "Deadline 1", "detail": "1 Day"},
            {"id": "deadline_2", "label": "Deadline 2", "detail": "2 Days"},
            {"id": "deadline_3", "label": "Deadline 3", "detail": "Depending on SRS Manager Approval"},
        ],
        "nodes": [dict(node) for node in SRS_FLOWCHART_NODE_DEFINITIONS],
        "edges": [{"from": source, "to": target} for source, target in SRS_FLOWCHART_EDGES],
        "case_classifications": CASE_CLASSIFICATIONS,
    }


def _node_definition(node_id: str) -> dict[str, Any]:
    return next((node for node in SRS_FLOWCHART_NODE_DEFINITIONS if node["id"] == node_id), {})


def _can_user_open_node(actor: str, workflow, node_id: str) -> bool:
    if node_id == SRS_NODE_GATEWAY:
        return _is_srs_manager(actor)
    if node_id == SRS_NODE_COORDINATION:
        return workflow.project_owner == actor
    if node_id == SRS_NODE_BMDP:
        return workflow.project_owner == actor or _is_selected_srs_team_member(workflow, actor)
    return False


def _node_disabled_reason(actor: str, workflow, node_id: str) -> str:
    definition = _node_definition(node_id)
    if not definition.get("clickable"):
        return "Display-only step."
    if not _can_user_open_node(actor, workflow, node_id):
        return "You do not have permission for this step."
    for previous in definition.get("requiredPreviousNodes") or []:
        if node_id == SRS_NODE_MANAGER_APPROVAL and previous == SRS_NODE_GM_APPROVAL and workflow.case_classification not in GM_APPROVAL_CASES:
            continue
        if node_id == SRS_NODE_BMDP and previous == SRS_NODE_ACTION_PATHS:
            if _node_status(workflow, SRS_NODE_ACTION_PATHS) in {NODE_STATUS_IN_PROGRESS, NODE_STATUS_COMPLETED}:
                continue
        if not _node_completed(workflow, previous):
            return "Complete the previous step first."
    if node_id == SRS_NODE_GM_APPROVAL and workflow.case_classification not in GM_APPROVAL_CASES:
        return "GM approval is not required for this case."
    if node_id == SRS_NODE_MANAGER_APPROVAL and workflow.case_classification in GM_APPROVAL_CASES and not _node_completed(workflow, SRS_NODE_GM_APPROVAL):
        return "Complete GM approval first."
    if node_id == SRS_NODE_BMDP and workflow.bmdp_path:
        return "BMDP has already been submitted."
    state = _node_status(workflow, node_id)
    if state not in {NODE_STATUS_IN_PROGRESS, NODE_STATUS_WAITING_APPROVAL, NODE_STATUS_READY}:
        return "This step is not active."
    if node_id != workflow.current_node and node_id != SRS_NODE_BMDP:
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
    workflow.updated_at = datetime.utcnow()
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
            "selected_at": datetime.utcnow(),
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
    additional = sorted(set(users or []))
    if not additional:
        raise ValueError("Select at least one additional SRS team member.")
    for user in additional:
        if not assert_user_can_login(user) or not (_roles(user) & SRS_ROLES):
            raise ValueError("Additional team members must be active SRS users.")
    _ensure_item_team_member(workflow, workflow.project_owner, actor, is_project_owner=True)
    for user in additional:
        _ensure_item_team_member(workflow, user, actor)
    complete_deadlines(trainer_item, SRS_NODE_COORDINATION)
    _set_node_state(workflow, SRS_NODE_COORDINATION, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_node_state(workflow, SRS_NODE_DELIVERABLES, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner)
    workflow.status = STATE_COORDINATION
    workflow.current_node = SRS_NODE_DELIVERABLES
    workflow.updated_at = datetime.utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_DELIVERABLES, "current_responsible_user": workflow.project_owner})
    _log("srs_team_selected", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_COORDINATION)
    return {"success": True, "trainer_item": trainer_item}


def submit_mandatory_coordination(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_workflow_action(actor, workflow, SRS_NODE_COORDINATION, allow_gm=False, allow_manager=False, allow_owner=True)
    _assert_transition_prerequisites("select_team", workflow, actor)
    if frappe.db.exists("SRS Item Team Member", {"workflow_instance": workflow.name, "is_project_owner": 0}):
        frappe.throw("SRS team has already been selected.", frappe.PermissionError)
    if frappe.db.exists("SRS Deliverables Matrix", {"workflow_instance": workflow.name}):
        frappe.throw("Coordination data has already been submitted.", frappe.PermissionError)

    additional = sorted(set(list(payload.get("users") or [])))
    if workflow.project_owner in additional:
        additional = [user for user in additional if user != workflow.project_owner]
    if not additional:
        raise ValueError("Select at least one additional SRS team member.")
    for user in additional:
        if not assert_user_can_login(user) or not (_roles(user) & SRS_ROLES):
            raise ValueError("Additional team members must be active SRS users.")

    case_classification = str(payload.get("case_classification") or "").strip()
    raw_deadline = payload.get("deadline_proposal_days")
    if isinstance(raw_deadline, float) and not raw_deadline.is_integer():
        raise ValueError("Deadline proposal must be a whole number.")
    deadline_days = int(raw_deadline or 0)
    if case_classification not in CASE_CLASSIFICATIONS:
        raise ValueError("A valid case classification is required.")
    if deadline_days < 1:
        raise ValueError("Deadline proposal must be at least 1 working day.")

    _ensure_item_team_member(workflow, workflow.project_owner, actor, is_project_owner=True)
    for user in additional:
        _ensure_item_team_member(workflow, user, actor)

    doc = frappe.get_doc(
        {
            "doctype": "SRS Deliverables Matrix",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": trainer_item,
            "submitted_by": actor,
            "submitted_at": datetime.utcnow(),
            "case_classification": case_classification,
            "deadline_proposal_days": deadline_days,
            "status": "SUBMITTED",
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)

    complete_deadlines(trainer_item, SRS_NODE_COORDINATION)
    workflow.case_classification = case_classification
    workflow.deadline_proposal_days = deadline_days
    workflow.status = STATE_WAITING_GM if case_classification in GM_APPROVAL_CASES else STATE_WAITING_MANAGER
    workflow.current_node = SRS_NODE_GM_APPROVAL if case_classification in GM_APPROVAL_CASES else SRS_NODE_MANAGER_APPROVAL
    workflow.updated_at = datetime.utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)

    _set_node_state(workflow, SRS_NODE_COORDINATION, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_node_state(workflow, SRS_NODE_DELIVERABLES, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_case_path_states(workflow, case_classification, actor, NODE_STATUS_IN_PROGRESS)
    next_node = SRS_NODE_GM_APPROVAL if case_classification in GM_APPROVAL_CASES else SRS_NODE_MANAGER_APPROVAL
    _set_node_state(workflow, next_node, NODE_STATUS_WAITING_APPROVAL, actor=actor)
    _create_approval(workflow, "GM_CASE_APPROVAL" if case_classification in GM_APPROVAL_CASES else "SRS_MANAGER_DEADLINE_APPROVAL", actor)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, "current_node", next_node)
    recipients = _active_users_with_role("General Manager" if case_classification in GM_APPROVAL_CASES else "SRS Manager")
    notify_many(
        recipients,
        title="SRS approval required",
        message=f"{case_classification} requires approval.",
        notification_type="APPROVAL_REQUIRED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=next_node,
        action_url="/approvals",
        priority="High",
    )
    _log("srs_coordination_submitted", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_COORDINATION)
    return {"success": True, "trainer_item": trainer_item}


def submit_srs_deliverables_matrix(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _assert_item_access(actor, trainer_item)
    workflow = _workflow_for_item(trainer_item)
    _assert_workflow_action(actor, workflow, SRS_NODE_DELIVERABLES, allow_gm=False, allow_manager=False, allow_owner=True)
    _assert_transition_prerequisites("submit_deliverables", workflow, actor)
    if frappe.db.exists("SRS Deliverables Matrix", {"workflow_instance": workflow.name}):
        frappe.throw("Deliverables Matrix has already been submitted.", frappe.PermissionError)
    case_classification = str(payload.get("case_classification") or "").strip()
    deadline_days = int(payload.get("deadline_proposal_days") or 0)
    if case_classification not in CASE_CLASSIFICATIONS:
        raise ValueError("A valid case classification is required.")
    if deadline_days < 1:
        raise ValueError("Deadline proposal must be at least 1 working day.")
    doc = frappe.get_doc(
        {
            "doctype": "SRS Deliverables Matrix",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": trainer_item,
            "submitted_by": actor,
            "submitted_at": datetime.utcnow(),
            "case_classification": case_classification,
            "deadline_proposal_days": deadline_days,
            "status": "SUBMITTED",
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    workflow.case_classification = case_classification
    workflow.deadline_proposal_days = deadline_days
    workflow.status = STATE_WAITING_GM if case_classification in GM_APPROVAL_CASES else STATE_WAITING_MANAGER
    workflow.current_node = SRS_NODE_GM_APPROVAL if case_classification in GM_APPROVAL_CASES else SRS_NODE_MANAGER_APPROVAL
    workflow.updated_at = datetime.utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_DELIVERABLES, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_case_path_states(workflow, case_classification, actor)
    next_node = SRS_NODE_GM_APPROVAL if case_classification in GM_APPROVAL_CASES else SRS_NODE_MANAGER_APPROVAL
    _set_node_state(workflow, next_node, NODE_STATUS_WAITING_APPROVAL, actor=actor)
    _create_approval(workflow, "GM_CASE_APPROVAL" if case_classification in GM_APPROVAL_CASES else "SRS_MANAGER_DEADLINE_APPROVAL", actor)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, "current_node", next_node)
    recipients = _active_users_with_role("General Manager" if case_classification in GM_APPROVAL_CASES else "SRS Manager")
    notify_many(
        recipients,
        title="SRS approval required",
        message=f"{case_classification} requires approval.",
        notification_type="GM_APPROVAL_REQUIRED" if case_classification in GM_APPROVAL_CASES else "SRS_MANAGER_APPROVAL_REQUIRED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=next_node,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    _log("srs_deliverables_submitted", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_DELIVERABLES)
    return {"success": True, "trainer_item": trainer_item}


def _create_approval(workflow, approval_type: str, actor: str) -> None:
    import frappe

    if frappe.db.exists("SRS Approval", {"workflow_instance": workflow.name, "approval_type": approval_type}):
        return
    required_role = "General Manager" if approval_type == "GM_CASE_APPROVAL" else "SRS Manager"
    doc = frappe.get_doc(
        {
            "doctype": "SRS Approval",
            "workflow_instance": workflow.name,
            "project": workflow.project,
            "trainer_item": workflow.trainer_item,
            "approval_type": approval_type,
            "status": "WAITING",
            "required_role": required_role,
            "original_case_classification": workflow.case_classification,
            "original_deadline_proposal_days": workflow.deadline_proposal_days,
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
    previous_case_classification = workflow.case_classification
    case_classification, deadline_days = _edited_case_and_deadline(workflow, payload)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    approval.status = "APPROVED_WITH_EDITS" if payload.get("case_classification") or payload.get("deadline_proposal_days") else "APPROVED"
    approval.edited_case_classification = case_classification
    approval.edited_deadline_proposal_days = deadline_days
    approval.comments = str(payload.get("comments") or "")[:500]
    approval.approved_by = actor
    approval.approved_at = datetime.utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    workflow.case_classification = case_classification
    workflow.deadline_proposal_days = deadline_days
    workflow.gm_approved_by = actor
    workflow.gm_approved_at = approval.approved_at
    workflow.status = STATE_WAITING_MANAGER
    workflow.current_node = SRS_NODE_MANAGER_APPROVAL
    workflow.updated_at = datetime.utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_case_path_states(workflow, case_classification, actor, path_group_case_classification=previous_case_classification)
    _set_node_state(workflow, SRS_NODE_GM_APPROVAL, NODE_STATUS_COMPLETED, actor=actor)
    _set_node_state(workflow, SRS_NODE_MANAGER_APPROVAL, NODE_STATUS_WAITING_APPROVAL, actor=actor)
    _create_approval(workflow, "SRS_MANAGER_DEADLINE_APPROVAL", actor)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, "current_node", SRS_NODE_MANAGER_APPROVAL)
    notify_many(
        _active_users_with_role("SRS Manager"),
        title="SRS Manager approval required",
        message="GM approval is complete. Final SRS deadline approval is required.",
        notification_type="GM_APPROVAL_COMPLETED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_MANAGER_APPROVAL,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    _log("srs_gm_approved", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_GM_APPROVAL)
    return {"success": True, "trainer_item": trainer_item}


def _edited_case_and_deadline(workflow, payload: dict[str, Any]) -> tuple[str, int]:
    case_classification = str(payload.get("case_classification") or workflow.case_classification or "").strip()
    deadline_days = int(payload.get("deadline_proposal_days") or workflow.deadline_proposal_days or 0)
    if case_classification not in CASE_CLASSIFICATIONS:
        raise ValueError("A valid case classification is required.")
    if deadline_days < 1:
        raise ValueError("Deadline proposal must be at least 1 working day.")
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
    previous_case_classification = workflow.case_classification
    case_classification, deadline_days = _edited_case_and_deadline(workflow, payload)
    approval = frappe.get_doc("SRS Approval", approval_name)
    if approval.status != "WAITING":
        frappe.throw("Approval has already been completed.", frappe.PermissionError)
    approval.status = "APPROVED_WITH_EDITS" if payload.get("case_classification") or payload.get("deadline_proposal_days") else "APPROVED"
    approval.edited_case_classification = case_classification
    approval.edited_deadline_proposal_days = deadline_days
    approval.comments = str(payload.get("comments") or "")[:500]
    approval.approved_by = actor
    approval.approved_at = datetime.utcnow()
    approval.flags.ignore_permissions = True
    approval.save(ignore_permissions=True)
    workflow.case_classification = case_classification
    workflow.approved_deadline_days = deadline_days
    workflow.srs_manager_approved_by = actor
    workflow.srs_manager_approved_at = approval.approved_at
    workflow.deadline_locked_at = approval.approved_at
    workflow.status = STATE_ACTION_PATHS
    workflow.current_node = SRS_NODE_ACTION_PATHS
    workflow.updated_at = datetime.utcnow()
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _set_node_state(workflow, SRS_NODE_MANAGER_APPROVAL, NODE_STATUS_COMPLETED, actor=actor)
    _set_node_state(workflow, SRS_NODE_DEADLINE_LOCKED, NODE_STATUS_COMPLETED, actor=actor)
    _set_case_path_states(
        workflow,
        case_classification,
        actor,
        path_group_case_classification=previous_case_classification,
        include_gm_not_applicable=False,
    )
    deadline = create_deadline(
        project=workflow.project,
        trainer_item=trainer_item,
        workflow_type=SRS_WORKFLOW_TYPE,
        node_id=SRS_NODE_ACTION_PATHS,
        triggered_by=actor,
        deadline_days=deadline_days,
    )
    _set_node_state(workflow, SRS_NODE_ACTION_PATHS, NODE_STATUS_IN_PROGRESS, actor=actor, responsible_user=workflow.project_owner, deadline=deadline)
    _set_node_state(workflow, SRS_NODE_BMDP, NODE_STATUS_READY, actor=actor, responsible_user=workflow.project_owner)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"current_node": SRS_NODE_ACTION_PATHS, "current_responsible_user": workflow.project_owner})
    notify_many(
        [workflow.project_owner],
        title="SRS deadline locked",
        message="The approved SRS deadline is locked. Action Paths are active.",
        notification_type="DEADLINE_LOCKED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_ACTION_PATHS,
        action_url=project_action_url("srs", workflow.project, trainer_item),
        priority="High",
    )
    _log("srs_manager_approved", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_MANAGER_APPROVAL)
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
            "submitted_at": datetime.utcnow(),
            "status": "SUBMITTED",
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    complete_deadlines(trainer_item, SRS_NODE_ACTION_PATHS)
    _set_node_state(workflow, SRS_NODE_ACTION_PATHS, NODE_STATUS_COMPLETED, actor=actor, responsible_user=workflow.project_owner)
    _set_case_path_states(
        workflow,
        workflow.case_classification,
        actor,
        NODE_STATUS_COMPLETED,
        path_group_case_classification=_existing_case_path_group_case(workflow, workflow.case_classification),
        include_gm_not_applicable=False,
    )
    _set_node_state(workflow, SRS_NODE_BMDP, NODE_STATUS_COMPLETED, actor=actor, responsible_user=actor)
    workflow.bmdp_path = path
    workflow.status = STATE_COMPLETE
    workflow.current_node = SRS_NODE_BMDP
    workflow.completed_at = datetime.utcnow()
    workflow.updated_at = workflow.completed_at
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value("BEDO Trainer Item", trainer_item, {"status": ITEM_STATUS_SRS_COMPLETE, "current_node": SRS_NODE_BMDP})
    report_to = frappe.get_all("BEDO Trainer Item Report To", filters={"trainer_item": trainer_item}, pluck="user")
    notify_many(
        report_to,
        title="BMDP submitted",
        message="BMDP path has been submitted. SRS Complete.",
        notification_type="BMDP_SUBMITTED",
        project=workflow.project,
        trainer_item=trainer_item,
        node_id=SRS_NODE_BMDP,
        action_url=project_action_url("gm", workflow.project, trainer_item),
        priority="Normal",
    )
    _log("srs_bmdp_path_submitted", actor, project=workflow.project, trainer_item=trainer_item, node_id=SRS_NODE_BMDP)
    return {"success": True, "trainer_item": trainer_item}


def _approval_roles_for_actor(actor: str) -> set[str]:
    roles = set()
    if _is_gm(actor):
        roles.add("General Manager")
    if _is_srs_manager(actor):
        roles.add("SRS Manager")
    return roles


def _approval_node_for_type(approval_type: str) -> str:
    if approval_type == "GM_CASE_APPROVAL":
        return SRS_NODE_GM_APPROVAL
    if approval_type == "SRS_MANAGER_DEADLINE_APPROVAL":
        return SRS_NODE_MANAGER_APPROVAL
    return ""


def _approval_is_actionable(row) -> bool:
    import frappe

    if row.status != "WAITING":
        return False
    target_node = _approval_node_for_type(row.approval_type)
    if not target_node:
        return False
    workflow = frappe.db.get_value(
        "SRS Workflow Instance",
        row.workflow_instance,
        ["current_node", "case_classification"],
        as_dict=True,
    )
    if not workflow or workflow.current_node != target_node:
        return False
    node_status = frappe.db.get_value(
        "SRS Workflow Node State",
        {"workflow_instance": row.workflow_instance, "node_id": target_node},
        "status",
    )
    if node_status != NODE_STATUS_WAITING_APPROVAL:
        return False
    if row.approval_type == "SRS_MANAGER_DEADLINE_APPROVAL" and workflow.case_classification in GM_APPROVAL_CASES:
        gm_status = frappe.db.get_value(
            "SRS Workflow Node State",
            {"workflow_instance": row.workflow_instance, "node_id": SRS_NODE_GM_APPROVAL},
            "status",
        )
        if gm_status != NODE_STATUS_COMPLETED:
            return False
    return True


def _approval_display_row(row) -> dict[str, Any]:
    import frappe

    project = frappe.db.get_value("BEDO Project", row.project, ["project_code", "project_name", "end_user", "po_deadline_date"], as_dict=True) or {}
    item = frappe.db.get_value("BEDO Trainer Item", row.trainer_item, ["trainer_item_name"], as_dict=True) or {}
    workflow = frappe.db.get_value(
        "SRS Workflow Instance",
        row.workflow_instance,
        ["current_node", "project_owner", "case_classification", "deadline_proposal_days", "approved_deadline_days"],
        as_dict=True,
    ) or {}
    submitted = frappe.db.get_value("SRS Deliverables Matrix", {"workflow_instance": row.workflow_instance}, ["submitted_by", "submitted_at"], as_dict=True) or {}
    return {
        "name": row.name,
        "approval_type": row.approval_type,
        "approval_label": "GM Case Approval" if row.approval_type == "GM_CASE_APPROVAL" else "SRS Manager Deadline Approval",
        "status": row.status,
        "required_role": row.required_role,
        "project": row.project,
        "project_code": project.get("project_code") or "",
        "project_name": project.get("project_name") or "",
        "end_user": project.get("end_user") or "",
        "po_deadline_date": str(project.get("po_deadline_date") or ""),
        "trainer_item": row.trainer_item,
        "trainer_item_name": item.get("trainer_item_name") or "",
        "submitted_by": submitted.get("submitted_by") or "",
        "submitted_by_name": _user_full_name(submitted.get("submitted_by")),
        "submitted_at": to_cairo_iso(submitted.get("submitted_at")),
        "project_owner": workflow.get("project_owner") or "",
        "project_owner_name": _user_full_name(workflow.get("project_owner")),
        "current_node": workflow.get("current_node") or "",
        "case_classification": row.edited_case_classification or workflow.get("case_classification") or row.original_case_classification or "",
        "deadline_proposal_days": row.edited_deadline_proposal_days or workflow.get("approved_deadline_days") or workflow.get("deadline_proposal_days") or row.original_deadline_proposal_days or 0,
        "priority": "High" if row.approval_type == "GM_CASE_APPROVAL" else "Normal",
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
        fields=["name", "workflow_instance", "project", "trainer_item", "approval_type", "status", "required_role", "original_case_classification", "edited_case_classification", "original_deadline_proposal_days", "edited_deadline_proposal_days", "creation"],
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
    return approve_srs_deadline_as_srs_manager(detail["trainer_item"], payload, actor, approval_name=approval)


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
