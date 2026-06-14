from datetime import datetime
from zoneinfo import ZoneInfo

from bedo_platform.services.deadline_service import calculate_next_working_start, calculate_working_due_at

CAIRO = ZoneInfo("Africa/Cairo")


def test_sunday_action_starts_monday_9am():
    start = calculate_next_working_start(datetime(2026, 6, 7, 10, 0, tzinfo=CAIRO))

    assert start == datetime(2026, 6, 8, 9, 0, tzinfo=CAIRO)


def test_thursday_action_starts_next_sunday_9am():
    start = calculate_next_working_start(datetime(2026, 6, 11, 16, 0, tzinfo=CAIRO))

    assert start == datetime(2026, 6, 14, 9, 0, tzinfo=CAIRO)


def test_friday_action_starts_next_sunday_9am():
    start = calculate_next_working_start(datetime(2026, 6, 12, 12, 0, tzinfo=CAIRO))

    assert start == datetime(2026, 6, 14, 9, 0, tzinfo=CAIRO)


def test_one_working_day_due_same_day_5pm():
    start = datetime(2026, 6, 8, 9, 0, tzinfo=CAIRO)

    assert calculate_working_due_at(start, 1) == datetime(2026, 6, 8, 17, 0, tzinfo=CAIRO)


def test_two_working_days_due_second_working_day_5pm():
    start = datetime(2026, 6, 11, 9, 0, tzinfo=CAIRO)

    assert calculate_working_due_at(start, 2) == datetime(2026, 6, 14, 17, 0, tzinfo=CAIRO)
