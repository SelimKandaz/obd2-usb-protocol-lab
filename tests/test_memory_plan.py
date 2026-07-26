from __future__ import annotations

import pytest

from vod700.memory import feedback_region_plan, review_print_region_plan


def test_feedback_region_plan_is_bounded_and_non_dispatchable():
    plan = feedback_region_plan(0x02000000)
    assert plan.start_address == 0x01FB0000
    assert plan.end_address_exclusive == 0x01FD0000
    assert len(plan.addresses) == 32
    assert plan.addresses[-1] == 0x01FCF000
    assert plan.dispatch_enabled is False


def test_feedback_region_plan_refuses_arbitrary_capacity():
    with pytest.raises(ValueError, match="only the captured"):
        feedback_region_plan(0x01000000)


def test_review_print_region_is_separate_static_only_tail_window():
    plan = review_print_region_plan(0x02000000)
    assert plan.start_address == 0x01FD0000
    assert plan.end_address_exclusive == 0x01FEE000
    assert len(plan.addresses) == 30
    assert plan.expected_data_signature == b"AUTOPHIX"
    assert plan.dispatch_enabled is False
