"""Unit tests for business-day calculations, holiday exclusions, and return windows."""
from datetime import date
from src.config import (
    is_business_day,
    add_business_days,
    business_days_between,
    get_return_window_days,
    get_return_deadline,
    HOLIDAYS,
)


def test_holidays_loaded():
    assert date(2026, 8, 15) in HOLIDAYS
    assert date(2026, 10, 2) in HOLIDAYS
    assert date(2026, 10, 19) in HOLIDAYS
    assert date(2026, 11, 9) in HOLIDAYS


def test_business_days():
    # 2026-10-18 is Sunday -> False
    assert not is_business_day(date(2026, 10, 18))
    # 2026-10-19 is warehouse holiday (Monday) -> False
    assert not is_business_day(date(2026, 10, 19))
    # 2026-10-20 is Tuesday -> True
    assert is_business_day(date(2026, 10, 20))
    # 2026-10-24 is Saturday -> True (Saturday is a business day)
    assert is_business_day(date(2026, 10, 24))


def test_refund_timeline_math():
    # Test Question PQ0008: card refund initiated 17 October 2026 (Saturday)
    # Timeline: 5 to 7 business days
    # Days: 18(Sun), 19(Hol), 20(B1), 21(B2), 22(B3), 23(B4), 24(B5), 25(Sun), 26(B6), 27(B7)
    start_d = date(2026, 10, 17)
    day5 = add_business_days(start_d, 5)
    day7 = add_business_days(start_d, 7)
    assert day5 == date(2026, 10, 24)
    assert day7 == date(2026, 10, 27)


def test_return_windows():
    # Standard Electronics delivered 2026-09-01 -> 7 calendar days
    assert get_return_window_days("electronics", delivered_date=date(2026, 9, 1)) == 7

    # Legacy Electronics delivered before 2026-08-01 (RET-3) -> 10 calendar days
    assert get_return_window_days("electronics", delivered_date=date(2026, 7, 20)) == 10

    # Normal Fashion -> 15 calendar days
    assert get_return_window_days("fashion", order_placed_date=date(2026, 9, 15)) == 15

    # Festive Sale Fashion placed between 01 Oct and 15 Oct 2026 (RET-8) -> 30 calendar days
    assert get_return_window_days("fashion", order_placed_date=date(2026, 10, 5)) == 30

    # Grocery -> 0 (not returnable)
    assert get_return_window_days("grocery") == 0


def test_return_deadline_calculation():
    # Delivered 2026-10-12, Fashion placed 2026-09-30 -> 15 days window -> 2026-10-27
    deliv = date(2026, 10, 12)
    placed = date(2026, 9, 30)
    deadline = get_return_deadline(deliv, "fashion", placed)
    assert deadline == date(2026, 10, 27)
