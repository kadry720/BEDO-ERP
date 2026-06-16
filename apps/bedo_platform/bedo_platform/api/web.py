from __future__ import annotations

import frappe

from bedo_platform.constants import FRAPPE_DESK_TECHNICAL_ROLES, VISIBLE_BUSINESS_ROLE_NAMES, VISIBLE_DEPARTMENTS
from bedo_platform.services.auth_service import get_safe_user_context, login_for_web
from bedo_platform.services.profile_service import get_current_profile, update_current_profile
from bedo_platform.services.deadline_service import (
    calculate_next_working_start,
    calculate_working_due_at,
    get_deadlines_for_trainer_item,
    run_deadline_reminder_check,
    run_overdue_check,
)
from bedo_platform.services.notification_service import list_my_notifications, mark_all_notifications_read, mark_notification_read
from bedo_platform.services.project_service import (
    add_trainer_item as add_bedo_trainer_item,
    approve_srs_approval as approve_srs_approval_service,
    approve_srs_approval_with_edits as approve_srs_approval_with_edits_service,
    approve_srs_case_as_gm as approve_srs_case_as_gm_service,
    approve_srs_deadline_as_srs_manager as approve_srs_deadline_as_srs_manager_service,
    assign_srs_project_owner as assign_srs_project_owner_service,
    complete_command_center_case_1 as complete_command_center_case_1_service,
    create_project as create_bedo_project,
    delete_project_cascade as delete_bedo_project_cascade,
    delete_trainer_item as delete_bedo_trainer_item,
    deliver_supplier_file as deliver_supplier_file_service,
    finalize_project_details as finalize_bedo_project_details,
    get_command_center_handoff_workspace as get_command_center_handoff_workspace_service,
    get_project_detail as get_bedo_project_detail,
    get_approval_detail as get_approval_detail_service,
    get_pending_approval_count as get_pending_approval_count_service,
    get_supplier_files_for_trainer_item as get_supplier_files_for_trainer_item_service,
    get_srs_flowchart_definition as get_srs_flowchart_definition_service,
    get_srs_trainer_item_audit_trail as get_srs_trainer_item_audit_trail_service,
    get_trainer_item_workspace as get_bedo_trainer_item_workspace,
    list_eligible_project_owners as list_eligible_project_owners_service,
    list_eligible_srs_team_members as list_eligible_srs_team_members_service,
    list_my_pending_approvals as list_my_pending_approvals_service,
    list_projects,
    list_report_to_candidates as list_report_to_candidates_service,
    list_trainer_items_for_project as list_bedo_trainer_items_for_project,
    release_project_to_srs as release_bedo_project_to_srs,
    request_pmdp_extension as request_pmdp_extension_service,
    request_supplier_deadline_extension as request_supplier_deadline_extension_service,
    select_srs_team as select_srs_team_service,
    submit_pmdp_gate_path as submit_pmdp_gate_path_service,
    submit_pmdp_path as submit_pmdp_path_service,
    submit_command_center_srs_ard_decision as submit_command_center_approval_service,
    submit_mandatory_coordination as submit_mandatory_coordination_service,
    submit_srs_bmdp_path as submit_srs_bmdp_path_service,
    submit_srs_deliverables_matrix as submit_srs_deliverables_matrix_service,
    update_project_details as update_bedo_project_details,
    update_trainer_item as update_bedo_trainer_item,
)
from bedo_platform.services.routing_service import ensure_dashboard_access, get_current_user_landing_route
from bedo_platform.services.security_audit_service import list_security_events_for_user
from bedo_platform.services.service_auth import require_service_auth, validate_service_request
from bedo_platform.services.user_management_service import (
    create_user_from_admin,
    disable_user,
    list_users_for_admin,
    soft_delete_user,
    update_user_from_admin,
    update_user_roles,
)


def service_api(fn):
    return frappe.whitelist(allow_guest=True)(require_service_auth(fn))


def _payload(value):
    if isinstance(value, str):
        return frappe.parse_json(value)
    return value or {}


@service_api
def login(username: str, password: str):
    return login_for_web(username, password)


@service_api
def me():
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return get_safe_user_context(user)


@service_api
def logout():
    user = validate_service_request()
    if user:
        from bedo_platform.services.security_audit_service import log_security_event

        log_security_event("logout", user=user, status="Success")
    return {"success": True}


@service_api
def get_landing_route():
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return {"route": get_current_user_landing_route(user)}


@service_api
def ensure_route_access(route: str):
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return ensure_dashboard_access(route, user)


@service_api
def get_admin_bootstrap():
    user = validate_service_request()
    if not user:
        frappe.throw("User context is required.", frappe.PermissionError)
    return {
        "roles": VISIBLE_BUSINESS_ROLE_NAMES,
        "departments": VISIBLE_DEPARTMENTS,
        "technical_desk_roles": sorted(FRAPPE_DESK_TECHNICAL_ROLES),
        "users": list_users_for_admin(user),
    }


@service_api
def list_users():
    user = validate_service_request()
    return {"users": list_users_for_admin(user)}


@service_api
def create_user(payload):
    user = validate_service_request()
    return create_user_from_admin(_payload(payload), actor=user)


@service_api
def update_user(target_user: str, payload):
    user = validate_service_request()
    return update_user_from_admin(target_user, _payload(payload), actor=user)


@service_api
def assign_roles(target_user: str, roles, primary_department: str = ""):
    user = validate_service_request()
    if isinstance(roles, str):
        roles = frappe.parse_json(roles)
    return update_user_roles(target_user, roles, primary_department, actor=user)


@service_api
def set_user_enabled(target_user: str, enabled: int):
    user = validate_service_request()
    if int(enabled):
        frappe.throw("Re-enable user is not implemented in this phase.", frappe.PermissionError)
    return disable_user(target_user, actor=user)


@service_api
def delete_user(target_user: str):
    user = validate_service_request()
    return soft_delete_user(target_user, actor=user)


@service_api
def get_my_profile():
    user = validate_service_request()
    return get_current_profile(user)


@service_api
def update_my_profile(payload):
    user = validate_service_request()
    return update_current_profile(_payload(payload), user)


@service_api
def list_security_events(limit: int = 50, filters=None):
    user = validate_service_request()
    payload = _payload(filters)
    payload.setdefault("limit", limit)
    return list_security_events_for_user(user, payload)


@service_api
def create_project(payload):
    user = validate_service_request()
    return create_bedo_project(_payload(payload), actor=user)


@service_api
def update_project_details(project: str, payload):
    user = validate_service_request()
    return update_bedo_project_details(project, _payload(payload), actor=user)


@service_api
def delete_project(project: str):
    user = validate_service_request()
    return delete_bedo_project_cascade(project, actor=user)


@service_api
def finalize_project_details(project: str):
    user = validate_service_request()
    return finalize_bedo_project_details(project, actor=user)


@service_api
def add_trainer_item(project: str, payload):
    user = validate_service_request()
    return add_bedo_trainer_item(project, _payload(payload), actor=user)


@service_api
def update_trainer_item(trainer_item: str, payload):
    user = validate_service_request()
    return update_bedo_trainer_item(trainer_item, _payload(payload), actor=user)


@service_api
def delete_trainer_item(trainer_item: str):
    user = validate_service_request()
    return delete_bedo_trainer_item(trainer_item, actor=user)


@service_api
def release_project_to_srs(project: str):
    user = validate_service_request()
    return release_bedo_project_to_srs(project, actor=user)


@service_api
def list_projects_for_user(page: int = 1, page_size: int = 25):
    user = validate_service_request()
    return list_projects(user, page=page, page_size=page_size)


@service_api
def get_project_detail(project: str):
    user = validate_service_request()
    return get_bedo_project_detail(project, actor=user)


@service_api
def list_trainer_items_for_project(project: str):
    user = validate_service_request()
    return list_bedo_trainer_items_for_project(project, actor=user)


@service_api
def get_trainer_item_workspace(trainer_item: str):
    user = validate_service_request()
    return get_bedo_trainer_item_workspace(trainer_item, actor=user)


@service_api
def get_srs_flowchart_definition():
    validate_service_request()
    return get_srs_flowchart_definition_service()


@service_api
def get_srs_workflow_instance(trainer_item: str):
    user = validate_service_request()
    workspace = get_bedo_trainer_item_workspace(trainer_item, actor=user)
    return {
        "workflow": workspace.get("workflow"),
        "node_states": workspace.get("node_states"),
        "deadlines": workspace.get("deadlines"),
        "node_availability": workspace.get("node_availability"),
        "server_now": workspace.get("server_now"),
    }


@service_api
def assign_srs_project_owner(trainer_item: str, project_owner: str):
    user = validate_service_request()
    return assign_srs_project_owner_service(trainer_item, project_owner, actor=user)


@service_api
def select_srs_team(trainer_item: str, users):
    user = validate_service_request()
    if isinstance(users, str):
        users = frappe.parse_json(users)
    return select_srs_team_service(trainer_item, users or [], actor=user)


@service_api
def submit_mandatory_coordination(trainer_item: str, payload):
    user = validate_service_request()
    return submit_mandatory_coordination_service(trainer_item, _payload(payload), actor=user)


@service_api
def submit_srs_deliverables_matrix(trainer_item: str, payload):
    user = validate_service_request()
    return submit_srs_deliverables_matrix_service(trainer_item, _payload(payload), actor=user)


@service_api
def approve_srs_case_as_gm(trainer_item: str, payload=None):
    user = validate_service_request()
    return approve_srs_case_as_gm_service(trainer_item, _payload(payload), actor=user)


@service_api
def approve_srs_deadline_as_srs_manager(trainer_item: str, payload=None):
    user = validate_service_request()
    return approve_srs_deadline_as_srs_manager_service(trainer_item, _payload(payload), actor=user)


@service_api
def submit_srs_bmdp_path(trainer_item: str, bmdp_path: str):
    user = validate_service_request()
    return submit_srs_bmdp_path_service(trainer_item, bmdp_path, actor=user)


@service_api
def submit_pmdp_gate_path(trainer_item: str, pmdp_path: str):
    user = validate_service_request()
    return submit_pmdp_gate_path_service(trainer_item, pmdp_path, actor=user)


@service_api
def request_pmdp_extension(trainer_item: str, payload):
    user = validate_service_request()
    return request_pmdp_extension_service(trainer_item, _payload(payload), actor=user)


@service_api
def submit_pmdp_path(trainer_item: str, pmdp_path: str):
    user = validate_service_request()
    return submit_pmdp_path_service(trainer_item, pmdp_path, actor=user)


@service_api
def submit_command_center_approval(trainer_item: str, payload):
    user = validate_service_request()
    return submit_command_center_approval_service(trainer_item, _payload(payload), actor=user)


@service_api
def get_command_center_handoff(trainer_item: str):
    user = validate_service_request()
    return get_command_center_handoff_workspace_service(trainer_item, actor=user)


@service_api
def submit_command_center_decision(trainer_item: str, payload):
    user = validate_service_request()
    return submit_command_center_approval_service(trainer_item, _payload(payload), actor=user)


@service_api
def complete_command_center_case_1(trainer_item: str):
    user = validate_service_request()
    return complete_command_center_case_1_service(trainer_item, actor=user)


@service_api
def get_supplier_files(trainer_item: str):
    user = validate_service_request()
    return get_supplier_files_for_trainer_item_service(trainer_item, actor=user)


@service_api
def deliver_supplier_file(supplier_file: str):
    user = validate_service_request()
    return deliver_supplier_file_service(supplier_file, actor=user)


@service_api
def request_supplier_extension(supplier_file: str, payload):
    user = validate_service_request()
    return request_supplier_deadline_extension_service(supplier_file, _payload(payload), actor=user)


@service_api
def list_my_pending_approvals(status: str = "WAITING"):
    user = validate_service_request()
    return list_my_pending_approvals_service(user, status=status)


@service_api
def get_pending_approval_count():
    user = validate_service_request()
    return get_pending_approval_count_service(user)


@service_api
def get_approval_detail(approval: str):
    user = validate_service_request()
    return get_approval_detail_service(approval, actor=user)


@service_api
def approve_srs_approval(approval: str, payload=None):
    user = validate_service_request()
    return approve_srs_approval_service(approval, actor=user, payload=_payload(payload))


@service_api
def approve_srs_approval_with_edits(approval: str, payload):
    user = validate_service_request()
    return approve_srs_approval_with_edits_service(approval, _payload(payload), actor=user)


@service_api
def get_srs_trainer_item_audit_trail(trainer_item: str):
    user = validate_service_request()
    return get_srs_trainer_item_audit_trail_service(trainer_item, actor=user)


@service_api
def get_deadlines_for_item(trainer_item: str):
    validate_service_request()
    return {"deadlines": get_deadlines_for_trainer_item(trainer_item)}


@service_api
def run_deadline_reminders():
    validate_service_request()
    return run_deadline_reminder_check()


@service_api
def run_overdue_deadline_check():
    validate_service_request()
    return run_overdue_check()


@service_api
def list_notifications(limit: int = 25):
    user = validate_service_request()
    return list_my_notifications(user, limit=int(limit or 25))


@service_api
def mark_notification_as_read(notification: str):
    user = validate_service_request()
    return mark_notification_read(user, notification)


@service_api
def mark_all_notifications_as_read():
    user = validate_service_request()
    return mark_all_notifications_read(user)


@service_api
def list_report_to_candidates():
    user = validate_service_request()
    return list_report_to_candidates_service(user)


@service_api
def list_eligible_project_owners():
    user = validate_service_request()
    return list_eligible_project_owners_service(user)


@service_api
def list_eligible_srs_team_members(workflow_instance: str = ""):
    user = validate_service_request()
    return list_eligible_srs_team_members_service(user, workflow_instance or None)


@service_api
def health():
    validate_service_request()
    frappe.db.sql("select 1")
    cache_ok = False
    try:
        cache = frappe.cache()
        key = "bedo_health_check"
        cache.set_value(key, "1", expires_in_sec=30)
        cache_ok = cache.get_value(key) == "1"
        cache.delete_value(key)
    except Exception:
        cache_ok = False
    return {
        "status": "ok",
        "database": "ok",
        "cache": "ok" if cache_ok else "unavailable",
        "app": "bedo_platform",
    }
