import pytest

from bedo_platform.services.project_service import _validate_project_payload


def test_project_code_uses_required_format_and_allows_duplicate_semantics():
    payload = {
        "project_name": "Test Project",
        "project_code": "05/26",
        "end_user": "BEDO",
        "po_deadline_date": "2026-06-30",
    }

    assert _validate_project_payload(payload)["project_code"] == "05/26"


def test_project_code_rejects_invalid_format():
    with pytest.raises(ValueError, match="format 05/26"):
        _validate_project_payload(
            {
                "project_name": "Test Project",
                "project_code": "5/2026",
                "end_user": "BEDO",
                "po_deadline_date": "2026-06-30",
            }
        )
