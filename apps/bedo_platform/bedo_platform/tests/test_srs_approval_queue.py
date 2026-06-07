import sys
from types import SimpleNamespace

from bedo_platform.constants import (
    NODE_STATUS_COMPLETED,
    NODE_STATUS_WAITING_APPROVAL,
    SRS_NODE_GM_APPROVAL,
    SRS_NODE_MANAGER_APPROVAL,
)
from bedo_platform.services import project_service


class FakeFrappe:
    def __init__(self, workflow, node_statuses):
        self.db = FakeDB(workflow, node_statuses)


class FakeDB:
    def __init__(self, workflow, node_statuses):
        self.workflow = workflow
        self.node_statuses = node_statuses

    def get_value(self, doctype, filters, fields, as_dict=False):
        if doctype == "SRS Workflow Instance":
            return SimpleNamespace(**self.workflow) if as_dict else None
        if doctype == "SRS Workflow Node State":
            return self.node_statuses.get(filters["node_id"])
        return None


def approval_row(approval_type):
    return SimpleNamespace(
        status="WAITING",
        approval_type=approval_type,
        workflow_instance="workflow-1",
    )


def test_srs_manager_approval_is_actionable_only_at_manager_gate(monkeypatch):
    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_MANAGER_APPROVAL, "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={SRS_NODE_MANAGER_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row("SRS_MANAGER_DEADLINE_APPROVAL")) is True


def test_stale_approval_is_not_actionable_when_workflow_has_moved(monkeypatch):
    fake_frappe = FakeFrappe(
        workflow={"current_node": "DELIVERABLES_MATRIX", "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={SRS_NODE_MANAGER_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row("SRS_MANAGER_DEADLINE_APPROVAL")) is False


def test_case_3_manager_approval_waits_for_completed_gm_approval(monkeypatch):
    manager_row = approval_row("SRS_MANAGER_DEADLINE_APPROVAL")
    workflow = {"current_node": SRS_NODE_MANAGER_APPROVAL, "case_classification": "Case 3 - Experimental Prototyping"}

    fake_frappe = FakeFrappe(
        workflow=workflow,
        node_statuses={
            SRS_NODE_MANAGER_APPROVAL: NODE_STATUS_WAITING_APPROVAL,
            SRS_NODE_GM_APPROVAL: NODE_STATUS_WAITING_APPROVAL,
        },
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(manager_row) is False

    fake_frappe = FakeFrappe(
        workflow=workflow,
        node_statuses={
            SRS_NODE_MANAGER_APPROVAL: NODE_STATUS_WAITING_APPROVAL,
            SRS_NODE_GM_APPROVAL: NODE_STATUS_COMPLETED,
        },
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(manager_row) is True
