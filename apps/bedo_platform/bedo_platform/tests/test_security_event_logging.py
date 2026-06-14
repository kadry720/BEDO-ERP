from bedo_platform.services.security_audit_service import sanitize_message


def test_security_event_message_redacts_passwords():
    assert sanitize_message("password=secret") == "[redacted security message]"


def test_security_event_message_keeps_safe_text():
    assert sanitize_message("login failure") == "login failure"
