from pathlib import Path

import pytest

from bedo_platform.services import workflow_reset_service


def test_reset_targets_are_explicit_and_normalized():
    assert workflow_reset_service.normalize_reset_target("command_center") == workflow_reset_service.RESET_COMMAND_CENTER
    assert workflow_reset_service.normalize_reset_target("srs_action_paths") == workflow_reset_service.RESET_SRS_ACTION_PATHS
    assert workflow_reset_service.normalize_reset_target("srs_coordination") == workflow_reset_service.RESET_SRS_COORDINATION

    with pytest.raises(ValueError, match="Unsupported reset target"):
        workflow_reset_service.normalize_reset_target("ard")


def test_reset_service_exposes_required_entrypoints():
    assert callable(workflow_reset_service.reset_command_center)
    assert callable(workflow_reset_service.reset_srs_to_action_paths)
    assert callable(workflow_reset_service.reset_srs_to_coordination)
    assert callable(workflow_reset_service.execute_workflow_reset)


def test_reset_service_supersedes_operational_records_without_deleting_audit_events():
    source = Path("apps/bedo_platform/bedo_platform/services/workflow_reset_service.py").read_text(encoding="utf-8")

    assert "SUPERSEDED_BY_RESET" in source
    assert "BEDO Meeting" in source
    assert "SRS Approval" in source
    assert "BEDO Command Center Handoff" in source
    assert "BEDO Security Event" not in source
