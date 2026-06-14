import pytest

from bedo_platform.services.project_service import _validate_project_payload


def test_project_payload_accepts_any_project_code_format():
    payload = {
        "project_name": "Test Project",
        "project_code": "5/2026",
        "end_user": "BEDO",
        "po_deadline_date": "2026-06-30",
    }

    assert _validate_project_payload(payload)["project_code"] == "5/2026"


def test_project_payload_rejects_blank_text_fields_only():
    with pytest.raises(ValueError, match="Project name is required"):
        _validate_project_payload({})


def test_project_payload_rejects_invalid_deadline():
    with pytest.raises(ValueError, match="PO deadline date must be a valid date"):
        _validate_project_payload(
            {
                "project_name": "Test Project",
                "project_code": "5/2026",
                "end_user": "BEDO",
                "po_deadline_date": "not-a-date",
            }
        )
