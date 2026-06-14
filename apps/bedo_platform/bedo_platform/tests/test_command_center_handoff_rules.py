import pytest

from bedo_platform.services import project_service


def test_command_center_case_3_does_not_require_deadline():
    command_case, deadline = project_service._command_center_case_and_deadline(
        {"command_center_case": project_service.COMMAND_CENTER_CASE_3}
    )

    assert command_case == project_service.COMMAND_CENTER_CASE_3
    assert deadline == 0


def test_command_center_case_1_requires_positive_deadline():
    with pytest.raises(ValueError, match="Deadline is required"):
        project_service._command_center_case_and_deadline({"command_center_case": project_service.COMMAND_CENTER_CASE_1})

    command_case, deadline = project_service._command_center_case_and_deadline(
        {"command_center_case": project_service.COMMAND_CENTER_CASE_1, "deadline_days": "3"}
    )

    assert command_case == project_service.COMMAND_CENTER_CASE_1
    assert deadline == 3


def test_command_center_case_2_requires_positive_deadline():
    with pytest.raises(ValueError, match="Deadline must be greater than zero"):
        project_service._command_center_case_and_deadline(
            {"command_center_case": project_service.COMMAND_CENTER_CASE_2, "deadline_days": "0"}
        )
