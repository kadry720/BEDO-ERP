from pathlib import Path

from bedo_platform.services import ard_workflow_service, supplier_order_service


def test_ard_interruption_doctypes_exist():
    assert Path("apps/bedo_platform/bedo_platform/ard/doctype/ard_interruption_request/ard_interruption_request.json").exists()
    assert Path("apps/bedo_platform/bedo_platform/suppliers/doctype/bedo_supplier_order/bedo_supplier_order.json").exists()


def test_ard_interruption_service_exposes_required_entrypoints():
    assert callable(ard_workflow_service.submit_interruption_request)
    assert callable(ard_workflow_service.resolve_ard_interruption_approval)
    assert callable(ard_workflow_service.confirm_procurement_items_received)
    assert callable(ard_workflow_service.choose_electronics_subcase)
    assert callable(ard_workflow_service.complete_electronics_action)
    assert callable(ard_workflow_service.complete_concept_proof)


def test_supplier_order_service_exposes_idempotent_creation():
    assert callable(supplier_order_service.create_supplier_order_from_ard)


def test_ard_interruption_approval_is_wired_to_general_approval_resolution():
    source = Path("apps/bedo_platform/bedo_platform/services/project_service.py").read_text(encoding="utf-8")
    api_source = Path("apps/bedo_platform/bedo_platform/api/web.py").read_text(encoding="utf-8")

    assert "ARD_INTERRUPTION_GM_APPROVAL" in source
    assert "resolve_ard_interruption_approval" in source
    assert "submit_ard_interruption_request" in api_source
    assert "confirm_ard_procurement_items_received" in api_source
    assert "choose_ard_electronics_subcase" in api_source
    assert "complete_ard_electronics_action" in api_source
    assert "complete_ard_concept_proof" in api_source
