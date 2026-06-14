from __future__ import annotations

import hashlib
import hmac
import os
import time
from functools import wraps
from typing import Any, Callable

from bedo_platform.services.config_validation import require_configured_secret


SERVICE_HEADER = "X-BEDO-Service"
USER_HEADER = "X-BEDO-User"
TIMESTAMP_HEADER = "X-BEDO-Timestamp"
NONCE_HEADER = "X-BEDO-Nonce"
SIGNATURE_HEADER = "X-BEDO-Signature"
MAX_CLOCK_SKEW_SECONDS = 300


def _get_secret() -> str:
    try:
        import frappe

        value = frappe.conf.get("BEDO_WEB_SERVICE_SECRET") or frappe.conf.get("bedo_web_service_secret")
        if value:
            return require_configured_secret("BEDO_WEB_SERVICE_SECRET", str(value))
    except Exception:
        pass
    return require_configured_secret("BEDO_WEB_SERVICE_SECRET", os.environ.get("BEDO_WEB_SERVICE_SECRET", ""))


def _request_body() -> bytes:
    try:
        import frappe

        request = getattr(frappe.local, "request", None)
        if request:
            return request.get_data() or b""
    except Exception:
        pass
    return b""


def _request_path() -> str:
    try:
        import frappe

        request = getattr(frappe.local, "request", None)
        if request:
            return request.path or ""
    except Exception:
        pass
    return ""


def _cache_set_if_absent(cache: Any, key: str) -> bool:
    redis_client = getattr(cache, "_redis", None) or getattr(cache, "redis_server", None)
    if redis_client and hasattr(redis_client, "set"):
        result = redis_client.set(key, "1", nx=True, ex=MAX_CLOCK_SKEW_SECONDS)
        return bool(result)
    if cache.get_value(key):
        return False
    cache.set_value(key, "1", expires_in_sec=MAX_CLOCK_SKEW_SECONDS)
    return True


def _mark_nonce_used(nonce: str) -> None:
    import frappe

    cache = frappe.cache()
    key = f"bedo_web_nonce:{nonce}"
    if not _cache_set_if_absent(cache, key):
        frappe.throw("Invalid service request.", frappe.PermissionError)


def _expected_signature(
    *,
    secret: str,
    service: str,
    user: str,
    timestamp: str,
    nonce: str,
    method: str,
    path: str,
    body: bytes,
) -> str:
    body_hash = hashlib.sha256(body).hexdigest()
    payload = "\n".join([service, user, timestamp, nonce, method.upper(), path, body_hash])
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def validate_service_request() -> str:
    import frappe

    cached_user = getattr(frappe.local, "bedo_service_auth_user", None)
    if cached_user is not None:
        return str(cached_user)

    secret = _get_secret()
    if not secret:
        frappe.throw("BEDO web service authentication is not configured.", frappe.PermissionError)

    request = getattr(frappe.local, "request", None)
    headers = request.headers if request else {}
    service = str(headers.get(SERVICE_HEADER, "")).strip()
    user = str(headers.get(USER_HEADER, "")).strip()
    timestamp = str(headers.get(TIMESTAMP_HEADER, "")).strip()
    nonce = str(headers.get(NONCE_HEADER, "")).strip()
    signature = str(headers.get(SIGNATURE_HEADER, "")).strip()

    if service != "bedo-web" or not timestamp or not nonce or not signature:
        frappe.throw("Invalid service request.", frappe.PermissionError)

    try:
        request_time = int(timestamp)
    except ValueError:
        frappe.throw("Invalid service request.", frappe.PermissionError)

    if abs(int(time.time()) - request_time) > MAX_CLOCK_SKEW_SECONDS:
        frappe.throw("Invalid service request.", frappe.PermissionError)

    expected = _expected_signature(
        secret=secret,
        service=service,
        user=user,
        timestamp=timestamp,
        nonce=nonce,
        method=getattr(request, "method", "POST") if request else "POST",
        path=_request_path(),
        body=_request_body(),
    )
    if not hmac.compare_digest(expected, signature):
        frappe.throw("Invalid service request.", frappe.PermissionError)

    _mark_nonce_used(nonce)

    if user:
        enabled = frappe.db.get_value("User", user, "enabled")
        if not enabled:
            frappe.throw("Invalid service user context.", frappe.PermissionError)
    frappe.local.bedo_service_auth_user = user
    return user


def require_service_auth(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        validate_service_request()
        return fn(*args, **kwargs)

    wrapper.bedo_requires_service_auth = True  # type: ignore[attr-defined]
    return wrapper
