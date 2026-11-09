import pytest
from app.services.gamification.engine import calculate_xp, get_level_from_xp


def test_base_xp():
    """Verify base XP for easy, medium, and hard without streak/speed bonus."""
    assert calculate_xp("easy", streak=0, response_ms=20000, time_limit_ms=30000) == 10
    assert calculate_xp("medium", streak=0, response_ms=20000, time_limit_ms=30000) == 20
    assert calculate_xp("hard", streak=0, response_ms=20000, time_limit_ms=30000) == 35


def test_xp_streak_multiplier():
    """Verify streak multiplier: up to 10 * 10% = +100%."""
    # 5 streak: 1 + 0.5 = 1.5x -> 20 * 1.5 = 30
    xp_5 = calculate_xp("medium", streak=5, response_ms=20000, time_limit_ms=30000)
    assert xp_5 == 30

    # 10 streak: 1 + 1.0 = 2.0x -> 20 * 2.0 = 40
    xp_10 = calculate_xp("medium", streak=10, response_ms=20000, time_limit_ms=30000)
    assert xp_10 == 40

    # >10 streak caps at 2.0x
    xp_15 = calculate_xp("medium", streak=15, response_ms=20000, time_limit_ms=30000)
    assert xp_15 == 40


def test_xp_speed_bonus():
    """Verify speed bonus: +25% when answered in < 40% of time limit."""
    # Time ratio: 5000 / 30000 = 0.166 < 0.4 -> +25%
    # Easy base 10 * 1.0 * 1.25 = 12
    xp_fast = calculate_xp("easy", streak=0, response_ms=5000, time_limit_ms=30000)
    assert xp_fast == 12

    # Medium base 20 * 1.0 * 1.25 = 25
    xp_med_fast = calculate_xp("medium", streak=0, response_ms=8000, time_limit_ms=30000)
    assert xp_med_fast == 25


def test_level_calculation():
    """Verify level threshold progression: Level n requires 100 * n^1.5 XP."""
    # Level 1 requires 100 XP to advance
    assert get_level_from_xp(0) == 1
    assert get_level_from_xp(99) == 1
    # Level 2 reached at 100 XP
    assert get_level_from_xp(100) == 2
    # Level 3 reached at 100 + 100*2^1.5 = 100 + 282 = 382 XP
    assert get_level_from_xp(385) >= 3
