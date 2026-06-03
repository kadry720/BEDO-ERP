import frappe

from bedo_erp.security.policies import get_current_user, require_admin_read
from bedo_erp.shared.constants import AUDIT_EVENT_TYPES, AUTH_SOURCES


def write_access_audit_log(
    event_type,
    user=None,
    auth_source="Unknown",
    success=0,
    failure_reason=None,
    session_id=None,
):
    if event_type not in AUDIT_EVENT_TYPES:
        frappe.throw("Invalid audit event type.", frappe.ValidationError)
    if auth_source not in AUTH_SOURCES:
        auth_source = "Unknown"
    if not _audit_logging_enabled():
        return None
    doc = frappe.get_doc(
        {
            "doctype": "BEDO Access Audit Log",
            "user": user or get_current_user(),
            "event_type": event_type,
            "auth_source": auth_source,
            "success": 1 if success else 0,
            "failure_reason": failure_reason,
            "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else None,
            "user_agent": _get_user_agent(),
            "session_id": session_id or _get_session_id(),
            "created_at": frappe.utils.now_datetime(),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def write_permission_denied(message):
    return write_access_audit_log(
        event_type="Permission Denied",
        success=0,
        failure_reason=message,
    )


def get_logs(filters=None):
    require_admin_read()
    normalized_filters = normalize_filters(filters)
    rows = frappe.get_all(
        "BEDO Access Audit Log",
        filters=normalized_filters,
        fields=[
            "name",
            "user",
            "event_type",
            "auth_source",
            "success",
            "failure_reason",
            "ip_address",
            "user_agent",
            "session_id",
            "created_at",
        ],
        order_by="created_at desc",
        limit_page_length=200,
    )
    return rows


def normalize_filters(filters=None):
    payload = frappe.parse_json(filters) if isinstance(filters, str) else filters
    payload = payload or {}
    if not isinstance(payload, dict):
        frappe.throw("Audit filters must be an object.", frappe.ValidationError)
    query_filters = {}
    if payload.get("user"):
        query_filters["user"] = payload["user"]
    if payload.get("event_type"):
        if payload["event_type"] not in AUDIT_EVENT_TYPES:
            frappe.throw("Invalid audit event type.", frappe.ValidationError)
        query_filters["event_type"] = payload["event_type"]
    if "success" in payload:
        query_filters["success"] = 1 if frappe.utils.cint(payload["success"]) else 0
    if payload.get("from_date") and payload.get("to_date"):
        query_filters["created_at"] = ["between", [payload["from_date"], payload["to_date"]]]
    elif payload.get("from_date"):
        query_filters["created_at"] = [">=", payload["from_date"]]
    elif payload.get("to_date"):
        query_filters["created_at"] = ["<=", payload["to_date"]]
    return query_filters


def _audit_logging_enabled():
    try:
        return bool(frappe.get_single("BEDO Security Settings").enable_audit_logging)
    except Exception:
        return True


def _get_user_agent():
    request = getattr(frappe.local, "request", None)
    if not request:
        return None
    return request.headers.get("User-Agent")


def _get_session_id():
    session = getattr(frappe.local, "session", None)
    if session and getattr(session, "sid", None):
        return session.sid
    return getattr(frappe.session, "sid", None)
