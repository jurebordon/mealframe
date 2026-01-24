"""Business logic services for MealFrame application."""

from .round_robin import (
    get_meals_for_type,
    get_next_meal_for_type,
    get_round_robin_state,
    peek_next_meal_for_type,
    reset_round_robin_state,
    update_round_robin_state,
)

from .weekly import (
    generate_weekly_plan,
    get_current_week_instance,
    get_full_weekly_instance,
    get_instance_day,
    get_slots_for_instance_day,
    switch_day_template,
    set_day_override,
    clear_day_override,
    is_date_in_week,
    get_week_start_date,
)

__all__ = [
    # Round-robin
    "get_meals_for_type",
    "get_next_meal_for_type",
    "get_round_robin_state",
    "peek_next_meal_for_type",
    "reset_round_robin_state",
    "update_round_robin_state",
    # Weekly planning
    "generate_weekly_plan",
    "get_current_week_instance",
    "get_full_weekly_instance",
    "get_instance_day",
    "get_slots_for_instance_day",
    "switch_day_template",
    "set_day_override",
    "clear_day_override",
    "is_date_in_week",
    "get_week_start_date",
]
