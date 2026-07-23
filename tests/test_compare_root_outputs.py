"""Tests for the Tier 1 ROOT-output comparison logic."""

import math

from scripts.compare_root_outputs import (
    calculate_relative_difference,
    close_enough,
)


def test_identical_values_agree():
    assert close_enough(
        reference=1.0,
        candidate=1.0,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )


def test_different_values_fail_exact_comparison():
    assert not close_enough(
        reference=1.0,
        candidate=1.0001,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )


def test_small_absolute_difference_can_pass():
    assert close_enough(
        reference=0.0,
        candidate=1e-12,
        relative_tolerance=0.0,
        absolute_tolerance=1e-10,
    )


def test_small_relative_difference_can_pass():
    assert close_enough(
        reference=100.0,
        candidate=100.000001,
        relative_tolerance=1e-7,
        absolute_tolerance=0.0,
    )


def test_nan_only_agrees_with_nan():
    assert close_enough(
        reference=math.nan,
        candidate=math.nan,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )

    assert not close_enough(
        reference=math.nan,
        candidate=1.0,
        relative_tolerance=0.0,
        absolute_tolerance=0.0,
    )


def test_relative_difference():
    assert calculate_relative_difference(100.0, 101.0) == 0.01


def test_relative_difference_with_two_zero_values():
    assert calculate_relative_difference(0.0, 0.0) == 0.0


def test_relative_difference_with_zero_reference():
    assert math.isinf(
        calculate_relative_difference(0.0, 1.0)
    )