"""Business logic services for MealFrame application."""

from .round_robin import (
    get_meals_for_type,
    get_next_meal_for_type,
    get_round_robin_state,
    peek_next_meal_for_type,
    reset_round_robin_state,
    update_round_robin_state,
)

from .meals import (
    create_meal,
    delete_meal,
    get_meal_by_id,
    import_meals_from_csv,
    list_meals,
    update_meal,
)

from .weekly import (
    generate_weekly_plan,
    regenerate_weekly_plan,
    get_current_week_instance,
    get_week_instance,
    get_full_weekly_instance,
    get_instance_day,
    get_slots_for_instance_day,
    switch_day_template,
    set_day_override,
    clear_day_override,
    is_date_in_week,
    get_week_start_date,
)

from .meal_types import (
    create_meal_type,
    delete_meal_type,
    get_meal_type_by_id,
    list_meal_types,
    update_meal_type,
)

from .day_templates import (
    create_day_template,
    delete_day_template,
    get_day_template_by_id,
    list_day_templates,
    update_day_template,
)

from .week_plans import (
    create_week_plan,
    delete_week_plan,
    get_week_plan_by_id,
    list_week_plans,
    set_default_week_plan,
    update_week_plan,
)

from .stats import get_stats

from .analytics import record_pageview

from .auth import (
    authenticate_user,
    get_user_by_id,
    issue_tokens,
    refresh_tokens,
    register_user,
    revoke_all_user_tokens,
    revoke_refresh_token,
)

__all__ = [
    # Meals
    "create_meal",
    "delete_meal",
    "get_meal_by_id",
    "import_meals_from_csv",
    "list_meals",
    "update_meal",
    # Round-robin
    "get_meals_for_type",
    "get_next_meal_for_type",
    "get_round_robin_state",
    "peek_next_meal_for_type",
    "reset_round_robin_state",
    "update_round_robin_state",
    # Weekly planning
    "generate_weekly_plan",
    "regenerate_weekly_plan",
    "get_current_week_instance",
    "get_week_instance",
    "get_full_weekly_instance",
    "get_instance_day",
    "get_slots_for_instance_day",
    "switch_day_template",
    "set_day_override",
    "clear_day_override",
    "is_date_in_week",
    "get_week_start_date",
    # Meal types
    "create_meal_type",
    "delete_meal_type",
    "get_meal_type_by_id",
    "list_meal_types",
    "update_meal_type",
    # Day templates
    "create_day_template",
    "delete_day_template",
    "get_day_template_by_id",
    "list_day_templates",
    "update_day_template",
    # Week plans
    "create_week_plan",
    "delete_week_plan",
    "get_week_plan_by_id",
    "list_week_plans",
    "set_default_week_plan",
    "update_week_plan",
    # Stats
    "get_stats",
    # Analytics
    "record_pageview",
    # Auth
    "authenticate_user",
    "get_user_by_id",
    "issue_tokens",
    "refresh_tokens",
    "register_user",
    "revoke_all_user_tokens",
    "revoke_refresh_token",
]
