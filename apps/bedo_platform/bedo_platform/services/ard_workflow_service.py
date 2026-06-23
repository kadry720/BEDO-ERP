from __future__ import annotations

from datetime import datetime
from typing import Any

from bedo_platform.constants import ARD_ROLES
from bedo_platform.services.deadline_service import CAIRO_TZ, to_cairo_iso, to_storage_datetime
from bedo_platform.services.meeting_service import (
    MEETING_STATUS_COMPLETED,
    MEETING_STATUS_PENDING_CONFIRMATION,
    MEETING_TYPE_INTERNAL_ARD_SYNC,
    MEETING_TYPE_PROGRESS_REVIEW,
    STANDARD_MEETING_DURATION,
    calculate_progress_review_meeting_at,
)
from bedo_platform.services.notification_service import notify_many, project_action_url
from bedo_platform.services.security_audit_service import log_security_event
from bedo_platform.services.user_profile_service import assert_user_can_login

ARD_WORKFLOW_TYPE = "ARD"
ARD_STATUS_IN_PROGRESS = "ARD_IN_PROGRESS"
ARD_STATUS_COMPLETE = "ARD_COMPLETE"
ARD_STATUS_WAITING_INTERNAL_SYNC = "WAITING_INTERNAL_SYNC"
ARD_STATUS_WAITING_OWNER_ASSIGNMENT = "WAITING_OWNER_ASSIGNMENT"
ARD_STATUS_WAITING_TEAM_SELECTION = "WAITING_TEAM_SELECTION"
ARD_STATUS_WAITING_PROGRESS_REVIEW = "WAITING_PROGRESS_REVIEW"
ARD_STATUS_WAITING_SCMDP = "WAITING_SCMDP"

ARD_NODE_HANDOVER_COMPLETE = "HANDOVER_COMPLETE"
ARD_NODE_INTERNAL_SYNC = "INTERNAL_ARD_SYNC_MEETING"
ARD_NODE_OWNER_ASSIGNMENT = "ARD_PROJECT_OWNER_ASSIGNMENT"
ARD_NODE_TEAM_SELECTION = "ARD_TEAM_SELECTION"
ARD_NODE_PROGRESS_REVIEW = "PROGRESS_REVIEW_MEETING"
ARD_NODE_GM_APPROVAL = "GM_APPROVAL"
ARD_NODE_COMMAND_CENTER_PROCUREMENT = "COMMAND_CENTER_PROCUREMENT_CONFIRMATION"
ARD_NODE_ELECTRONICS_SYSTEM_DESIGN = "ELECTRONICS_SYSTEM_DESIGN"
ARD_NODE_CONCEPT_PROOF = "CONCEPT_PROOF_PROTOTYPING"
ARD_NODE_SCMDP_SUBMISSION = "SCMDP_SUBMISSION"

ARD_NODE_STATUS_LOCKED = "LOCKED"
ARD_NODE_STATUS_READY = "READY"
ARD_NODE_STATUS_IN_PROGRESS = "IN_PROGRESS"
ARD_NODE_STATUS_COMPLETED = "COMPLETED"
ARD_NODE_STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
ARD_NODE_STATUS_WAITING_APPROVAL = "WAITING_APPROVAL"

ARD_PROGRESS_OUTCOME_ON_PLAN = "ON_PLAN"

ARD_FLOWCHART_NODES: list[dict[str, Any]] = [
    {"id": ARD_NODE_HANDOVER_COMPLETE, "label": "Handover Complete", "lane": "handover", "column": "milestone_1", "kind": "display", "clickable": False},
    {"id": ARD_NODE_INTERNAL_SYNC, "label": "Internal ARD Sync Meeting", "lane": "formation", "column": "milestone_1", "kind": "action", "clickable": True},
    {"id": ARD_NODE_OWNER_ASSIGNMENT, "label": "ARD Project Owner Assignment", "lane": "formation", "column": "milestone_1", "kind": "action", "clickable": True},
    {"id": ARD_NODE_TEAM_SELECTION, "label": "ARD Team Selection", "lane": "formation", "column": "milestone_1", "kind": "action", "clickable": True},
    {"id": ARD_NODE_PROGRESS_REVIEW, "label": "Progress Review Meeting", "lane": "review", "column": "milestone_2", "kind": "action", "clickable": True},
    {"id": ARD_NODE_GM_APPROVAL, "label": "GM Approval", "lane": "interruptions", "column": "milestone_2", "kind": "approval", "clickable": False},
    {"id": ARD_NODE_COMMAND_CENTER_PROCUREMENT, "label": "Command Center Procurement Confirmation", "lane": "interruptions", "column": "final", "kind": "action", "clickable": True},
    {"id": ARD_NODE_ELECTRONICS_SYSTEM_DESIGN, "label": "Electronics System Design", "lane": "interruptions", "column": "final", "kind": "action", "clickable": True},
    {"id": ARD_NODE_CONCEPT_PROOF, "label": "Concept-Proof Prototyping", "lane": "interruptions", "column": "final", "kind": "action", "clickable": True},
    {"id": ARD_NODE_SCMDP_SUBMISSION, "label": "SCMDP Submission", "lane": "final", "column": "final", "kind": "action", "clickable": True},
]

ARD_FLOWCHART_EDGES = [
    (ARD_NODE_HANDOVER_COMPLETE, ARD_NODE_INTERNAL_SYNC),
    (ARD_NODE_INTERNAL_SYNC, ARD_NODE_OWNER_ASSIGNMENT),
    (ARD_NODE_OWNER_ASSIGNMENT, ARD_NODE_TEAM_SELECTION),
    (ARD_NODE_TEAM_SELECTION, ARD_NODE_PROGRESS_REVIEW),
    (ARD_NODE_PROGRESS_REVIEW, ARD_NODE_SCMDP_SUBMISSION),
    (ARD_NODE_PROGRESS_REVIEW, ARD_NODE_GM_APPROVAL),
    (ARD_NODE_GM_APPROVAL, ARD_NODE_COMMAND_CENTER_PROCUREMENT),
    (ARD_NODE_GM_APPROVAL, ARD_NODE_ELECTRONICS_SYSTEM_DESIGN),
    (ARD_NODE_GM_APPROVAL, ARD_NODE_CONCEPT_PROOF),
    (ARD_NODE_COMMAND_CENTER_PROCUREMENT, ARD_NODE_SCMDP_SUBMISSION),
    (ARD_NODE_ELECTRONICS_SYSTEM_DESIGN, ARD_NODE_SCMDP_SUBMISSION),
    (ARD_NODE_CONCEPT_PROOF, ARD_NODE_SCMDP_SUBMISSION),
]


def _utcnow() -> datetime:
    return datetime.utcnow()


def get_ard_flowchart_definition() -> dict[str, Any]:
    return {
        "lanes": [
            {"id": "handover", "label": "Handover"},
            {"id": "formation", "label": "ARD Formation"},
            {"id": "review", "label": "Review"},
            {"id": "interruptions", "label": "Interruption Paths"},
            {"id": "final", "label": "Final Submission"},
        ],
        "deadline_columns": [
            {"id": "milestone_1", "label": "Milestone 1", "detail": "Team selection due by working day 3"},
            {"id": "milestone_2", "label": "Milestone 2", "detail": "Progress review due by working day 4"},
            {"id": "final", "label": "Final", "detail": "SCMDP within seven working days"},
        ],
        "nodes": ARD_FLOWCHART_NODES,
        "edges": [{"from": left, "to": right} for left, right in ARD_FLOWCHART_EDGES],
    }


def _active_users_with_role(role: str) -> list[str]:
    import frappe

    users = []
    for row in frappe.get_all("Has Role", filters={"role": role}, fields=["parent"]):
        if row.parent not in {"Administrator", "Guest"} and assert_user_can_login(row.parent):
            users.append(row.parent)
    return sorted(set(users))


def _roles(user: str) -> set[str]:
    import frappe

    return set(frappe.get_roles(user))


def _require_role(actor: str, role: str) -> None:
    import frappe

    if role not in _roles(actor):
        frappe.throw(f"{role} access is required.", frappe.PermissionError)


def _user_full_name(user: str) -> str:
    if not user:
        return ""
    import frappe

    row = frappe.db.get_value("User", user, ["first_name", "last_name", "username"], as_dict=True) or {}
    full_name = " ".join(part for part in [row.get("first_name"), row.get("last_name")] if part)
    return full_name or row.get("username") or user


def _primary_assignment(user: str) -> dict[str, str]:
    import frappe

    row = frappe.db.get_value(
        "BEDO User Role Assignment",
        {"user": user, "is_active": 1, "is_primary_department": 1},
        ["business_role", "department"],
        as_dict=True,
    ) or {}
    department = ""
    if row.get("department"):
        department = frappe.db.get_value("BEDO Department", row.get("department"), "department_key") or row.get("department") or ""
    return {"business_role": row.get("business_role") or "", "department": department or ""}


def _active_ard_users() -> list[str]:
    users: set[str] = set()
    for role in sorted(ARD_ROLES):
        users.update(_active_users_with_role(role))
    return sorted(users)


def _workflow_for_item(trainer_item: str):
    import frappe

    name = frappe.db.get_value("ARD Workflow Instance", {"trainer_item": trainer_item, "is_superseded": 0}, "name")
    if not name:
        frappe.throw("ARD workflow has not started for this trainer item.", frappe.DoesNotExistError)
    return frappe.get_doc("ARD Workflow Instance", name)


def _node_state_name(workflow, node_id: str) -> str:
    import frappe

    return frappe.db.get_value(
        "ARD Workflow Node State",
        {"workflow_instance": workflow.name, "node_id": node_id, "is_superseded": 0},
        "name",
    ) or ""


def _update_node_state(workflow, node_id: str, status: str, actor: str, *, responsible_user: str = "", started: bool = False, completed: bool = False, display_data: dict[str, Any] | None = None) -> None:
    import frappe

    state_name = _node_state_name(workflow, node_id)
    if not state_name:
        _set_ard_node_state(workflow, node_id, status, actor, responsible_user=responsible_user)
        return
    values: dict[str, Any] = {"status": status, "last_action_by": actor}
    if responsible_user != "":
        values["responsible_user"] = responsible_user
    now = _utcnow()
    if started:
        values["started_at"] = now
    if completed:
        values["completed_at"] = now
        values.setdefault("started_at", now)
    if display_data is not None:
        values["display_data"] = frappe.as_json(display_data)
    frappe.db.set_value("ARD Workflow Node State", state_name, values, update_modified=False)


def _set_current_node(workflow, node_id: str, actor: str, *, status: str = ARD_STATUS_IN_PROGRESS, responsible_user: str = "") -> None:
    import frappe

    workflow.current_node = node_id
    workflow.status = status
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    frappe.db.set_value(
        "BEDO Trainer Item",
        workflow.trainer_item,
        {
            "status": ARD_STATUS_IN_PROGRESS if status != ARD_STATUS_COMPLETE else ARD_STATUS_COMPLETE,
            "current_workflow": ARD_WORKFLOW_TYPE,
            "current_pillar": "ARD",
            "current_node": node_id,
            "current_responsible_user": responsible_user,
        },
        update_modified=False,
    )


def _set_ard_node_state(workflow, node_id: str, status: str, actor: str, *, responsible_user: str = "") -> None:
    import frappe

    doc = frappe.new_doc("ARD Workflow Node State")
    doc.workflow_instance = workflow.name
    doc.project = workflow.project
    doc.trainer_item = workflow.trainer_item
    doc.generation = workflow.generation
    doc.node_id = node_id
    doc.status = status
    doc.last_action_by = actor
    doc.responsible_user = responsible_user
    doc.display_data = "{}"
    if status == ARD_NODE_STATUS_IN_PROGRESS:
        doc.started_at = _utcnow()
    if status == ARD_NODE_STATUS_COMPLETED:
        doc.started_at = _utcnow()
        doc.completed_at = _utcnow()
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)


def _safe_node_state(row) -> dict[str, Any]:
    import frappe

    display_data = {}
    if getattr(row, "display_data", ""):
        try:
            display_data = frappe.parse_json(row.display_data) or {}
        except Exception:
            display_data = {}
    return {
        "node_id": row.node_id,
        "status": row.status,
        "started_at": to_cairo_iso(row.started_at),
        "completed_at": to_cairo_iso(row.completed_at),
        "responsible_user": row.responsible_user or "",
        "responsible_name": _user_full_name(row.responsible_user),
        "last_action_by": row.last_action_by or "",
        "last_action_by_name": _user_full_name(row.last_action_by),
        "display_data": display_data,
    }


def _safe_team_member(row) -> dict[str, Any]:
    return {
        "user": row.user,
        "full_name": row.full_name or _user_full_name(row.user),
        "department": row.department or "ARD",
        "business_role": row.business_role or "",
        "is_project_owner": int(row.is_project_owner or 0),
        "selected_by": row.selected_by or "",
        "selected_at": to_cairo_iso(row.selected_at),
    }


def _safe_meeting(meeting: str) -> dict[str, Any] | None:
    if not meeting:
        return None
    import frappe
    from bedo_platform.services.meeting_service import _meeting_row

    if not frappe.db.exists("BEDO Meeting", meeting):
        return None
    row = frappe.db.get_value(
        "BEDO Meeting",
        meeting,
        [
            "name",
            "meeting_id",
            "meeting_type",
            "project",
            "trainer_item",
            "source_workflow",
            "source_workflow_generation",
            "source_node",
            "organizer",
            "organizer_department",
            "scheduled_at",
            "time_zone",
            "expected_end_at",
            "status",
            "title",
            "description",
            "created_at",
            "confirmed_at",
            "completed_at",
            "overdue_at",
        ],
        as_dict=True,
    )
    return _meeting_row(row) if row else None


def _project_row(project: str) -> dict[str, Any]:
    import frappe

    row = frappe.db.get_value(
        "BEDO Project",
        project,
        ["name", "project_code", "project_name", "end_user", "po_deadline_date", "status"],
        as_dict=True,
    ) or {}
    return dict(row)


def _trainer_item_row(trainer_item: str) -> dict[str, Any]:
    import frappe

    row = frappe.db.get_value(
        "BEDO Trainer Item",
        trainer_item,
        ["name", "project", "trainer_name", "trainer_item_name", "quantity", "original_quantity", "separation_mode", "sequence_no", "status", "current_node", "current_responsible_user"],
        as_dict=True,
    ) or {}
    return dict(row)


def _workflow_row(workflow) -> dict[str, Any]:
    return {
        "name": workflow.name,
        "project": workflow.project,
        "trainer_item": workflow.trainer_item,
        "source_handoff": workflow.source_handoff,
        "source_workflow": workflow.source_workflow,
        "generation": int(workflow.generation or 1),
        "status": workflow.status,
        "current_node": workflow.current_node,
        "project_owner": workflow.project_owner or "",
        "started_by": workflow.started_by,
        "started_at": to_cairo_iso(workflow.started_at),
        "internal_sync_meeting": workflow.internal_sync_meeting or "",
        "progress_review_meeting": workflow.progress_review_meeting or "",
        "scmdp_path": getattr(workflow, "scmdp_path", "") or "",
        "scmdp_submitted_by": getattr(workflow, "scmdp_submitted_by", "") or "",
        "scmdp_submitted_at": to_cairo_iso(getattr(workflow, "scmdp_submitted_at", None)),
        "completed_by": workflow.completed_by or "",
        "completed_at": to_cairo_iso(workflow.completed_at),
    }


def start_ard_workflow_from_handoff(handoff, actor: str) -> dict[str, Any]:
    import frappe

    existing = frappe.db.get_value("ARD Workflow Instance", {"source_handoff": handoff.name, "is_superseded": 0}, "name")
    if existing:
        return {"success": True, "workflow": existing, "created": False}

    now = _utcnow()
    workflow = frappe.get_doc(
        {
            "doctype": "ARD Workflow Instance",
            "project": handoff.project,
            "trainer_item": handoff.trainer_item,
            "source_handoff": handoff.name,
            "source_workflow": handoff.srs_workflow_instance,
            "generation": int(getattr(handoff, "generation", 1) or 1),
            "status": ARD_STATUS_IN_PROGRESS,
            "current_node": ARD_NODE_INTERNAL_SYNC,
            "started_by": actor,
            "started_at": now,
            "is_superseded": 0,
        }
    )
    workflow.flags.ignore_permissions = True
    workflow.insert(ignore_permissions=True)
    for node in ARD_FLOWCHART_NODES:
        status = ARD_NODE_STATUS_LOCKED
        if node["id"] == ARD_NODE_HANDOVER_COMPLETE:
            status = ARD_NODE_STATUS_COMPLETED
        elif node["id"] == ARD_NODE_INTERNAL_SYNC:
            status = ARD_NODE_STATUS_IN_PROGRESS
        elif node["id"] in {
            ARD_NODE_COMMAND_CENTER_PROCUREMENT,
            ARD_NODE_ELECTRONICS_SYSTEM_DESIGN,
            ARD_NODE_CONCEPT_PROOF,
        }:
            status = ARD_NODE_STATUS_NOT_APPLICABLE
        _set_ard_node_state(workflow, node["id"], status, actor)

    frappe.db.set_value(
        "BEDO Trainer Item",
        handoff.trainer_item,
        {"status": ARD_STATUS_IN_PROGRESS, "current_workflow": ARD_WORKFLOW_TYPE, "current_pillar": "ARD", "current_node": ARD_NODE_INTERNAL_SYNC, "current_responsible_user": ""},
    )
    recipients = _active_users_with_role("ARD Manager")
    notify_many(
        recipients,
        title="ARD workflow started",
        message="A trainer item has entered the ARD workflow after handover completion.",
        notification_type="ARD_WORKFLOW_STARTED",
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        workflow_type=ARD_WORKFLOW_TYPE,
        node_id=ARD_NODE_INTERNAL_SYNC,
        action_url=project_action_url("ard", handoff.project, handoff.trainer_item),
        priority="High",
    )
    log_security_event(
        "ard_workflow_started",
        user=actor,
        project=handoff.project,
        trainer_item=handoff.trainer_item,
        workflow_type=ARD_WORKFLOW_TYPE,
        node_id=ARD_NODE_HANDOVER_COMPLETE,
        status="Success",
        message=workflow.name,
    )
    return {"success": True, "workflow": workflow.name, "created": True}


def ard_visible_project_names(actor: str) -> list[str]:
    import frappe

    roles = set(frappe.get_roles(actor))
    if not (roles & ARD_ROLES):
        return []
    rows = frappe.get_all(
        "ARD Workflow Instance",
        filters={"is_superseded": 0},
        fields=["project"],
    )
    return sorted({row.project for row in rows})


def _assert_can_view_workflow(workflow, actor: str) -> None:
    import frappe

    roles = _roles(actor)
    if "General Manager" in roles or roles & ARD_ROLES:
        return
    assigned = frappe.db.exists(
        "ARD Workflow Team Member",
        {"workflow_instance": workflow.name, "user": actor, "is_active": 1},
    )
    if assigned:
        return
    frappe.throw("You do not have access to this ARD workflow.", frappe.PermissionError)


def _node_availability(workflow, actor: str, state_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roles = _roles(actor)
    is_manager = "ARD Manager" in roles
    is_owner = bool(workflow.project_owner and workflow.project_owner == actor)
    states = {row["node_id"]: row["status"] for row in state_rows}

    def row(node_id: str, can_act: bool, disabled_reason: str = "") -> dict[str, Any]:
        status = states.get(node_id, ARD_NODE_STATUS_LOCKED)
        can_open = status not in {ARD_NODE_STATUS_LOCKED, ARD_NODE_STATUS_NOT_APPLICABLE}
        return {
            "nodeId": node_id,
            "canView": True,
            "canOpen": can_open,
            "canAct": can_open and can_act,
            "disabledReason": "" if can_open and can_act else disabled_reason,
        }

    return [
        row(ARD_NODE_HANDOVER_COMPLETE, False, "Handover completion is automatic."),
        row(ARD_NODE_INTERNAL_SYNC, is_manager, "ARD Manager access is required."),
        row(ARD_NODE_OWNER_ASSIGNMENT, is_manager, "ARD Manager access is required."),
        row(ARD_NODE_TEAM_SELECTION, is_owner, "Only the ARD project owner can select the team."),
        row(ARD_NODE_PROGRESS_REVIEW, is_owner, "Only the ARD project owner can submit the progress review outcome."),
        row(ARD_NODE_GM_APPROVAL, False, "GM approval is only opened by interruption requests."),
        row(ARD_NODE_COMMAND_CENTER_PROCUREMENT, False, "Procurement interruption is inactive unless requested."),
        row(ARD_NODE_ELECTRONICS_SYSTEM_DESIGN, False, "Electronics interruption is inactive unless requested."),
        row(ARD_NODE_CONCEPT_PROOF, False, "Concept-Proof interruption is inactive unless requested."),
        row(ARD_NODE_SCMDP_SUBMISSION, is_owner, "Only the ARD project owner can submit SCMDP."),
    ]


def get_ard_workspace(trainer_item: str, actor: str) -> dict[str, Any]:
    import frappe
    from bedo_platform.services.deadline_service import get_deadlines_for_trainer_item, server_now_iso

    workflow = _workflow_for_item(trainer_item)
    _assert_can_view_workflow(workflow, actor)
    node_states = [
        _safe_node_state(row)
        for row in frappe.get_all(
            "ARD Workflow Node State",
            filters={"workflow_instance": workflow.name, "is_superseded": 0},
            fields=[
                "node_id",
                "status",
                "started_at",
                "completed_at",
                "responsible_user",
                "last_action_by",
                "display_data",
            ],
            order_by="creation asc",
        )
    ]
    team_members = [
        _safe_team_member(row)
        for row in frappe.get_all(
            "ARD Workflow Team Member",
            filters={"workflow_instance": workflow.name, "is_active": 1},
            fields=["user", "full_name", "department", "business_role", "is_project_owner", "selected_by", "selected_at"],
            order_by="is_project_owner desc, creation asc",
        )
    ]
    return {
        "project": _project_row(workflow.project),
        "trainer_item": _trainer_item_row(workflow.trainer_item),
        "workflow": _workflow_row(workflow),
        "node_states": node_states,
        "team_members": team_members,
        "node_availability": _node_availability(workflow, actor, node_states),
        "meetings": {
            "internal_sync": _safe_meeting(workflow.internal_sync_meeting),
            "progress_review": _safe_meeting(workflow.progress_review_meeting),
        },
        "ard_users": list_eligible_ard_team_members(actor),
        "deadlines": [
            row
            for row in get_deadlines_for_trainer_item(workflow.trainer_item)
            if row.get("workflow_type") == ARD_WORKFLOW_TYPE
        ],
        "server_now": server_now_iso(),
        "tabs": ["ARD", "Meetings", "Audit Log"],
    }


def list_eligible_ard_team_members(actor: str) -> list[dict[str, str]]:
    roles = _roles(actor)
    if "General Manager" not in roles and not (roles & ARD_ROLES):
        import frappe

        frappe.throw("ARD access is required.", frappe.PermissionError)
    users = []
    for user in _active_ard_users():
        assignment = _primary_assignment(user)
        users.append(
            {
                "user": user,
                "username": user,
                "full_name": _user_full_name(user),
                "business_role": assignment["business_role"] or next((role for role in sorted(_roles(user)) if role.startswith("ARD ")), "ARD User"),
                "department": assignment["department"] or "ARD",
                "department_key": "ARD",
            }
        )
    return users


def _upsert_team_member(workflow, user: str, actor: str, *, is_project_owner: int = 0) -> str:
    import frappe

    assignment = _primary_assignment(user)
    existing = frappe.db.get_value("ARD Workflow Team Member", {"workflow_instance": workflow.name, "user": user}, "name")
    doc = frappe.get_doc("ARD Workflow Team Member", existing) if existing else frappe.new_doc("ARD Workflow Team Member")
    doc.workflow_instance = workflow.name
    doc.project = workflow.project
    doc.trainer_item = workflow.trainer_item
    doc.generation = int(workflow.generation or 1)
    doc.user = user
    doc.full_name = _user_full_name(user)
    doc.department = assignment["department"] or "ARD"
    doc.business_role = assignment["business_role"] or next((role for role in sorted(_roles(user)) if role.startswith("ARD ")), "ARD User")
    doc.is_project_owner = int(is_project_owner)
    doc.selected_by = actor
    doc.selected_at = _utcnow()
    doc.is_active = 1
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    return doc.name


def _validate_ard_users(users: list[str]) -> list[str]:
    selected = sorted({str(user or "").strip() for user in users if str(user or "").strip()})
    active = set(_active_ard_users())
    invalid = [user for user in selected if user not in active]
    if invalid:
        import frappe

        frappe.throw(f"Only active ARD users can be selected: {', '.join(invalid)}", frappe.PermissionError)
    return selected


def _upsert_ard_meeting(
    *,
    workflow,
    meeting_type: str,
    node_id: str,
    title: str,
    scheduled_at: datetime,
    actor: str,
    participant_users: list[str],
) -> str:
    import frappe

    scheduled = scheduled_at
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=CAIRO_TZ)
    else:
        scheduled = scheduled.astimezone(CAIRO_TZ)
    meeting_id = f"{meeting_type}-{workflow.name}-G{int(workflow.generation or 1)}"
    existing = frappe.db.get_value("BEDO Meeting", {"meeting_id": meeting_id, "is_superseded": 0}, "name")
    meeting = frappe.get_doc("BEDO Meeting", existing) if existing else frappe.new_doc("BEDO Meeting")
    meeting.meeting_id = meeting_id
    meeting.meeting_type = meeting_type
    meeting.project = workflow.project
    meeting.trainer_item = workflow.trainer_item
    meeting.source_workflow = workflow.name
    meeting.source_workflow_generation = int(workflow.generation or 1)
    meeting.source_node = node_id
    meeting.organizer = actor
    meeting.organizer_department = "ARD"
    meeting.scheduled_at = to_storage_datetime(scheduled)
    meeting.time_zone = "Africa/Cairo"
    meeting.expected_end_at = to_storage_datetime(scheduled + STANDARD_MEETING_DURATION)
    meeting.status = MEETING_STATUS_PENDING_CONFIRMATION
    meeting.title = title
    meeting.description = f"{title} for ARD workflow {workflow.name}."
    meeting.created_at = getattr(meeting, "created_at", None) or to_storage_datetime(datetime.now(CAIRO_TZ))
    meeting.related_reference_doctype = "ARD Workflow Instance"
    meeting.related_reference_name = workflow.name
    meeting.is_superseded = 0
    meeting.flags.ignore_permissions = True
    if existing:
        meeting.save(ignore_permissions=True)
    else:
        meeting.insert(ignore_permissions=True)

    from bedo_platform.services.meeting_service import _upsert_meeting_participant

    _upsert_meeting_participant(
        meeting=meeting.name,
        user=actor,
        department="ARD",
        participation_source="organizer",
        selected_by=actor,
        confirmation_status="CONFIRMED",
    )
    for user in _validate_ard_users(participant_users):
        _upsert_meeting_participant(
            meeting=meeting.name,
            user=user,
            department="ARD",
            participation_source="selected team member",
            selected_by=actor,
        )
    return meeting.name


def schedule_internal_sync_meeting(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    _require_role(actor, "ARD Manager")
    workflow = _workflow_for_item(trainer_item)
    if workflow.current_node != ARD_NODE_INTERNAL_SYNC:
        frappe.throw("Internal ARD Sync Meeting is not active for this workflow.", frappe.PermissionError)
    scheduled_at = payload.get("scheduled_at")
    if not scheduled_at:
        frappe.throw("Scheduled date and time are required.", frappe.ValidationError)
    scheduled = datetime.fromisoformat(str(scheduled_at))
    participants = payload.get("participants") or payload.get("users") or []
    meeting = _upsert_ard_meeting(
        workflow=workflow,
        meeting_type=MEETING_TYPE_INTERNAL_ARD_SYNC,
        node_id=ARD_NODE_INTERNAL_SYNC,
        title="Internal ARD Sync Meeting",
        scheduled_at=scheduled,
        actor=actor,
        participant_users=list(participants),
    )
    workflow.internal_sync_meeting = meeting
    workflow.status = ARD_STATUS_WAITING_INTERNAL_SYNC
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _update_node_state(workflow, ARD_NODE_INTERNAL_SYNC, ARD_NODE_STATUS_IN_PROGRESS, actor, started=True, display_data={"Meeting": meeting})
    notify_many(
        _active_users_with_role("ARD Manager"),
        title="Internal ARD Sync Meeting scheduled",
        message="The Internal ARD Sync Meeting has been scheduled.",
        notification_type="ARD_INTERNAL_SYNC_MEETING",
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        workflow_type=ARD_WORKFLOW_TYPE,
        node_id=ARD_NODE_INTERNAL_SYNC,
        action_url="/meetings",
        priority="High",
    )
    log_security_event("ard_internal_sync_scheduled", user=actor, project=workflow.project, trainer_item=workflow.trainer_item, workflow_type=ARD_WORKFLOW_TYPE, node_id=ARD_NODE_INTERNAL_SYNC, status="Success", message=meeting)
    return {"success": True, "meeting": meeting, "workspace": get_ard_workspace(trainer_item, actor)}


def complete_internal_sync_meeting(trainer_item: str, actor: str) -> dict[str, Any]:
    import frappe

    _require_role(actor, "ARD Manager")
    workflow = _workflow_for_item(trainer_item)
    if workflow.current_node != ARD_NODE_INTERNAL_SYNC:
        frappe.throw("Internal ARD Sync Meeting is not active for this workflow.", frappe.PermissionError)
    if workflow.internal_sync_meeting:
        frappe.db.set_value(
            "BEDO Meeting",
            workflow.internal_sync_meeting,
            {"status": MEETING_STATUS_COMPLETED, "completed_at": to_storage_datetime(datetime.now(CAIRO_TZ))},
            update_modified=False,
        )
    _update_node_state(workflow, ARD_NODE_INTERNAL_SYNC, ARD_NODE_STATUS_COMPLETED, actor, completed=True, display_data={"Meeting": workflow.internal_sync_meeting or ""})
    _update_node_state(workflow, ARD_NODE_OWNER_ASSIGNMENT, ARD_NODE_STATUS_IN_PROGRESS, actor, started=True)
    _set_current_node(workflow, ARD_NODE_OWNER_ASSIGNMENT, actor, status=ARD_STATUS_WAITING_OWNER_ASSIGNMENT, responsible_user=actor)
    log_security_event("ard_internal_sync_completed", user=actor, project=workflow.project, trainer_item=workflow.trainer_item, workflow_type=ARD_WORKFLOW_TYPE, node_id=ARD_NODE_INTERNAL_SYNC, status="Success")
    return {"success": True, "workspace": get_ard_workspace(trainer_item, actor)}


def assign_ard_project_owner(trainer_item: str, project_owner: str, actor: str) -> dict[str, Any]:
    import frappe

    _require_role(actor, "ARD Manager")
    workflow = _workflow_for_item(trainer_item)
    if workflow.current_node != ARD_NODE_OWNER_ASSIGNMENT:
        frappe.throw("ARD project owner assignment is not active for this workflow.", frappe.PermissionError)
    owner = _validate_ard_users([project_owner])[0]
    workflow.project_owner = owner
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _upsert_team_member(workflow, owner, actor, is_project_owner=1)
    _update_node_state(workflow, ARD_NODE_OWNER_ASSIGNMENT, ARD_NODE_STATUS_COMPLETED, actor, responsible_user=owner, completed=True, display_data={"Project Owner": _user_full_name(owner)})
    _update_node_state(workflow, ARD_NODE_TEAM_SELECTION, ARD_NODE_STATUS_IN_PROGRESS, actor, responsible_user=owner, started=True)
    _set_current_node(workflow, ARD_NODE_TEAM_SELECTION, actor, status=ARD_STATUS_WAITING_TEAM_SELECTION, responsible_user=owner)
    notify_many(
        [owner],
        title="ARD project ownership assigned",
        message="You have been assigned as the ARD project owner.",
        notification_type="ARD_PROJECT_OWNER_ASSIGNED",
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        workflow_type=ARD_WORKFLOW_TYPE,
        node_id=ARD_NODE_TEAM_SELECTION,
        action_url=project_action_url("ard", workflow.project, workflow.trainer_item),
        priority="High",
    )
    log_security_event("ard_owner_assigned", user=actor, target_user=owner, project=workflow.project, trainer_item=workflow.trainer_item, workflow_type=ARD_WORKFLOW_TYPE, node_id=ARD_NODE_OWNER_ASSIGNMENT, status="Success")
    return {"success": True, "workspace": get_ard_workspace(trainer_item, actor)}


def select_ard_team(trainer_item: str, users: list[str], actor: str) -> dict[str, Any]:
    import frappe

    workflow = _workflow_for_item(trainer_item)
    if workflow.project_owner != actor:
        frappe.throw("Only the ARD project owner can select the ARD team.", frappe.PermissionError)
    if workflow.current_node != ARD_NODE_TEAM_SELECTION:
        frappe.throw("ARD team selection is not active for this workflow.", frappe.PermissionError)
    selected = [user for user in _validate_ard_users(users) if user != actor]
    for row in frappe.get_all("ARD Workflow Team Member", filters={"workflow_instance": workflow.name, "is_project_owner": 0, "is_active": 1}, pluck="name"):
        frappe.db.set_value("ARD Workflow Team Member", row, "is_active", 0, update_modified=False)
    for user in selected:
        _upsert_team_member(workflow, user, actor)
    completed_at = datetime.now(CAIRO_TZ)
    progress_meeting_at = calculate_progress_review_meeting_at(completed_at)
    meeting = _upsert_ard_meeting(
        workflow=workflow,
        meeting_type=MEETING_TYPE_PROGRESS_REVIEW,
        node_id=ARD_NODE_PROGRESS_REVIEW,
        title="Progress Review Meeting",
        scheduled_at=progress_meeting_at,
        actor=actor,
        participant_users=selected,
    )
    workflow.progress_review_meeting = meeting
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _update_node_state(workflow, ARD_NODE_TEAM_SELECTION, ARD_NODE_STATUS_COMPLETED, actor, responsible_user=actor, completed=True, display_data={"Selected Team": len(selected)})
    _update_node_state(workflow, ARD_NODE_PROGRESS_REVIEW, ARD_NODE_STATUS_IN_PROGRESS, actor, responsible_user=actor, started=True, display_data={"Meeting": meeting, "Scheduled At": to_cairo_iso(progress_meeting_at)})
    _set_current_node(workflow, ARD_NODE_PROGRESS_REVIEW, actor, status=ARD_STATUS_WAITING_PROGRESS_REVIEW, responsible_user=actor)
    notify_many(
        selected + [actor],
        title="ARD team selected",
        message="The ARD team has been selected and the Progress Review Meeting was created.",
        notification_type="ARD_TEAM_SELECTED",
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        workflow_type=ARD_WORKFLOW_TYPE,
        node_id=ARD_NODE_PROGRESS_REVIEW,
        action_url="/meetings",
        priority="High",
    )
    log_security_event("ard_team_selected", user=actor, project=workflow.project, trainer_item=workflow.trainer_item, workflow_type=ARD_WORKFLOW_TYPE, node_id=ARD_NODE_TEAM_SELECTION, status="Success", message=f"{len(selected)} team member(s)")
    return {"success": True, "workspace": get_ard_workspace(trainer_item, actor)}


def submit_progress_review_outcome(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    workflow = _workflow_for_item(trainer_item)
    if workflow.project_owner != actor:
        frappe.throw("Only the ARD project owner can submit the progress review outcome.", frappe.PermissionError)
    if workflow.current_node != ARD_NODE_PROGRESS_REVIEW:
        frappe.throw("Progress Review Meeting is not active for this workflow.", frappe.PermissionError)
    outcome = str(payload.get("outcome") or payload.get("progress_outcome") or "").strip().upper().replace("-", "_").replace(" ", "_")
    if outcome != ARD_PROGRESS_OUTCOME_ON_PLAN:
        frappe.throw("Request Interruption outcomes will be handled by the ARD interruption workflow.", frappe.ValidationError)
    if workflow.progress_review_meeting:
        frappe.db.set_value(
            "BEDO Meeting",
            workflow.progress_review_meeting,
            {"status": MEETING_STATUS_COMPLETED, "completed_at": to_storage_datetime(datetime.now(CAIRO_TZ))},
            update_modified=False,
        )
    workflow.progress_review_outcome = ARD_PROGRESS_OUTCOME_ON_PLAN
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _update_node_state(workflow, ARD_NODE_PROGRESS_REVIEW, ARD_NODE_STATUS_COMPLETED, actor, responsible_user=actor, completed=True, display_data={"Outcome": "On Plan"})
    for node_id in [ARD_NODE_GM_APPROVAL, ARD_NODE_COMMAND_CENTER_PROCUREMENT, ARD_NODE_ELECTRONICS_SYSTEM_DESIGN, ARD_NODE_CONCEPT_PROOF]:
        _update_node_state(workflow, node_id, ARD_NODE_STATUS_NOT_APPLICABLE, actor)
    _update_node_state(workflow, ARD_NODE_SCMDP_SUBMISSION, ARD_NODE_STATUS_IN_PROGRESS, actor, responsible_user=actor, started=True)
    _set_current_node(workflow, ARD_NODE_SCMDP_SUBMISSION, actor, status=ARD_STATUS_WAITING_SCMDP, responsible_user=actor)
    log_security_event("ard_progress_review_outcome", user=actor, project=workflow.project, trainer_item=workflow.trainer_item, workflow_type=ARD_WORKFLOW_TYPE, node_id=ARD_NODE_PROGRESS_REVIEW, status="Success", message="On Plan")
    return {"success": True, "workspace": get_ard_workspace(trainer_item, actor)}


def submit_scmdp(trainer_item: str, payload: dict[str, Any], actor: str) -> dict[str, Any]:
    import frappe

    workflow = _workflow_for_item(trainer_item)
    if workflow.project_owner != actor:
        frappe.throw("Only the ARD project owner can submit SCMDP.", frappe.PermissionError)
    if workflow.current_node != ARD_NODE_SCMDP_SUBMISSION:
        frappe.throw("SCMDP submission is not active for this workflow.", frappe.PermissionError)
    scmdp_path = str(payload.get("scmdp_path") or "").strip()
    if not scmdp_path:
        frappe.throw("SCMDP path is required.", frappe.ValidationError)
    if not payload.get("checklist_confirmed") and not payload.get("scmdp_checklist_confirmed"):
        frappe.throw("SCMDP checklist confirmation is required.", frappe.ValidationError)
    now = _utcnow()
    workflow.scmdp_path = scmdp_path
    workflow.scmdp_checklist_confirmed = 1
    workflow.scmdp_submitted_by = actor
    workflow.scmdp_submitted_at = now
    workflow.completed_by = actor
    workflow.completed_at = now
    workflow.status = ARD_STATUS_COMPLETE
    workflow.flags.ignore_permissions = True
    workflow.save(ignore_permissions=True)
    _update_node_state(workflow, ARD_NODE_SCMDP_SUBMISSION, ARD_NODE_STATUS_COMPLETED, actor, responsible_user=actor, completed=True, display_data={"SCMDP Path": scmdp_path})
    _set_current_node(workflow, ARD_NODE_SCMDP_SUBMISSION, actor, status=ARD_STATUS_COMPLETE, responsible_user="")
    notify_many(
        _active_users_with_role("General Manager") + _active_users_with_role("ARD Manager"),
        title="ARD workflow complete",
        message="SCMDP was submitted and the ARD workflow is complete.",
        notification_type="ARD_WORKFLOW_COMPLETE",
        project=workflow.project,
        trainer_item=workflow.trainer_item,
        workflow_type=ARD_WORKFLOW_TYPE,
        node_id=ARD_NODE_SCMDP_SUBMISSION,
        action_url=project_action_url("ard", workflow.project, workflow.trainer_item),
        priority="Normal",
    )
    log_security_event("ard_scmdp_submitted", user=actor, project=workflow.project, trainer_item=workflow.trainer_item, workflow_type=ARD_WORKFLOW_TYPE, node_id=ARD_NODE_SCMDP_SUBMISSION, status="Success", message=scmdp_path)
    return {"success": True, "workspace": get_ard_workspace(trainer_item, actor)}
