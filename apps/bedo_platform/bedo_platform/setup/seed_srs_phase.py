from __future__ import annotations

from bedo_platform.constants import SRS_SECTION_OPTIONS

SECTION_PREFIX = {
    "Electronics": "srselectronics",
    "Electrical": "srselectrical",
    "Control": "srscontrol",
    "Mechatronics": "srsmechatronics",
    "Mechanical": "srsmechanical",
    "Mechanical Design": "srsmechanicaldesign",
}


def _table_exists(table_name: str) -> bool:
    import frappe

    return bool(frappe.db.sql("show tables like %s", table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    import frappe

    return bool(
        frappe.db.sql(
            """
            select index_name
            from information_schema.statistics
            where table_schema = database()
              and table_name = %s
              and index_name = %s
            limit 1
            """,
            (table_name, index_name),
        )
    )


def _ensure_index(table_name: str, index_name: str, columns: str) -> None:
    import frappe

    if _table_exists(table_name) and not _index_exists(table_name, index_name):
        frappe.db.sql(f"create index {index_name} on `{table_name}` ({columns})")


def ensure_indexes() -> None:
    _ensure_index("tabBEDO Trainer Item", "idx_bedo_item_project_node_user_status", "project, current_node, current_responsible_user, status")
    _ensure_index("tabSRS Workflow Instance", "idx_srs_instance_project_status_owner_node", "project, status, project_owner, current_node")
    _ensure_index("tabSRS Workflow Instance", "idx_srs_instance_trainer_item", "trainer_item")
    _ensure_index("tabSRS Workflow Node State", "idx_srs_node_workflow_node_status_user", "workflow_instance, node_id, status, responsible_user")
    _ensure_index("tabBEDO Deadline", "idx_bedo_deadline_item_node_status_due", "trainer_item, node_id, status, due_at")
    _ensure_index("tabBEDO Deadline", "idx_bedo_deadline_status_due_overdue", "status, due_at, overdue_notified_at")
    _ensure_index("tabBEDO Deadline", "idx_bedo_deadline_status_start_due_reminder", "status, start_at, due_at, reminder_notified_at")
    _ensure_index("tabBEDO Notification", "idx_bedo_notification_user_read_created", "recipient_user, is_read, created_at")
    _ensure_index("tabBEDO Security Event", "idx_bedo_audit_project_item_event_created", "project, trainer_item, event_type, created_at")
    _ensure_index("tabBEDO Security Event", "idx_bedo_audit_created_status_event", "created_at, status, event_type")
    _ensure_index("tabSRS Team", "idx_srs_team_leader_active", "team_leader_user, is_active")
    _ensure_index("tabSRS Team Member", "idx_srs_team_member_team_user_active", "team, engineer_user, is_active")
    _ensure_index("tabBEDO Command Center Handoff", "idx_bedo_cc_handoff_project_item_status", "project, trainer_item, status, is_active")
    _ensure_index("tabBEDO Command Center Handoff", "idx_bedo_cc_handoff_responsible_status", "responsible_user, status, is_active")
    _ensure_index("tabBEDO Supplier File", "idx_bedo_supplier_project_item_status", "project, trainer_item, status, is_active")
    _ensure_index("tabBEDO Supplier File", "idx_bedo_supplier_responsible_status", "responsible_user, status, is_active")


def _section_key(section_name: str) -> str:
    return section_name.upper().replace(" ", "_")


def _user(username: str) -> str:
    import frappe

    return frappe.db.get_value("User", {"username": username}, "name") or ""


def _upsert_srs_section(section_name: str) -> str:
    import frappe

    section_key = _section_key(section_name)
    existing = frappe.db.get_value("SRS Section", {"section_key": section_key}, "name")
    doc = frappe.get_doc("SRS Section", existing) if existing else frappe.new_doc("SRS Section")
    doc.section_name = section_name
    doc.section_key = section_key
    doc.is_active = 1
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    return doc.name


def _upsert_srs_team(section_name: str) -> None:
    import frappe

    prefix = SECTION_PREFIX[section_name]
    section = _upsert_srs_section(section_name)
    leader = _user(f"{prefix}tl")
    if not leader:
        return
    team_name = f"SRS {section_name} Team"
    existing = frappe.db.get_value("SRS Team", {"team_name": team_name}, "name")
    doc = frappe.get_doc("SRS Team", existing) if existing else frappe.new_doc("SRS Team")
    doc.section = section
    doc.team_name = team_name
    doc.team_leader_user = leader
    doc.is_active = 1
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)

    active_members = set()
    for index in range(1, 5):
        engineer = _user(f"{prefix}eng{index}")
        if not engineer:
            continue
        active_members.add(engineer)
        existing_member = frappe.db.get_value("SRS Team Member", {"team": doc.name, "engineer_user": engineer}, "name")
        member = frappe.get_doc("SRS Team Member", existing_member) if existing_member else frappe.new_doc("SRS Team Member")
        member.team = doc.name
        member.engineer_user = engineer
        member.is_active = 1
        member.flags.ignore_permissions = True
        if existing_member:
            member.save(ignore_permissions=True)
        else:
            member.insert(ignore_permissions=True)

    for member_name in frappe.get_all("SRS Team Member", filters={"team": doc.name, "is_active": 1}, pluck="name"):
        member_user = frappe.db.get_value("SRS Team Member", member_name, "engineer_user")
        if member_user not in active_members:
            frappe.db.set_value("SRS Team Member", member_name, "is_active", 0, update_modified=False)


def execute() -> None:
    import frappe

    ensure_indexes()
    if _table_exists("tabSRS Section"):
        for section_name in SRS_SECTION_OPTIONS:
            _upsert_srs_team(section_name)
    frappe.db.commit()
