from __future__ import annotations

import hashlib
import hmac
import json
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
REQUEST_ID_HEADER = "X-BEDO-Request-ID"
MAX_CLOCK_SKEW_SECONDS = 300


def _get_secret() -> str:
    env_value = os.environ.get("BEDO_WEB_SERVICE_SECRET", "")
    if env_value:
        return require_configured_secret("BEDO_WEB_SERVICE_SECRET", env_value)
    try:
        import frappe

        value = frappe.conf.get("BEDO_WEB_SERVICE_SECRET") or frappe.conf.get("bedo_web_service_secret")
        if value:
            return require_configured_secret("BEDO_WEB_SERVICE_SECRET", str(value))
    except Exception:
        pass
    return require_configured_secret("BEDO_WEB_SERVICE_SECRET", "")


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


def _performance_logs_enabled() -> bool:
    setting = os.environ.get("BEDO_PERFORMANCE_LOGS", "").lower()
    if setting in {"0", "false"}:
        return False
    if setting in {"1", "true"}:
        return True
    mode = os.environ.get("BEDO_ENV") or os.environ.get("NODE_ENV") or "development"
    return mode.lower() not in {"local", "dev", "development", "test"}


def _user_fingerprint(user: str) -> str:
    if not user:
        return ""
    return hashlib.sha256(user.encode("utf-8")).hexdigest()[:16]


def _request_id() -> str:
    try:
        import frappe

        request = getattr(frappe.local, "request", None)
        headers = request.headers if request else {}
        return str(headers.get(REQUEST_ID_HEADER, "")).strip()
    except Exception:
        return ""


def _log_performance_event(*, route_or_method: str, status: str, duration_ms: float, user: str = "") -> None:
    if not _performance_logs_enabled():
        return
    try:
        import frappe

        payload: dict[str, str | float] = {
            "event": "bedo.performance",
            "layer": "frappe-service",
            "route_or_method": route_or_method,
            "status": status,
            "duration_ms": round(max(0, duration_ms), 2),
        }
        request_id = _request_id()
        if request_id:
            payload["request_id"] = request_id
        user_hash = _user_fingerprint(user)
        if user_hash:
            payload["user_hash"] = user_hash
        frappe.logger("bedo_platform").info(json.dumps(payload, separators=(",", ":")))
    except Exception:
        return


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
        started_at = time.perf_counter()
        user = ""
        status = "ok"
        try:
            user = validate_service_request()
            return fn(*args, **kwargs)
        except Exception:
            status = "error"
            raise
        finally:
            _log_performance_event(
                route_or_method=fn.__name__,
                status=status,
                duration_ms=(time.perf_counter() - started_at) * 1000,
                user=user,
            )

    wrapper.bedo_requires_service_auth = True  # type: ignore[attr-defined]
    return wrapper
