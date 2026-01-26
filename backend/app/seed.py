"""
Seed script for MealFrame initial data.

Run from backend directory:
    python -m app.seed

Idempotent - safe to re-run. Checks for existing data before inserting.
Data defined in docs/frozen/SEED_DATA.md
"""

import asyncio
import logging
from decimal import Decimal

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models import (
    AppConfig,
    DayTemplate,
    DayTemplateSlot,
    Meal,
    MealType,
    WeekPlan,
    WeekPlanDay,
    meal_to_meal_type,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data definitions (from docs/frozen/SEED_DATA.md)
# ---------------------------------------------------------------------------

MEAL_TYPES = [
    {"name": "Breakfast", "description": "Standard weekday breakfast. Protein + slow carbs. Low decision, routine anchor.", "tags": ["weekday", "morning"]},
    {"name": "Pre-Workout Breakfast", "description": "Morning workout fuel. Higher carbs, easy to digest.", "tags": ["workout", "morning", "pre-workout"]},
    {"name": "Mid-Morning Protein", "description": "Appetite control snack. Coffee + protein drink.", "tags": ["snack", "protein"]},
    {"name": "Lunch", "description": "Main daytime meal. Balanced macros, satiety-focused.", "tags": ["main-meal"]},
    {"name": "Afternoon Filler", "description": "Prevent evening hunger. Protein + fiber. Non-workout days.", "tags": ["snack", "protein", "evening-prep"]},
    {"name": "Pre-Workout Snack", "description": "Evening workout fuel. Carb-forward.", "tags": ["workout", "pre-workout", "snack"]},
    {"name": "Post-Workout Snack", "description": "Post-workout recovery. Protein-dominant, hunger dampening.", "tags": ["workout", "post-workout", "snack", "protein"]},
    {"name": "Dinner", "description": "Family meal. Protein-heavy, controlled carbs. High environmental risk.", "tags": ["main-meal", "evening"]},
    {"name": "After-Exercise Dinner", "description": "Post-workout dinner variant. Recovery framing.", "tags": ["main-meal", "evening", "post-workout"]},
    {"name": "Weekend Breakfast", "description": "Weekend morning meal. More caloric, protein-first.", "tags": ["weekend", "morning"]},
    {"name": "Light Dinner", "description": "Calorie control dinner. Protein + vegetables.", "tags": ["main-meal", "evening", "light"]},
    {"name": "Hiking Fuel", "description": "Endurance activity fuel. Carbs + protein.", "tags": ["weekend", "activity", "endurance"]},
]

# Each meal: (name, portion_description, calories, protein, carbs, fat, [meal_type_names])
MEALS = [
    # Breakfast
    ("Scrambled Eggs", "2 eggs + 1 slice whole wheat toast + 10g butter", 320, 18, 15, 22, ["Breakfast", "Weekend Breakfast"]),
    ("Oatmeal Classic", "60g oats + 200ml milk + 1 tbsp honey", 350, 12, 55, 8, ["Breakfast"]),
    ("Greek Yogurt Parfait", "200g Greek yogurt + 30g granola + mixed berries", 320, 22, 38, 10, ["Breakfast", "Weekend Breakfast"]),
    # Pre-Workout Breakfast
    ("Banana Oatmeal", "50g oats + 1 banana + 1 scoop whey", 420, 32, 58, 6, ["Pre-Workout Breakfast"]),
    ("Toast with Peanut Butter", "2 slices toast + 30g peanut butter + 1 banana", 450, 15, 55, 20, ["Pre-Workout Breakfast"]),
    # Mid-Morning Protein
    ("Protein Coffee", "1 scoop whey + 200ml cold coffee + ice", 120, 25, 3, 1, ["Mid-Morning Protein"]),
    ("Protein Shake Simple", "1.5 scoops whey + 300ml water", 180, 38, 4, 2, ["Mid-Morning Protein"]),
    # Lunch
    ("Chicken Rice Bowl", "150g chicken breast + 150g rice + mixed vegetables", 520, 42, 50, 12, ["Lunch"]),
    ("Tuna Salad", "1 can tuna + mixed greens + 1 tbsp olive oil + vegetables", 380, 35, 12, 22, ["Lunch"]),
    ("Turkey Sandwich", "100g turkey + 2 slices bread + lettuce + tomato + mustard", 380, 32, 35, 12, ["Lunch"]),
    # Afternoon Filler
    ("Cottage Cheese Bowl", "200g cottage cheese + cucumber + cherry tomatoes", 220, 28, 8, 8, ["Afternoon Filler"]),
    ("Protein Bar", "1 protein bar (60g)", 220, 20, 22, 8, ["Afternoon Filler", "Pre-Workout Snack"]),
    ("Veggie Sticks with Hummus", "Carrots + celery + bell pepper + 60g hummus", 180, 6, 18, 10, ["Afternoon Filler"]),
    # Pre-Workout Snack
    ("Rice Cakes with Banana", "3 rice cakes + 1 banana + 15g honey", 280, 4, 62, 2, ["Pre-Workout Snack"]),
    ("Energy Balls", "3 energy balls (dates + oats + peanut butter)", 250, 6, 35, 10, ["Pre-Workout Snack"]),
    # Post-Workout Snack
    ("Protein Smoothie", "1.5 scoops whey + 1 banana + 200ml milk", 350, 40, 35, 6, ["Post-Workout Snack"]),
    ("Greek Yogurt with Honey", "250g Greek yogurt + 1 tbsp honey", 280, 25, 28, 8, ["Post-Workout Snack"]),
    ("Chocolate Milk Recovery", "500ml chocolate milk", 320, 16, 48, 8, ["Post-Workout Snack"]),
    # Dinner
    ("Grilled Salmon", "180g salmon + 200g roasted vegetables + small potato", 520, 42, 30, 25, ["Dinner", "After-Exercise Dinner"]),
    ("Chicken Stir Fry", "150g chicken + mixed vegetables + 100g rice", 480, 38, 40, 18, ["Dinner", "After-Exercise Dinner"]),
    ("Beef with Vegetables", "150g lean beef + broccoli + carrots + 100g rice", 520, 40, 35, 22, ["Dinner", "After-Exercise Dinner"]),
    ("Pasta Bolognese", "100g pasta + 150g meat sauce + side salad", 580, 35, 55, 22, ["Dinner"]),
    # Light Dinner
    ("Grilled Chicken Salad", "150g chicken breast + large mixed salad + 1 tbsp dressing", 350, 40, 12, 16, ["Light Dinner"]),
    ("Egg White Omelette", "4 egg whites + vegetables + 30g feta", 220, 28, 6, 10, ["Light Dinner"]),
    ("Fish with Vegetables", "150g white fish + steamed vegetables + lemon", 280, 35, 10, 12, ["Light Dinner"]),
    # Weekend Breakfast
    ("Full Breakfast", "2 eggs + 2 bacon strips + toast + tomatoes + beans (half portion)", 550, 30, 35, 32, ["Weekend Breakfast"]),
    ("Protein Pancakes", "3 protein pancakes + berries + 1 tbsp maple syrup", 480, 35, 50, 15, ["Weekend Breakfast"]),
    ("Avocado Toast Deluxe", "2 slices toast + 1 avocado + 2 poached eggs", 520, 22, 35, 35, ["Weekend Breakfast"]),
    # Hiking Fuel
    ("Trail Mix Pack", "80g trail mix (nuts + dried fruit)", 420, 12, 40, 26, ["Hiking Fuel"]),
    ("PB&J Sandwich", "2 slices bread + 30g peanut butter + 20g jam", 450, 14, 55, 20, ["Hiking Fuel"]),
    ("Banana + Protein Bar", "1 banana + 1 protein bar", 340, 22, 45, 10, ["Hiking Fuel"]),
]

# (template_name, notes, [(position, meal_type_name), ...])
DAY_TEMPLATES = [
    ("Normal Workday", "Standard non-workout weekday. Focus on hunger control and evening restraint.", [
        (1, "Breakfast"),
        (2, "Mid-Morning Protein"),
        (3, "Lunch"),
        (4, "Afternoon Filler"),
        (5, "Dinner"),
    ]),
    ("Morning Workout Workday", "Gym session in the morning. Fuel before, recover after, stable evening.", [
        (1, "Pre-Workout Breakfast"),
        (2, "Post-Workout Snack"),
        (3, "Lunch"),
        (4, "Afternoon Filler"),
        (5, "Dinner"),
    ]),
    ("Evening Workout Workday", "Gym session in the evening. Prevent post-workout binge behavior.", [
        (1, "Breakfast"),
        (2, "Mid-Morning Protein"),
        (3, "Lunch"),
        (4, "Pre-Workout Snack"),
        (5, "After-Exercise Dinner"),
    ]),
    ("Weekend", "Standard weekend day. Enjoyment with boundaries.", [
        (1, "Weekend Breakfast"),
        (2, "Lunch"),
        (3, "Light Dinner"),
    ]),
    ("Hiking Weekend Day", "Long hike or outdoor activity. Extra fuel for endurance.", [
        (1, "Weekend Breakfast"),
        (2, "Hiking Fuel"),
        (3, "Lunch"),
        (4, "Light Dinner"),
    ]),
]

# (weekday_index, template_name)
DEFAULT_WEEK_PLAN_DAYS = [
    (0, "Normal Workday"),        # Monday
    (1, "Morning Workout Workday"),  # Tuesday
    (2, "Normal Workday"),        # Wednesday
    (3, "Evening Workout Workday"),  # Thursday
    (4, "Morning Workout Workday"),  # Friday
    (5, "Weekend"),               # Saturday
    (6, "Weekend"),               # Sunday
]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

async def seed_app_config(db: AsyncSession) -> None:
    """Create app_config singleton if it doesn't exist."""
    result = await db.execute(select(AppConfig).where(AppConfig.id == 1))
    config = result.scalar_one_or_none()
    if config:
        logger.info("AppConfig already exists, skipping")
        return
    config = AppConfig(id=1, timezone="Europe/Ljubljana", week_start_day=0)
    db.add(config)
    await db.flush()
    logger.info("Created AppConfig (timezone=Europe/Ljubljana, week_start_day=0)")


async def seed_meal_types(db: AsyncSession) -> dict[str, MealType]:
    """Create meal types. Returns name→MealType mapping."""
    result = await db.execute(select(MealType))
    existing = {mt.name: mt for mt in result.scalars().all()}

    if len(existing) >= len(MEAL_TYPES):
        logger.info(f"All {len(existing)} meal types already exist, skipping")
        return existing

    name_to_obj: dict[str, MealType] = {}
    created = 0
    for mt_data in MEAL_TYPES:
        if mt_data["name"] in existing:
            name_to_obj[mt_data["name"]] = existing[mt_data["name"]]
            continue
        mt = MealType(**mt_data)
        db.add(mt)
        await db.flush()  # Get ID assigned
        name_to_obj[mt.name] = mt
        created += 1

    logger.info(f"Created {created} meal types ({len(existing)} already existed)")
    return name_to_obj


async def seed_meals(db: AsyncSession, meal_type_map: dict[str, MealType]) -> None:
    """Create meals and their meal_type associations."""
    result = await db.execute(select(Meal))
    existing_names = {m.name for m in result.scalars().all()}

    if len(existing_names) >= len(MEALS):
        logger.info(f"All {len(existing_names)} meals already exist, skipping")
        return

    created = 0
    for name, portion, cals, protein, carbs, fat, type_names in MEALS:
        if name in existing_names:
            continue
        meal = Meal(
            name=name,
            portion_description=portion,
            calories_kcal=cals,
            protein_g=Decimal(str(protein)),
            carbs_g=Decimal(str(carbs)),
            fat_g=Decimal(str(fat)),
        )
        db.add(meal)
        await db.flush()

        # Create meal_to_meal_type associations
        for type_name in type_names:
            mt = meal_type_map.get(type_name)
            if not mt:
                logger.warning(f"Meal type '{type_name}' not found for meal '{name}'")
                continue
            await db.execute(
                insert(meal_to_meal_type).values(meal_id=meal.id, meal_type_id=mt.id)
            )

        created += 1

    await db.flush()
    logger.info(f"Created {created} meals ({len(existing_names)} already existed)")


async def seed_day_templates(db: AsyncSession, meal_type_map: dict[str, MealType]) -> dict[str, DayTemplate]:
    """Create day templates with slots. Returns name→DayTemplate mapping."""
    result = await db.execute(select(DayTemplate))
    existing = {dt.name: dt for dt in result.scalars().all()}

    if len(existing) >= len(DAY_TEMPLATES):
        logger.info(f"All {len(existing)} day templates already exist, skipping")
        return existing

    name_to_obj: dict[str, DayTemplate] = {}
    created = 0
    for tmpl_name, notes, slots_data in DAY_TEMPLATES:
        if tmpl_name in existing:
            name_to_obj[tmpl_name] = existing[tmpl_name]
            continue

        tmpl = DayTemplate(name=tmpl_name, notes=notes)
        db.add(tmpl)
        await db.flush()

        for position, mt_name in slots_data:
            mt = meal_type_map.get(mt_name)
            if not mt:
                logger.warning(f"Meal type '{mt_name}' not found for template '{tmpl_name}'")
                continue
            slot = DayTemplateSlot(
                day_template_id=tmpl.id,
                position=position,
                meal_type_id=mt.id,
            )
            db.add(slot)

        await db.flush()
        name_to_obj[tmpl_name] = tmpl
        created += 1

    logger.info(f"Created {created} day templates ({len(existing)} already existed)")
    return name_to_obj


async def seed_week_plan(db: AsyncSession, template_map: dict[str, DayTemplate]) -> WeekPlan:
    """Create default week plan with day mappings."""
    result = await db.execute(select(WeekPlan).where(WeekPlan.name == "Default Week"))
    existing = result.scalar_one_or_none()

    if existing:
        logger.info("Default Week plan already exists, skipping")
        return existing

    plan = WeekPlan(name="Default Week", is_default=True)
    db.add(plan)
    await db.flush()

    for weekday, tmpl_name in DEFAULT_WEEK_PLAN_DAYS:
        tmpl = template_map.get(tmpl_name)
        if not tmpl:
            logger.warning(f"Template '{tmpl_name}' not found for weekday {weekday}")
            continue
        day = WeekPlanDay(
            week_plan_id=plan.id,
            weekday=weekday,
            day_template_id=tmpl.id,
        )
        db.add(day)

    await db.flush()
    logger.info("Created Default Week plan with 7 day mappings")
    return plan


async def update_app_config_default_plan(db: AsyncSession, week_plan: WeekPlan) -> None:
    """Set default_week_plan_id in app_config."""
    result = await db.execute(select(AppConfig).where(AppConfig.id == 1))
    config = result.scalar_one_or_none()
    if not config:
        logger.warning("AppConfig not found, cannot set default_week_plan_id")
        return

    if config.default_week_plan_id == week_plan.id:
        logger.info("AppConfig already has correct default_week_plan_id, skipping")
        return

    config.default_week_plan_id = week_plan.id
    await db.flush()
    logger.info(f"Updated AppConfig default_week_plan_id to {week_plan.id}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_seed() -> None:
    """Execute all seed operations in order."""
    logger.info("Starting seed...")

    async with AsyncSessionLocal() as db:
        try:
            # 1. App config
            await seed_app_config(db)

            # 2. Meal types
            meal_type_map = await seed_meal_types(db)

            # 3-4. Meals + associations
            await seed_meals(db, meal_type_map)

            # 5-6. Day templates + slots
            template_map = await seed_day_templates(db, meal_type_map)

            # 7-8. Week plan + day mappings
            week_plan = await seed_week_plan(db, template_map)

            # 9. Update app_config with default plan
            await update_app_config_default_plan(db, week_plan)

            await db.commit()
            logger.info("Seed complete!")

        except Exception:
            await db.rollback()
            logger.exception("Seed failed, rolled back")
            raise
        finally:
            await db.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_seed())
