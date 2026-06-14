import sys
from types import SimpleNamespace

from bedo_platform.constants import (
    GLOBAL_DEADLINE_EXTENSION_APPROVAL,
    NODE_STATUS_COMPLETED,
    NODE_STATUS_IN_PROGRESS,
    NODE_STATUS_WAITING_APPROVAL,
    SRS_NODE_BMDP,
    SRS_NODE_CASE_3,
    SRS_NODE_COMMAND_CENTER_APPROVAL,
    SRS_NODE_DUAL_GATE_APPROVAL,
    SRS_NODE_FINAL_GM_APPROVAL,
    SRS_NODE_GATE_2_PMDP,
    SRS_NODE_PHYSICAL_BUILD_TEST,
    SRS_NODE_PMDP,
    SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
)
from bedo_platform.services import project_service


class FakeFrappe:
    def __init__(self, workflow, node_statuses, approval_rows=None, deadlines=None):
        self.db = FakeDB(workflow, node_statuses, deadlines or {})
        self.approval_rows = approval_rows or []

    def get_all(self, doctype, filters=None, fields=None, order_by=None, page_length=None):
        if doctype == "SRS Approval":
            return [SimpleNamespace(**row) for row in self.approval_rows[: page_length or len(self.approval_rows)]]
        return []


class FakeDB:
    def __init__(self, workflow, node_statuses, deadlines):
        self.workflow = workflow
        self.node_statuses = node_statuses
        self.deadlines = deadlines

    def get_value(self, doctype, filters, fields, as_dict=False):
        if doctype == "SRS Workflow Instance":
            if as_dict:
                return SimpleNamespace(**self.workflow)
            if isinstance(fields, str):
                return self.workflow.get(fields)
            return None
        if doctype == "SRS Workflow Node State":
            return self.node_statuses.get(filters["node_id"])
        if doctype == "BEDO Deadline":
            row = self.deadlines.get(filters)
            if not row:
                return None
            if as_dict:
                return SimpleNamespace(**{field: row.get(field) for field in fields})
            if isinstance(fields, str):
                return row.get(fields)
        return None


def approval_row(approval_type):
    return SimpleNamespace(
        status="WAITING",
        approval_type=approval_type,
        workflow_instance="workflow-1",
        deadline="deadline-1",
        node_id=SRS_NODE_BMDP,
    )


def test_srs_manager_approval_is_actionable_only_at_dual_gate(monkeypatch):
    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_DUAL_GATE_APPROVAL, "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={SRS_NODE_DUAL_GATE_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row("SRS_MANAGER_DEADLINE_APPROVAL")) is True


def test_stale_approval_is_not_actionable_when_workflow_has_moved(monkeypatch):
    fake_frappe = FakeFrappe(
        workflow={"current_node": "DELIVERABLES_MATRIX", "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={SRS_NODE_DUAL_GATE_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row("SRS_MANAGER_DEADLINE_APPROVAL")) is False


def test_gm_dual_gate_approval_waits_for_srs_manager_decision(monkeypatch):
    gm_row = approval_row("GM_CASE_APPROVAL")
    workflow = {"current_node": SRS_NODE_DUAL_GATE_APPROVAL, "case_classification": "Case 3 - Experimental Prototyping"}

    fake_frappe = FakeFrappe(
        workflow=workflow,
        node_statuses={SRS_NODE_DUAL_GATE_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(gm_row) is False

    fake_frappe = FakeFrappe(
        workflow={**workflow, "srs_manager_approved_at": "2026-06-11 10:00:00"},
        node_statuses={SRS_NODE_DUAL_GATE_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(gm_row) is True


def test_pmdp_gm_dual_gate_approval_waits_for_srs_pmdp_approval(monkeypatch):
    gm_row = approval_row("PMDP_DUAL_GATE_GM_APPROVAL")
    workflow = {"current_node": SRS_NODE_PMDP_DUAL_GATE_APPROVAL, "case_classification": "Case 3 - Experimental Prototyping"}

    fake_frappe = FakeFrappe(
        workflow=workflow,
        node_statuses={SRS_NODE_PMDP_DUAL_GATE_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
        approval_rows=[{"status": "WAITING"}],
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(gm_row) is False

    fake_frappe = FakeFrappe(
        workflow=workflow,
        node_statuses={SRS_NODE_PMDP_DUAL_GATE_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
        approval_rows=[{"status": "APPROVED"}],
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(gm_row) is True


def test_command_center_gm_approval_is_actionable_only_at_final_gm_node(monkeypatch):
    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_FINAL_GM_APPROVAL, "case_classification": "Case 4 - Vanguard Manufacturing"},
        node_statuses={SRS_NODE_FINAL_GM_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row("COMMAND_CENTER_GM_APPROVAL")) is True

    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_COMMAND_CENTER_APPROVAL, "case_classification": "Case 4 - Vanguard Manufacturing"},
        node_statuses={SRS_NODE_FINAL_GM_APPROVAL: NODE_STATUS_WAITING_APPROVAL},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row("COMMAND_CENTER_GM_APPROVAL")) is False


def test_global_deadline_extension_is_actionable_only_for_overdue_live_node(monkeypatch):
    row = approval_row(GLOBAL_DEADLINE_EXTENSION_APPROVAL)
    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_BMDP, "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={SRS_NODE_BMDP: "IN_PROGRESS"},
        deadlines={"deadline-1": {"status": "OVERDUE", "node_id": SRS_NODE_BMDP}},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(row) is True

    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_BMDP, "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={SRS_NODE_BMDP: NODE_STATUS_COMPLETED},
        deadlines={"deadline-1": {"status": "OVERDUE", "node_id": SRS_NODE_BMDP}},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(row) is False

    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_BMDP, "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={SRS_NODE_BMDP: "IN_PROGRESS"},
        deadlines={"deadline-1": {"status": "ACTIVE", "node_id": SRS_NODE_BMDP}},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    assert project_service._approval_is_actionable(row) is False


def test_case_3_gate_2_pmdp_is_available_while_case_3_remains_in_progress(monkeypatch):
    workflow = SimpleNamespace(
        name="workflow-1",
        project_owner="owner",
        case_classification=project_service.CASE_3,
        current_node=SRS_NODE_GATE_2_PMDP,
        pmdp_gate_path="",
        pmdp_path="",
        bmdp_path="",
    )
    statuses = {SRS_NODE_CASE_3: NODE_STATUS_IN_PROGRESS, SRS_NODE_GATE_2_PMDP: NODE_STATUS_IN_PROGRESS}
    monkeypatch.setattr(project_service, "_node_status", lambda _workflow, node_id: statuses.get(node_id, "LOCKED"))

    assert project_service._node_disabled_reason("owner", workflow, SRS_NODE_GATE_2_PMDP) == ""


def test_case_3_pmdp_is_available_while_physical_build_remains_in_progress(monkeypatch):
    workflow = SimpleNamespace(
        name="workflow-1",
        project_owner="owner",
        case_classification=project_service.CASE_3,
        current_node=SRS_NODE_PMDP,
        pmdp_gate_path="path/to/gate2.pdf",
        pmdp_path="",
        bmdp_path="",
    )
    statuses = {
        SRS_NODE_PHYSICAL_BUILD_TEST: NODE_STATUS_IN_PROGRESS,
        SRS_NODE_PMDP: NODE_STATUS_IN_PROGRESS,
    }
    monkeypatch.setattr(project_service, "_node_status", lambda _workflow, node_id: statuses.get(node_id, NODE_STATUS_COMPLETED))

    assert project_service._node_disabled_reason("owner", workflow, SRS_NODE_PMDP) == ""
