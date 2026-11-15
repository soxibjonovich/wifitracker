from datetime import date

import pytest

from wifitracker import limits

MAC = "AA:BB:CC:DD:EE:FF"
DAY1 = date(2026, 11, 15)
DAY2 = date(2026, 11, 16)


def test_set_and_remove_limit():
    limits.set_limit("aa-bb-cc-dd-ee-ff", 2, "tablet")
    assert limits.get_limits() == {MAC: {"hours": 2, "name": "tablet"}}
    assert limits.remove_limit(MAC) is True
    assert limits.remove_limit(MAC) is False


def test_negative_hours_rejected():
    with pytest.raises(ValueError):
        limits.set_limit(MAC, -1)


def test_usage_counts_only_limited_active_devices():
    limits.set_limit(MAC, 1)
    limits.record_usage([MAC, "11:22:33:44:55:66"], 600, DAY1)
    assert limits.used_seconds(MAC, DAY1) == 600
    assert limits.used_seconds("11:22:33:44:55:66", DAY1) == 0


def test_block_once_limit_used_up():
    limits.set_limit(MAC, 1)
    assert limits.record_usage([MAC], 3599, DAY1) == ([], [])
    assert limits.record_usage([MAC], 1, DAY1) == ([MAC], [])


def test_not_blocked_again_once_marked():
    limits.set_limit(MAC, 0.5)
    to_block, _ = limits.record_usage([MAC], 1800, DAY1)
    limits.mark_blocked(to_block[0], DAY1)
    assert limits.record_usage([], 30, DAY1) == ([], [])


def test_failed_block_is_retried():
    limits.set_limit(MAC, 0.5)
    limits.record_usage([MAC], 1800, DAY1)
    # Router call failed, so mark_blocked was never called.
    assert limits.record_usage([], 30, DAY1) == ([MAC], [])


def test_new_day_resets_usage_and_unblocks():
    limits.set_limit(MAC, 1)
    limits.record_usage([MAC], 3600, DAY1)
    limits.mark_blocked(MAC, DAY1)
    assert limits.record_usage([], 30, DAY2) == ([], [MAC])
    assert limits.used_seconds(MAC, DAY2) == 0
    limits.mark_unblocked(MAC, DAY2)
    assert limits.get_usage(DAY2)["blocked"] == []


def test_raising_or_removing_limit_unblocks():
    limits.set_limit(MAC, 1)
    limits.record_usage([MAC], 3600, DAY1)
    limits.mark_blocked(MAC, DAY1)
    limits.set_limit(MAC, 2)
    assert limits.record_usage([], 30, DAY1) == ([], [MAC])
    limits.remove_limit(MAC)
    assert limits.record_usage([], 30, DAY1) == ([], [MAC])


def test_zero_hours_blocks_right_away():
    limits.set_limit(MAC, 0)
    assert limits.record_usage([], 0, DAY1) == ([MAC], [])
