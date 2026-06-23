from __future__ import annotations

from datetime import datetime
from typing import Any

from bedo_platform.constants import ARD_ROLES
from bedo_platform.services.notification_service import notify_many, project_action_url
from bedo_platform.services.security_audit_service import log_security_event
from bedo_platform.services.user_profile_service import assert_user_can_login

ARD_WORKFLOW_TYPE = "ARD"
ARD_STATUS_IN_PROGRESS = "ARD_IN_PROGRESS"
ARD_STATUS_COMPLETE = "ARD_COMPLETE"

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
    if status == ARD_NODE_STATUS_IN_PROGRESS:
        doc.started_at = _utcnow()
    if status == ARD_NODE_STATUS_COMPLETED:
        doc.started_at = _utcnow()
        doc.completed_at = _utcnow()
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)


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
