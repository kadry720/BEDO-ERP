from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from bedo_platform.constants import (
    ALL_ROLE_NAMES,
    INITIAL_USERS,
    ROLE_DEPARTMENT_KEY,
    SRS_ELECTRONICS_SECTION_HEAD_ROLE,
    VISIBLE_BUSINESS_ROLE_NAMES,
)
from bedo_platform.services import ard_workflow_service


def test_electronics_capability_role_is_seeded_without_becoming_primary_department_role():
    assert SRS_ELECTRONICS_SECTION_HEAD_ROLE == "SRS Electronics Section Head"
    assert SRS_ELECTRONICS_SECTION_HEAD_ROLE in ALL_ROLE_NAMES
    assert SRS_ELECTRONICS_SECTION_HEAD_ROLE in VISIBLE_BUSINESS_ROLE_NAMES
    assert SRS_ELECTRONICS_SECTION_HEAD_ROLE not in ROLE_DEPARTMENT_KEY

    electronics_head = next(user for user in INITIAL_USERS if user["username"] == "srselectronicshead")
    assert "SRS Section Head" in electronics_head["roles"]
    assert SRS_ELECTRONICS_SECTION_HEAD_ROLE in electronics_head["roles"]


def test_electronics_capability_patch_is_registered():
    patches = Path("apps/bedo_platform/bedo_platform/patches.txt").read_text(encoding="utf-8")

    assert "bedo_platform.patches.ensure_srs_electronics_capability_role" in patches


def test_electronics_capability_helper_checks_exact_role(monkeypatch):
    monkeypatch.setattr(ard_workflow_service, "_roles", lambda actor: {SRS_ELECTRONICS_SECTION_HEAD_ROLE} if actor == "srselectronicshead" else {"SRS Section Head"})

    assert ard_workflow_service.is_srs_electronics_section_head("srselectronicshead") is True
    assert ard_workflow_service.is_srs_electronics_section_head("srsmechanicalhead") is False


def test_electronics_cases_queue_requires_capability_role(monkeypatch):
    class FakeFrappe:
        PermissionError = PermissionError

        @staticmethod
        def throw(message, exc):
            raise exc(message)

    monkeypatch.setitem(sys.modules, "frappe", FakeFrappe)
    monkeypatch.setattr(ard_workflow_service, "is_srs_electronics_section_head", lambda _actor: False)

    with pytest.raises(PermissionError, match="SRS Electronics Section Head"):
        ard_workflow_service.list_srs_electronics_ard_cases("srsmechanicalhead")


def test_electronics_cases_queue_filters_current_generation_node_states(monkeypatch):
    calls = []

    class FakeDb:
        @staticmethod
        def get_value(doctype, filters, fields=None, as_dict=False):
            calls.append((doctype, filters))
            if doctype == "ARD Workflow Instance":
                return SimpleNamespace(name="ARD-WF-1", project="PROJECT-1", trainer_item="TRAINER-1", current_node="ELECTRONICS_SYSTEM_DESIGN", status="ARD_IN_PROGRESS", is_superseded=0)
            if doctype == "BEDO Project":
                return {"project_code": "01/26", "project_name": "Software Lab", "end_user": "Banha University"} if as_dict else None
            if doctype == "BEDO Trainer Item":
                return {"trainer_item_name": "Website_1", "quantity": 1} if as_dict else None
            return None

    class FakeFrappe:
        db = FakeDb()

        @staticmethod
        def get_all(doctype, filters=None, fields=None, order_by=None, **_kwargs):
            assert doctype == "ARD Workflow Node State"
            assert filters["node_id"] == ard_workflow_service.ARD_NODE_ELECTRONICS_SYSTEM_DESIGN
            assert filters["is_superseded"] == 0
            assert filters["status"] == ["in", [ard_workflow_service.ARD_NODE_STATUS_READY, ard_workflow_service.ARD_NODE_STATUS_IN_PROGRESS]]
            return [
                SimpleNamespace(
                    workflow_instance="ARD-WF-1",
                    status=ard_workflow_service.ARD_NODE_STATUS_IN_PROGRESS,
                    responsible_user="srselectronicshead",
                    started_at="2026-06-21 10:00:00",
                    completed_at=None,
                    display_data='{"Electronics Subcase":"NEW_DESIGN"}',
                )
            ]

    monkeypatch.setitem(sys.modules, "frappe", FakeFrappe)
    monkeypatch.setattr(ard_workflow_service, "is_srs_electronics_section_head", lambda _actor: True)
    monkeypatch.setattr(ard_workflow_service, "to_cairo_iso", lambda value: f"CAIRO:{value}" if value else "")

    rows = ard_workflow_service.list_srs_electronics_ard_cases("srselectronicshead")

    assert rows == [
        {
            "workflow_instance": "ARD-WF-1",
            "project": "PROJECT-1",
            "project_code": "01/26",
            "project_name": "Software Lab",
            "end_user": "Banha University",
            "trainer_item": "TRAINER-1",
            "trainer_item_name": "Website_1",
            "quantity": 1,
            "ard_status": "ARD_IN_PROGRESS",
            "current_node": "ELECTRONICS_SYSTEM_DESIGN",
            "electronics_status": "IN_PROGRESS",
            "electronics_subcase": "NEW_DESIGN",
            "responsible_user": "srselectronicshead",
            "started_at": "CAIRO:2026-06-21 10:00:00",
            "completed_at": "",
        }
    ]
