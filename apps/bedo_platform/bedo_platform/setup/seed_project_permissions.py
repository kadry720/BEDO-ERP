from __future__ import annotations

from datetime import datetime


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

    if not _index_exists(table_name, index_name):
        frappe.db.sql(f"create index {index_name} on `{table_name}` ({columns})")


def ensure_indexes() -> None:
    _ensure_index("tabBEDO Project", "idx_bedo_project_department_section_active", "department_key, section, is_active")
    _ensure_index("tabBEDO Project Assignment", "idx_bedo_assignment_project_stage_active", "project, stage, is_active")
    _ensure_index("tabBEDO Project Assignment", "idx_bedo_assignment_user_active", "assigned_to_user, is_active")
    _ensure_index("tabBEDO Project Assignment", "idx_bedo_assignment_stage_user", "stage, assigned_to_user")
    _ensure_index("tabARD Team", "idx_ard_team_leader_active", "team_leader, is_active")
    _ensure_index("tabARD Team Member", "idx_ard_team_member_team_user_active", "team, user, is_active")
    _ensure_index("tabARD Team Member", "idx_ard_team_member_user_active", "user, is_active")


def _user(username: str) -> str:
    import frappe

    return frappe.db.get_value("User", {"username": username}, "name") or ""


def _upsert_team(team_key: str, team_name: str, section: str, leader_username: str, engineer_usernames: list[str]) -> None:
    import frappe

    leader = _user(leader_username)
    if not leader:
        return
    existing = frappe.db.get_value("ARD Team", {"team_key": team_key}, "name")
    doc = frappe.get_doc("ARD Team", existing) if existing else frappe.new_doc("ARD Team")
    doc.team_key = team_key
    doc.team_name = team_name
    doc.section = section
    doc.team_leader = leader
    doc.is_active = 1
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)

    active_users = {leader}
    for engineer_username in engineer_usernames:
        engineer = _user(engineer_username)
        if not engineer:
            continue
        active_users.add(engineer)
        existing_member = frappe.db.get_value("ARD Team Member", {"team": doc.name, "user": engineer}, "name")
        member = frappe.get_doc("ARD Team Member", existing_member) if existing_member else frappe.new_doc("ARD Team Member")
        member.team = doc.name
        member.user = engineer
        member.role = "ARD Engineer"
        member.is_active = 1
        member.flags.ignore_permissions = True
        if existing_member:
            member.save(ignore_permissions=True)
        else:
            member.insert(ignore_permissions=True)

    for member_name in frappe.get_all("ARD Team Member", filters={"team": doc.name, "is_active": 1}, pluck="name"):
        member_user = frappe.db.get_value("ARD Team Member", member_name, "user")
        if member_user not in active_users:
            frappe.db.set_value("ARD Team Member", member_name, "is_active", 0, update_modified=False)


def _assignment_exists(project: str, stage: str) -> bool:
    import frappe

    return bool(frappe.db.exists("BEDO Project Assignment", {"project": project, "stage": stage, "is_active": 1}))


def _assign(project: str, stage: str, assigned_by: str, assigned_to_user: str, team: str = "") -> str:
    import frappe

    existing = frappe.db.get_value(
        "BEDO Project Assignment",
        {"project": project, "stage": stage, "assigned_to_user": assigned_to_user, "is_active": 1},
        "name",
    )
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": "BEDO Project Assignment",
            "project": project,
            "stage": stage,
            "assigned_by": assigned_by,
            "assigned_to_user": assigned_to_user,
            "assigned_to_role": stage,
            "team": team,
            "assigned_at": datetime.utcnow(),
            "is_active": 1,
        }
    )
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    return doc.name


def seed_permission_test_project() -> None:
    import frappe

    gm = _user("gm")
    manager = _user("ardmanager")
    section_head = _user("ardsectionhead1")
    team_leader = _user("ardteamleader1")
    engineer1 = _user("ardengineer1")
    engineer2 = _user("ardengineer2")
    if not all([gm, manager, section_head, team_leader, engineer1, engineer2]):
        return

    project = frappe.db.get_value(
        "BEDO Project",
        {"project_name": "Permission Test Electronics Cross Assignment"},
        "name",
    )
    if not project:
        doc = frappe.get_doc(
            {
                "doctype": "BEDO Project",
                "project_name": "Permission Test Electronics Cross Assignment",
                "department_key": "ARD",
                "section": "Electronics",
                "details": "Seeded project used to verify assignment-based visibility across sections.",
                "created_by_user": gm,
                "is_active": 1,
                "current_stage": "Created",
            }
        )
        doc.flags.ignore_permissions = True
        doc.insert(ignore_permissions=True)
        project = doc.name
    elif project != "Permission Test Electronics Cross Assignment" and not frappe.db.exists(
        "BEDO Project",
        "Permission Test Electronics Cross Assignment",
    ):
        project = frappe.rename_doc(
            "BEDO Project",
            project,
            "Permission Test Electronics Cross Assignment",
            force=True,
        )

    manager_assignment = _assign(project, "ARD Manager", gm, manager)
    section_assignment = _assign(project, "ARD Section Head", manager, section_head)
    team_assignment = _assign(project, "ARD Team Leader", section_head, team_leader)
    team = frappe.db.get_value("ARD Team", {"team_leader": team_leader, "is_active": 1}, "name") or ""
    if not _assignment_exists(project, "ARD Engineer"):
        _assign(project, "ARD Engineer", team_leader, engineer1, team)
        _assign(project, "ARD Engineer", team_leader, engineer2, team)
    frappe.db.set_value(
        "BEDO Project",
        project,
        {
            "current_stage": "Engineers Assigned",
            "manager_assignment": manager_assignment,
            "section_head_assignment": section_assignment,
            "team_leader_assignment": team_assignment,
        },
        update_modified=False,
    )


def execute() -> None:
    import frappe

    ensure_indexes()
    _upsert_team("ARD-TL-1", "ARD Team Leader 1 Team", "Electronics", "ardteamleader1", ["ardengineer1", "ardengineer2"])
    _upsert_team("ARD-TL-2", "ARD Team Leader 2 Team", "Mechanics", "ardteamleader2", ["ardengineer3", "ardengineer4"])
    seed_permission_test_project()
    frappe.db.commit()
