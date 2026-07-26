"""Capture-derived storage mapping and non-dispatch planning.

This package has no USB transport dependency.  It records the smallest known
read-shaped region while keeping every live memory operation disabled.
"""
from __future__ import annotations

from .plan import (
    FeedbackRegionPlan,
    ReviewPrintRegionPlan,
    feedback_region_plan,
    review_print_region_plan,
)

__all__ = [
    "FeedbackRegionPlan",
    "ReviewPrintRegionPlan",
    "feedback_region_plan",
    "review_print_region_plan",
]
