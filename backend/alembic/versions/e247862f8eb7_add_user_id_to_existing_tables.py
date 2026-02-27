"""add_user_id_to_existing_tables

Adds user_id FK to all existing tables, creates an admin user,
backfills existing data with the admin user_id, then sets NOT NULL.

Also changes unique constraints to be per-user (composite with user_id).

Revision ID: e247862f8eb7
Revises: 6a9cd73c43d6
Create Date: 2026-02-27 14:52:19.536266

"""
import os
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'e247862f8eb7'
down_revision = '6a9cd73c43d6'
branch_labels = None
depends_on = None

# Fixed admin user UUID for deterministic migration (same across environments)
ADMIN_USER_ID = "00000000-0000-4000-a000-000000000001"


def upgrade() -> None:
    conn = op.get_bind()

    # ── Step 1: Create admin user for backfill ──────────────────────────
    admin_email = os.getenv("ADMIN_EMAIL", "admin@mealframe.io")

    # Check if admin user already exists (idempotent)
    result = conn.execute(
        sa.text("SELECT id FROM \"user\" WHERE email = :email"),
        {"email": admin_email},
    )
    admin_row = result.fetchone()
    if admin_row:
        admin_id = str(admin_row[0])
    else:
        admin_id = ADMIN_USER_ID
        conn.execute(
            sa.text("""
                INSERT INTO "user" (id, email, password_hash, email_verified, is_active, auth_provider, created_at, updated_at)
                VALUES (:id, :email, NULL, true, true, 'email', now(), now())
            """),
            {"id": admin_id, "email": admin_email},
        )

    # ── Step 2: Add user_id columns as NULLABLE ─────────────────────────
    tables = ['meal', 'meal_type', 'day_template', 'week_plan', 'weekly_plan_instance']
    for table in tables:
        op.add_column(table, sa.Column('user_id', UUID(), nullable=True))

    # round_robin_state: add user_id and change PK
    op.add_column('round_robin_state', sa.Column('user_id', UUID(), nullable=True))

    # ── Step 3: Backfill all existing rows with admin user_id ───────────
    for table in tables + ['round_robin_state']:
        conn.execute(
            sa.text(f'UPDATE "{table}" SET user_id = :uid WHERE user_id IS NULL'),
            {"uid": admin_id},
        )

    # ── Step 4: Set NOT NULL ────────────────────────────────────────────
    for table in tables + ['round_robin_state']:
        op.alter_column(table, 'user_id', nullable=False)

    # ── Step 5: Add indexes and FK constraints ──────────────────────────
    for table in tables:
        op.create_index(f'ix_{table}_user_id', table, ['user_id'], unique=False)
        op.create_foreign_key(f'fk_{table}_user_id', table, 'user', ['user_id'], ['id'], ondelete='CASCADE')

    op.create_foreign_key('fk_round_robin_state_user_id', 'round_robin_state', 'user', ['user_id'], ['id'], ondelete='CASCADE')

    # ── Step 6: Update unique constraints to be per-user ────────────────

    # day_template: unique(name) → unique(user_id, name)
    op.drop_constraint('day_template_name_key', 'day_template', type_='unique')
    op.create_unique_constraint('uq_day_template_user_name', 'day_template', ['user_id', 'name'])

    # meal_type: unique index on name → unique(user_id, name)
    # The old unique constraint was created as a unique index
    op.drop_index('ix_meal_type_name', table_name='meal_type')
    op.create_unique_constraint('uq_meal_type_user_name', 'meal_type', ['user_id', 'name'])

    # weekly_plan_instance: unique(week_start_date) → unique(user_id, week_start_date)
    op.drop_index('ix_weekly_plan_instance_week_start_date', table_name='weekly_plan_instance')
    op.create_index('ix_weekly_plan_instance_week_start_date', 'weekly_plan_instance', ['week_start_date'], unique=False)
    op.create_unique_constraint('uq_weekly_plan_instance_user_week', 'weekly_plan_instance', ['user_id', 'week_start_date'])

    # ── Step 7: round_robin_state PK change ─────────────────────────────
    # Old PK: (meal_type_id) → New PK: (user_id, meal_type_id)
    op.drop_constraint('round_robin_state_pkey', 'round_robin_state', type_='primary')
    op.create_primary_key('pk_round_robin_state', 'round_robin_state', ['user_id', 'meal_type_id'])


def downgrade() -> None:
    # ── Reverse PK change on round_robin_state ──────────────────────────
    op.drop_constraint('pk_round_robin_state', 'round_robin_state', type_='primary')
    op.create_primary_key('round_robin_state_pkey', 'round_robin_state', ['meal_type_id'])

    # ── Restore unique constraints ──────────────────────────────────────
    op.drop_constraint('uq_weekly_plan_instance_user_week', 'weekly_plan_instance', type_='unique')
    op.drop_index('ix_weekly_plan_instance_week_start_date', table_name='weekly_plan_instance')
    op.create_index('ix_weekly_plan_instance_week_start_date', 'weekly_plan_instance', ['week_start_date'], unique=True)

    op.drop_constraint('uq_meal_type_user_name', 'meal_type', type_='unique')
    op.create_index('ix_meal_type_name', 'meal_type', ['name'], unique=True)

    op.drop_constraint('uq_day_template_user_name', 'day_template', type_='unique')
    op.create_unique_constraint('day_template_name_key', 'day_template', ['name'])

    # ── Drop FK constraints and indexes ─────────────────────────────────
    op.drop_constraint('fk_round_robin_state_user_id', 'round_robin_state', type_='foreignkey')

    tables = ['weekly_plan_instance', 'week_plan', 'day_template', 'meal_type', 'meal']
    for table in tables:
        op.drop_constraint(f'fk_{table}_user_id', table, type_='foreignkey')
        op.drop_index(f'ix_{table}_user_id', table_name=table)

    # ── Drop user_id columns ────────────────────────────────────────────
    for table in tables + ['round_robin_state']:
        op.drop_column(table, 'user_id')

    # Note: admin user is NOT deleted on downgrade (data preservation)
