"""RoundRobinState model - tracks rotation state per meal type per user."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class RoundRobinState(Base):
    """
    Tracks rotation state per meal type per user.

    Maintains the last-used meal ID for each meal type to enable deterministic
    round-robin meal selection. The algorithm orders meals by (created_at ASC, id ASC)
    and advances through them in sequence.

    See Tech Spec section 3.1 and ADR-002 for algorithm details.
    """
    __tablename__ = "round_robin_state"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "meal_type_id", name="pk_round_robin_state"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    meal_type_id = Column(UUID(as_uuid=True), ForeignKey("meal_type.id", ondelete="CASCADE"), nullable=False)
    last_meal_id = Column(UUID(as_uuid=True), ForeignKey("meal.id", ondelete="SET NULL"))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="round_robin_states")
    meal_type = relationship("MealType", back_populates="round_robin_state")
    last_meal = relationship("Meal", foreign_keys=[last_meal_id])

    def __repr__(self):
        return f"<RoundRobinState(user={self.user_id}, meal_type={self.meal_type_id}, last_meal={self.last_meal_id})>"
