from __future__ import annotations

import sys

from bedo_platform.services import deadline_service


class FakeFrappe:
    def __init__(self):
        self.calls = []

    def get_all(self, doctype, **kwargs):
        self.calls.append((doctype, kwargs))
        return []


def test_overdue_check_filters_by_due_time(monkeypatch):
    fake = FakeFrappe()
    monkeypatch.setitem(sys.modules, "frappe", fake)

    result = deadline_service.run_overdue_check()

    assert result == {"checked": 0, "sent": 0, "approvals": 0}
    doctype, kwargs = fake.calls[0]
    assert doctype == "BEDO Deadline"
    assert kwargs["filters"]["status"] == "ACTIVE"
    assert kwargs["filters"]["due_at"][0] == "<="
    assert kwargs["order_by"] == "due_at asc"


def test_reminder_check_filters_start_or_due_candidates(monkeypatch):
    fake = FakeFrappe()
    monkeypatch.setitem(sys.modules, "frappe", fake)

    result = deadline_service.run_deadline_reminder_check()

    assert result == {"checked": 0, "sent": 0}
    doctype, kwargs = fake.calls[0]
    assert doctype == "BEDO Deadline"
    assert kwargs["filters"]["status"] == "ACTIVE"
    assert kwargs["or_filters"]
    assert kwargs["order_by"] == "due_at asc"
