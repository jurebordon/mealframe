"""
Service layer for adherence statistics.

Calculates adherence rates, streaks, per-meal-type breakdowns,
and daily data points for the Stats view.

Adherence formula (from Tech Spec section 4.3):
    (followed + adjusted) / (total - social - unmarked)
"""
import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal_type import MealType
from app.models.weekly_plan import (
    WeeklyPlanInstance,
    WeeklyPlanInstanceDay,
    WeeklyPlanSlot,
)
from app.schemas.stats import (
    DailyAdherence,
    MealTypeAdherence,
    StatsResponse,
    StatusBreakdown,
)

logger = logging.getLogger(__name__)


def _adherence_rate(followed: int, adjusted: int, total: int, social: int, unmarked: int) -> Decimal:
    """Calculate adherence rate. Returns 0 if denominator is zero."""
    denominator = total - social - unmarked
    if denominator <= 0:
        return Decimal("0")
    rate = Decimal(followed + adjusted) / Decimal(denominator)
    return rate.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


async def get_stats(db: AsyncSession, days: int) -> StatsResponse:
    """
    Calculate adherence statistics for the given period.

    Args:
        db: Database session
        days: Number of days to look back (from today inclusive)

    Returns:
        StatsResponse with all computed stats
    """
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # Fetch all slots in the date range
    slots_query = (
        select(WeeklyPlanSlot)
        .where(
            and_(
                WeeklyPlanSlot.date >= start_date,
                WeeklyPlanSlot.date <= today,
            )
        )
        .order_by(WeeklyPlanSlot.date, WeeklyPlanSlot.position)
    )
    result = await db.execute(slots_query)
    slots = result.scalars().all()

    # Fetch override days in range
    override_query = (
        select(func.count())
        .select_from(WeeklyPlanInstanceDay)
        .where(
            and_(
                WeeklyPlanInstanceDay.date >= start_date,
                WeeklyPlanInstanceDay.date <= today,
                WeeklyPlanInstanceDay.is_override.is_(True),
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
    adjusted = status_counts.get("adjusted", 0)
    skipped = status_counts.get("skipped", 0)
    replaced = status_counts.get("replaced", 0)
    social = status_counts.get("social", 0)
    unmarked = status_counts.get(None, 0)

    total_slots = len(slots)
    completed_slots = total_slots - unmarked

    by_status = StatusBreakdown(
        followed=followed,
        adjusted=adjusted,
        skipped=skipped,
        replaced=replaced,
        social=social,
        unmarked=unmarked,
    )

    adherence_rate = _adherence_rate(followed, adjusted, total_slots, social, unmarked)

    # Calculate streaks
    current_streak, best_streak = await _calculate_streaks(db, today)

    # Per-meal-type breakdown
    by_meal_type = await _calculate_meal_type_adherence(db, start_date, today)

    # Daily adherence data points
    daily_adherence = _calculate_daily_adherence(slots, start_date, today)

    # Average daily macros
    avg_cal, avg_pro = await _calculate_avg_daily_macros(db, start_date, today)

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
    )


async def _calculate_streaks(db: AsyncSession, today: date) -> tuple[int, int]:
    """
    Calculate current and best streaks.

    A streak day = a day where ALL slots have a completion status
    (i.e. no unmarked slots). The streak breaks on any day with unmarked slots
    or any day with no slots at all.

    We look back up to 365 days for best streak, and count backwards
    from today for current streak.
    """
    lookback_start = today - timedelta(days=364)

    # Get per-day counts of total slots and unmarked slots
    day_stats_query = (
        select(
            WeeklyPlanSlot.date,
            func.count().label("total"),
            func.count().filter(WeeklyPlanSlot.completion_status.is_(None)).label("unmarked"),
        )
        .where(
            and_(
                WeeklyPlanSlot.date >= lookback_start,
                WeeklyPlanSlot.date <= today,
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
    db: AsyncSession, start_date: date, end_date: date
) -> list[MealTypeAdherence]:
    """
    Calculate per-meal-type adherence, sorted by lowest adherence first.
    """
    # Get meal type names
    mt_query = select(MealType.id, MealType.name)
    mt_result = await db.execute(mt_query)
    meal_type_names: dict[UUID, str] = {row.id: row.name for row in mt_result.all()}

    # Get per-type stats
    type_stats_query = (
        select(
            WeeklyPlanSlot.meal_type_id,
            func.count().label("total"),
            func.count().filter(WeeklyPlanSlot.completion_status == "followed").label("followed_count"),
            func.count().filter(WeeklyPlanSlot.completion_status == "adjusted").label("adjusted_count"),
            func.count().filter(WeeklyPlanSlot.completion_status == "social").label("social_count"),
            func.count().filter(WeeklyPlanSlot.completion_status.is_(None)).label("unmarked_count"),
        )
        .where(
            and_(
                WeeklyPlanSlot.date >= start_date,
                WeeklyPlanSlot.date <= end_date,
                WeeklyPlanSlot.meal_type_id.isnot(None),
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
            row.followed_count, row.adjusted_count, row.total, row.social_count, row.unmarked_count
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
    db: AsyncSession, start_date: date, end_date: date
) -> tuple[Decimal | None, Decimal | None]:
    """Calculate average daily calories and protein across days with data."""
    from sqlalchemy.orm import selectinload

    slots_query = (
        select(WeeklyPlanSlot)
        .where(
            and_(
                WeeklyPlanSlot.date >= start_date,
                WeeklyPlanSlot.date <= end_date,
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
                1 for s in day_slots if s.completion_status in ("followed", "adjusted")
            )
            social_count = sum(
                1 for s in day_slots if s.completion_status == "social"
            )
            unmarked_count = sum(
                1 for s in day_slots if s.completion_status is None
            )
            rate = _adherence_rate(followed_count, 0, total, social_count, unmarked_count)
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
