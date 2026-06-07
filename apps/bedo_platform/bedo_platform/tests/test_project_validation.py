from bedo_platform.services.project_service import _validate_project_payload


def test_project_payload_accepts_any_project_code_format():
    payload = {
        "project_name": "Test Project",
        "project_code": "5/2026",
        "end_user": "BEDO",
        "po_deadline_date": "2026-06-30",
    }

    assert _validate_project_payload(payload)["project_code"] == "5/2026"


def test_project_payload_fills_database_required_values_when_blank():
    values = _validate_project_payload({})

    assert values["project_name"] == "Untitled Project"
    assert values["project_code"].startswith("PRJ-")
    assert values["end_user"] == "Unspecified"
    assert values["po_deadline_date"]


def test_project_payload_replaces_invalid_deadline_with_default_date():
    values = _validate_project_payload({"po_deadline_date": "not-a-date"})

    assert values["po_deadline_date"] != "not-a-date"
