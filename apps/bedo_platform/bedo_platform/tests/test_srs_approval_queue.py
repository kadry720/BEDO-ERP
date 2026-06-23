import sys
from types import SimpleNamespace

from bedo_platform.constants import (
    COMMAND_CENTER_SRS_ARD_GM_APPROVAL,
    GLOBAL_DEADLINE_EXTENSION_APPROVAL,
    NODE_STATUS_COMPLETED,
    NODE_STATUS_IN_PROGRESS,
    NODE_STATUS_WAITING_APPROVAL,
    SRS_NODE_BMDP,
    SRS_NODE_CASE_3,
    SRS_NODE_DUAL_GATE_APPROVAL,
    SRS_NODE_GATE_2_PMDP,
    SRS_NODE_PHYSICAL_BUILD_TEST,
    SRS_NODE_PMDP,
    SRS_NODE_PMDP_DUAL_GATE_APPROVAL,
    SUPPLIER_DEADLINE_EXTENSION_APPROVAL,
)
from bedo_platform.services import project_service


class FakeFrappe:
    def __init__(self, workflow, node_statuses, approval_rows=None, deadlines=None, handoffs=None, supplier_files=None):
        self.db = FakeDB(workflow, node_statuses, deadlines or {}, handoffs or {}, supplier_files or {})
        self.approval_rows = approval_rows or []

    def get_all(self, doctype, filters=None, fields=None, order_by=None, page_length=None):
        if doctype == "SRS Approval":
            return [SimpleNamespace(**row) for row in self.approval_rows[: page_length or len(self.approval_rows)]]
        return []


class FakeDB:
    def __init__(self, workflow, node_statuses, deadlines, handoffs, supplier_files):
        self.workflow = workflow
        self.node_statuses = node_statuses
        self.deadlines = deadlines
        self.handoffs = handoffs
        self.supplier_files = supplier_files

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
        if doctype == "BEDO Command Center Handoff":
            row = self.handoffs.get(filters)
            if not row:
                return None
            if fields == "name":
                return row.get("name")
            if fields == "status":
                return row.get("status")
            if as_dict:
                return SimpleNamespace(**{field: row.get(field) for field in fields})
            if isinstance(fields, str):
                return row.get(fields)
        if doctype == "BEDO Supplier File":
            row = self.supplier_files.get(filters)
            if not row:
                return None
            if fields == "name":
                return row.get("name")
            if fields == "status":
                return row.get("status")
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
        project="project-1",
        trainer_item="trainer-1",
        deadline="deadline-1",
        node_id=SRS_NODE_BMDP,
        command_center_handoff="handoff-1",
        supplier_file="supplier-1",
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


def test_command_center_handoff_approval_is_actionable_only_when_waiting_for_gm(monkeypatch):
    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_BMDP, "case_classification": "Case 4 - Vanguard Manufacturing"},
        node_statuses={SRS_NODE_BMDP: NODE_STATUS_COMPLETED},
        handoffs={"handoff-1": {"name": "handoff-1", "status": "WAITING_GM_APPROVAL"}},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row(COMMAND_CENTER_SRS_ARD_GM_APPROVAL)) is True

    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_BMDP, "case_classification": "Case 4 - Vanguard Manufacturing"},
        node_statuses={SRS_NODE_BMDP: NODE_STATUS_COMPLETED},
        handoffs={"handoff-1": {"name": "handoff-1", "status": "PENDING_COMMAND_CENTER"}},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row(COMMAND_CENTER_SRS_ARD_GM_APPROVAL)) is False


def test_supplier_extension_approval_is_actionable_only_when_supplier_waits(monkeypatch):
    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_BMDP, "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={},
        supplier_files={"supplier-1": {"name": "supplier-1", "status": "WAITING_EXTENSION_APPROVAL"}},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row(SUPPLIER_DEADLINE_EXTENSION_APPROVAL)) is True

    fake_frappe = FakeFrappe(
        workflow={"current_node": SRS_NODE_BMDP, "case_classification": "Case 1 - Legacy Validation"},
        node_statuses={},
        supplier_files={"supplier-1": {"name": "supplier-1", "status": "IN_PROGRESS"}},
    )
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)

    assert project_service._approval_is_actionable(approval_row(SUPPLIER_DEADLINE_EXTENSION_APPROVAL)) is False


def test_approval_department_is_inferred_from_approval_type():
    assert project_service._approval_department_for_type("GM_CASE_APPROVAL") == "SRS"
    assert project_service._approval_department_for_type(COMMAND_CENTER_SRS_ARD_GM_APPROVAL) == "Command Center"
    assert project_service._approval_department_for_type(SUPPLIER_DEADLINE_EXTENSION_APPROVAL) == "Suppliers"
    assert project_service._approval_department_for_type("ARD_INTERRUPTION_GM_APPROVAL") == "ARD"


def test_approval_display_row_includes_backfilled_department(monkeypatch):
    monkeypatch.setattr(project_service, "_user_full_name", lambda user: user or "")
    monkeypatch.setattr(project_service, "to_cairo_iso", lambda value: str(value or ""))
    monkeypatch.setattr(project_service, "deadline_unit_label", lambda: "working days")
    monkeypatch.setattr(project_service, "_node_display_label", lambda node_id: node_id)

    class FakeDB:
        def get_value(self, doctype, filters, fields, as_dict=False):
            if as_dict:
                return {}
            return ""

    fake_frappe = SimpleNamespace(db=FakeDB())
    monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
    row = SimpleNamespace(
        name="approval-1",
        approval_type=COMMAND_CENTER_SRS_ARD_GM_APPROVAL,
        approval_department="",
        status="WAITING",
        required_role="General Manager",
        workflow_instance="workflow-1",
        project="project-1",
        trainer_item="trainer-1",
        command_center_handoff="handoff-1",
        supplier_file="",
        deadline="",
        node_id="",
        assigned_to_user="commandcenter",
        original_case_classification="Case 3 - Deliver to ARD directly",
        edited_case_classification="",
        original_deadline_proposal_days=0,
        edited_deadline_proposal_days=0,
        comments="",
        creation="2026-06-23 10:00:00",
    )

    assert project_service._approval_display_row(row)["approval_department"] == "Command Center"


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
