"""
Service layer for adherence statistics.

Calculates adherence rates, streaks, per-meal-type breakdowns,
and daily data points for the Stats view.

Adherence formula (ADR-012):
    followed / (total - equivalent - social - unmarked)

'equivalent' is neutral — excluded from both numerator and denominator.
"""
import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.models.day_template import DayTemplate
from app.models.meal_type import MealType
from app.models.weekly_plan import (
    WeeklyPlanInstance,
    WeeklyPlanInstanceDay,
    WeeklyPlanSlot,
)
from app.schemas.stats import (
    DailyAdherence,
    MealTypeAdherence,
    OverLimitBreakdown,
    StatsResponse,
    StatusBreakdown,
)

logger = logging.getLogger(__name__)


def _adherence_rate(followed: int, total: int, equivalent: int, social: int, unmarked: int) -> Decimal:
    """Calculate adherence rate per ADR-012. Returns 0 if denominator is zero.

    Formula: followed / (total - equivalent - social - unmarked)
    'equivalent' is neutral and excluded from both numerator and denominator.
    """
    denominator = total - equivalent - social - unmarked
    if denominator <= 0:
        return Decimal("0")
    rate = Decimal(followed) / Decimal(denominator)
    return rate.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _user_slots_filter(user_id: UUID):
    """Return a join condition that filters slots to a specific user's weekly plans."""
    return and_(
        WeeklyPlanSlot.weekly_plan_instance_id == WeeklyPlanInstance.id,
        WeeklyPlanInstance.user_id == user_id,
    )


async def get_stats(db: AsyncSession, days: int, user_id: UUID) -> StatsResponse:
    """
    Calculate adherence statistics for the given period, scoped to user.

    Args:
        db: Database session
        days: Number of days to look back (from today inclusive)
        user_id: UUID of the authenticated user

    Returns:
        StatsResponse with all computed stats
    """
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # Fetch all slots in the date range, scoped to user
    slots_query = (
        select(WeeklyPlanSlot)
        .join(WeeklyPlanInstance, WeeklyPlanSlot.weekly_plan_instance_id == WeeklyPlanInstance.id)
        .where(
            and_(
                WeeklyPlanSlot.date >= start_date,
                WeeklyPlanSlot.date <= today,
                WeeklyPlanInstance.user_id == user_id,
            )
        )
        .order_by(WeeklyPlanSlot.date, WeeklyPlanSlot.position)
    )
    result = await db.execute(slots_query)
    slots = result.scalars().all()

    # Fetch override days in range, scoped to user
    override_query = (
        select(func.count())
        .select_from(WeeklyPlanInstanceDay)
        .join(WeeklyPlanInstance, WeeklyPlanInstanceDay.weekly_plan_instance_id == WeeklyPlanInstance.id)
        .where(
            and_(
                WeeklyPlanInstanceDay.date >= start_date,
                WeeklyPlanInstanceDay.date <= today,
                WeeklyPlanInstanceDay.is_override.is_(True),
                WeeklyPlanInstance.user_id == user_id,
            )
        )
    )
    override_result = await db.execute(override_query)
    override_days = override_result.scalar() or 0

    # Build status breakdown
    status_counts: dict[str | None, int] = defaultdict(int)
    for slot in slots:
        status_counts[slot.completion_status] += 1

    followed = status_counts.get("followed", 0)
    equivalent = status_counts.get("equivalent", 0)
    skipped = status_counts.get("skipped", 0)
    deviated = status_counts.get("deviated", 0)
    social = status_counts.get("social", 0)
    unmarked = status_counts.get(None, 0)

    total_slots = len(slots)
    completed_slots = total_slots - unmarked

    by_status = StatusBreakdown(
        followed=followed,
        equivalent=equivalent,
        skipped=skipped,
        deviated=deviated,
        social=social,
        unmarked=unmarked,
    )

    adherence_rate = _adherence_rate(followed, total_slots, equivalent, social, unmarked)

    # Calculate streaks
    current_streak, best_streak = await _calculate_streaks(db, today, user_id)

    # Per-meal-type breakdown
    by_meal_type = await _calculate_meal_type_adherence(db, start_date, today, user_id)

    # Daily adherence data points
    daily_adherence = _calculate_daily_adherence(slots, start_date, today)

    # Average daily macros
    avg_cal, avg_pro = await _calculate_avg_daily_macros(db, start_date, today, user_id)

    # Over-limit stats
    over_limit_days, days_with_limits, over_limit_breakdown = await _calculate_over_limit_stats(
        db, start_date, today, user_id
    )

    return StatsResponse(
        period_days=days,
        total_slots=total_slots,
        completed_slots=completed_slots,
        by_status=by_status,
        adherence_rate=adherence_rate,
        current_streak=current_streak,
        best_streak=best_streak,
        override_days=override_days,
        by_meal_type=by_meal_type,
        daily_adherence=daily_adherence,
        avg_daily_calories=avg_cal,
        avg_daily_protein=avg_pro,
        over_limit_days=over_limit_days,
        days_with_limits=days_with_limits,
        over_limit_breakdown=over_limit_breakdown,
    )


async def _calculate_streaks(db: AsyncSession, today: date, user_id: UUID) -> tuple[int, int]:
    """
    Calculate current and best streaks, scoped to user.

    A streak day = a day where ALL slots have a completion status
    (i.e. no unmarked slots). The streak breaks on any day with unmarked slots
    or any day with no slots at all.

    We look back up to 365 days for best streak, and count backwards
    from today for current streak.
    """
    lookback_start = today - timedelta(days=364)

    # Get per-day counts of total slots and unmarked slots, scoped to user
    day_stats_query = (
        select(
            WeeklyPlanSlot.date,
            func.count().label("total"),
            func.count().filter(WeeklyPlanSlot.completion_status.is_(None)).label("unmarked"),
        )
        .join(WeeklyPlanInstance, WeeklyPlanSlot.weekly_plan_instance_id == WeeklyPlanInstance.id)
        .where(
            and_(
                WeeklyPlanSlot.date >= lookback_start,
                WeeklyPlanSlot.date <= today,
                WeeklyPlanInstance.user_id == user_id,
            )
        )
        .group_by(WeeklyPlanSlot.date)
        .order_by(WeeklyPlanSlot.date)
    )
    result = await db.execute(day_stats_query)
    rows = result.all()

    # Build a dict: date -> (total, unmarked)
    day_map: dict[date, tuple[int, int]] = {}
    for row in rows:
        day_map[row.date] = (row.total, row.unmarked)

    # Calculate best streak across all days
    best_streak = 0
    current_run = 0
    for row in rows:
        if row.total > 0 and row.unmarked == 0:
            current_run += 1
            best_streak = max(best_streak, current_run)
        else:
            current_run = 0

    # Calculate current streak (backwards from yesterday — today is still in progress)
    current_streak = 0
    d = today - timedelta(days=1)
    while d >= lookback_start:
        if d in day_map:
            total, unmarked_count = day_map[d]
            if total > 0 and unmarked_count == 0:
                current_streak += 1
            else:
                break
        else:
            # No slots for this day — streak breaks
            break
        d -= timedelta(days=1)

    return current_streak, best_streak


async def _calculate_meal_type_adherence(
    db: AsyncSession, start_date: date, end_date: date, user_id: UUID,
) -> list[MealTypeAdherence]:
    """
    Calculate per-meal-type adherence, sorted by lowest adherence first.
    Scoped to user.
    """
    # Get meal type names for this user
    mt_query = select(MealType.id, MealType.name).where(MealType.user_id == user_id)
    mt_result = await db.execute(mt_query)
    meal_type_names: dict[UUID, str] = {row.id: row.name for row in mt_result.all()}

    # Get per-type stats, scoped to user
    type_stats_query = (
        select(
            WeeklyPlanSlot.meal_type_id,
            func.count().label("total"),
            func.count().filter(WeeklyPlanSlot.completion_status == "followed").label("followed_count"),
            func.count().filter(WeeklyPlanSlot.completion_status == "equivalent").label("equivalent_count"),
            func.count().filter(WeeklyPlanSlot.completion_status == "social").label("social_count"),
            func.count().filter(WeeklyPlanSlot.completion_status.is_(None)).label("unmarked_count"),
        )
        .join(WeeklyPlanInstance, WeeklyPlanSlot.weekly_plan_instance_id == WeeklyPlanInstance.id)
        .where(
            and_(
                WeeklyPlanSlot.date >= start_date,
                WeeklyPlanSlot.date <= end_date,
                WeeklyPlanSlot.meal_type_id.isnot(None),
                WeeklyPlanInstance.user_id == user_id,
            )
        )
        .group_by(WeeklyPlanSlot.meal_type_id)
    )
    result = await db.execute(type_stats_query)
    rows = result.all()

    adherence_list: list[MealTypeAdherence] = []
    for row in rows:
        mt_id = row.meal_type_id
        name = meal_type_names.get(mt_id, "Unknown")
        rate = _adherence_rate(
            row.followed_count, row.total, row.equivalent_count, row.social_count, row.unmarked_count
        )
        adherence_list.append(
            MealTypeAdherence(
                meal_type_id=mt_id,
                name=name,
                total=row.total,
                followed=row.followed_count,
                adherence_rate=rate,
            )
        )

    # Sort by lowest adherence first
    adherence_list.sort(key=lambda x: x.adherence_rate)
    return adherence_list


async def _calculate_avg_daily_macros(
    db: AsyncSession, start_date: date, end_date: date, user_id: UUID,
) -> tuple[Decimal | None, Decimal | None]:
    """Calculate average daily calories and protein across days with data, scoped to user."""
    slots_query = (
        select(WeeklyPlanSlot)
        .join(WeeklyPlanInstance, WeeklyPlanSlot.weekly_plan_instance_id == WeeklyPlanInstance.id)
        .where(
            and_(
                WeeklyPlanSlot.date >= start_date,
                WeeklyPlanSlot.date <= end_date,
                WeeklyPlanInstance.user_id == user_id,
            )
        )
        .options(selectinload(WeeklyPlanSlot.meal))
    )
    result = await db.execute(slots_query)
    slots_with_meals = result.scalars().all()

    daily_totals: dict[date, dict] = defaultdict(
        lambda: {"calories": Decimal(0), "protein": Decimal(0), "has_data": False}
    )
    for slot in slots_with_meals:
        if slot.meal:
            day = daily_totals[slot.date]
            if slot.meal.calories_kcal is not None:
                day["calories"] += Decimal(slot.meal.calories_kcal)
                day["has_data"] = True
            if slot.meal.protein_g is not None:
                day["protein"] += slot.meal.protein_g
                day["has_data"] = True

    days_with_data = [d for d in daily_totals.values() if d["has_data"]]
    if not days_with_data:
        return None, None

    n = Decimal(len(days_with_data))
    avg_cal = (sum(d["calories"] for d in days_with_data) / n).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    avg_pro = (sum(d["protein"] for d in days_with_data) / n).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )

    return avg_cal, avg_pro


def _calculate_daily_adherence(
    slots: list, start_date: date, end_date: date
) -> list[DailyAdherence]:
    """
    Build per-day adherence data points for chart display.

    Only includes days that have slots (no empty days generated).
    """
    # Group slots by date
    by_date: dict[date, list] = defaultdict(list)
    for slot in slots:
        by_date[slot.date].append(slot)

    daily: list[DailyAdherence] = []
    d = start_date
    while d <= end_date:
        day_slots = by_date.get(d)
        if day_slots:
            total = len(day_slots)
            followed_count = sum(
                1 for s in day_slots if s.completion_status == "followed"
            )
            equivalent_count = sum(
                1 for s in day_slots if s.completion_status == "equivalent"
            )
            social_count = sum(
                1 for s in day_slots if s.completion_status == "social"
            )
            unmarked_count = sum(
                1 for s in day_slots if s.completion_status is None
            )
            rate = _adherence_rate(followed_count, total, equivalent_count, social_count, unmarked_count)
            daily.append(
                DailyAdherence(
                    date=d,
                    total=total,
                    followed=followed_count,
                    adherence_rate=rate,
                )
            )
        d += timedelta(days=1)

    return daily


async def _calculate_over_limit_stats(
    db: AsyncSession, start_date: date, end_date: date, user_id: UUID,
) -> tuple[int, int, list[OverLimitBreakdown]]:
    """
    Calculate over-limit statistics for days with template soft limits, scoped to user.

    For each day that has a template with max_calories_kcal or max_protein_g set,
    sum the actual meal macros and compare against the limits.

    Returns:
        (over_limit_days, days_with_limits, breakdown_list)
    """
    # Get instance days in range that have a template with limits, scoped to user
    days_query = (
        select(WeeklyPlanInstanceDay)
        .join(WeeklyPlanInstance, WeeklyPlanInstanceDay.weekly_plan_instance_id == WeeklyPlanInstance.id)
        .join(DayTemplate, WeeklyPlanInstanceDay.day_template_id == DayTemplate.id)
        .where(
            and_(
                WeeklyPlanInstanceDay.date >= start_date,
                WeeklyPlanInstanceDay.date <= end_date,
                WeeklyPlanInstanceDay.is_override.is_(False),
                WeeklyPlanInstance.user_id == user_id,
                # At least one limit is set
                (DayTemplate.max_calories_kcal.isnot(None))
                | (DayTemplate.max_protein_g.isnot(None)),
            )
        )
        .options(selectinload(WeeklyPlanInstanceDay.day_template))
    )
    result = await db.execute(days_query)
    instance_days = result.scalars().all()

    if not instance_days:
        return 0, 0, []

    # Get all slots for these dates with their meals
    dates_with_limits = [d.date for d in instance_days]
    slots_query = (
        select(WeeklyPlanSlot)
        .join(WeeklyPlanInstance, WeeklyPlanSlot.weekly_plan_instance_id == WeeklyPlanInstance.id)
        .where(
            WeeklyPlanSlot.date.in_(dates_with_limits),
            WeeklyPlanInstance.user_id == user_id,
        )
        .options(selectinload(WeeklyPlanSlot.meal))
    )
    slots_result = await db.execute(slots_query)
    all_slots = slots_result.scalars().all()

    # Sum macros per date
    daily_totals: dict[date, dict[str, Decimal]] = defaultdict(
        lambda: {"calories": Decimal(0), "protein": Decimal(0)}
    )
    for slot in all_slots:
        if slot.meal:
            day = daily_totals[slot.date]
            if slot.meal.calories_kcal is not None:
                day["calories"] += Decimal(slot.meal.calories_kcal)
            if slot.meal.protein_g is not None:
                day["protein"] += slot.meal.protein_g

    # Compare against limits, tracking per-template stats
    # Key: template name -> {days_over, total_days, cal_over, pro_over}
    template_stats: dict[str, dict] = defaultdict(
        lambda: {"days_over": 0, "total_days": 0, "cal_over": False, "pro_over": False}
    )
    over_limit_days_set: set[date] = set()

    for instance_day in instance_days:
        template = instance_day.day_template
        tname = template.name
        template_stats[tname]["total_days"] += 1

        totals = daily_totals.get(instance_day.date)
        if not totals:
            continue

        cal_over = (
            template.max_calories_kcal is not None
            and totals["calories"] > Decimal(template.max_calories_kcal)
        )
        pro_over = (
            template.max_protein_g is not None
            and totals["protein"] > template.max_protein_g
        )

        if cal_over or pro_over:
            over_limit_days_set.add(instance_day.date)
            template_stats[tname]["days_over"] += 1
            if cal_over:
                template_stats[tname]["cal_over"] = True
            if pro_over:
                template_stats[tname]["pro_over"] = True

    # Build breakdown list
    breakdown: list[OverLimitBreakdown] = []
    for tname, stats in template_stats.items():
        if stats["days_over"] > 0:
            if stats["cal_over"] and stats["pro_over"]:
                exceeded = "both"
            elif stats["cal_over"]:
                exceeded = "calories"
            else:
                exceeded = "protein"
            breakdown.append(
                OverLimitBreakdown(
                    template_name=tname,
                    days_over=stats["days_over"],
                    total_days=stats["total_days"],
                    exceeded_metric=exceeded,
                )
            )

    # Sort by most over-limit days first
    breakdown.sort(key=lambda x: x.days_over, reverse=True)

    return len(over_limit_days_set), len(instance_days), breakdown
