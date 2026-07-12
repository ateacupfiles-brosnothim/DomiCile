"""
SQLAlchemy ORM Models — Tasks Management App
Matches schema.sql exactly (UUID PKs, constraints, indexes, triggers).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp (avoids the deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username      = Column(String(50),  unique=True, nullable=False)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url    = Column(String(255))
    created_at    = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                           onupdate=_utcnow)

    # Relationships
    tasks        = relationship("Task",       back_populates="owner",  cascade="all, delete-orphan")
    teams_owned  = relationship("Team",       back_populates="creator", foreign_keys="Team.created_by")
    memberships  = relationship("TeamMember", back_populates="user",   cascade="all, delete-orphan")
    shares_made  = relationship("TaskShare",  back_populates="sharer", foreign_keys="TaskShare.shared_by")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

class Team(Base):
    __tablename__ = "teams"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name        = Column(String(100), nullable=False)
    description = Column(Text)
    created_by  = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at  = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                         onupdate=_utcnow)

    # Relationships
    creator = relationship("User",       back_populates="teams_owned", foreign_keys=[created_by])
    members = relationship("TeamMember", back_populates="team",        cascade="all, delete-orphan")
    shares  = relationship("TaskShare",  back_populates="team",        cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# TeamMember
# ---------------------------------------------------------------------------

class TeamMember(Base):
    __tablename__ = "team_members"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    team_id   = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"),  nullable=False)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),  nullable=False)
    role      = Column(String(20),  nullable=False, default="member")
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
        CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_team_members_role"),
        Index("idx_team_members_user_id", "user_id"),
        Index("idx_team_members_team_id", "team_id"),
    )

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="memberships")

    def __repr__(self) -> str:
        return f"<TeamMember team={self.team_id} user={self.user_id} role={self.role!r}>"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task(Base):
    __tablename__ = "tasks"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text      = Column(Text,        nullable=False)
    priority  = Column(String(20),  nullable=False, default="normal")
    status    = Column(String(20),  nullable=False, default="open")
    deadline  = Column(DateTime(timezone=True))
    photo_url = Column(String(255))

    # AI fields
    ai_extracted      = Column(Boolean,       nullable=False, default=False)
    ai_summary        = Column(Text)
    ai_suggested_tags = Column(ARRAY(Text))   # PostgreSQL native text[]

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(),
                        onupdate=_utcnow)

    __table_args__ = (
        CheckConstraint("priority IN ('urgent', 'normal', 'low')",                 name="ck_tasks_priority"),
        CheckConstraint("status IN ('open', 'in_progress', 'done', 'cancelled')", name="ck_tasks_status"),
        Index("idx_tasks_user_id",      "user_id"),
        Index("idx_tasks_priority",     "priority"),
        Index("idx_tasks_status",       "status"),
        # Partial indexes are defined via DDL event below (SQLAlchemy limitation)
    )

    # Relationships
    owner  = relationship("User",      back_populates="tasks")
    shares = relationship("TaskShare", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Task id={self.id} priority={self.priority!r} status={self.status!r}>"


# ---------------------------------------------------------------------------
# TaskShare
# ---------------------------------------------------------------------------

class TaskShare(Base):
    __tablename__ = "task_shares"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    task_id   = Column(UUID(as_uuid=True), ForeignKey("tasks.id",  ondelete="CASCADE"),  nullable=False)
    team_id   = Column(UUID(as_uuid=True), ForeignKey("teams.id",  ondelete="CASCADE"),  nullable=False)
    shared_by = Column(UUID(as_uuid=True), ForeignKey("users.id",  ondelete="RESTRICT"), nullable=False)
    shared_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("task_id", "team_id", name="uq_task_shares_task_team"),
        Index("idx_task_shares_task_id", "task_id"),
        Index("idx_task_shares_team_id", "team_id"),
    )

    # Relationships
    task   = relationship("Task", back_populates="shares")
    team   = relationship("Team", back_populates="shares")
    sharer = relationship("User", back_populates="shares_made", foreign_keys=[shared_by])

    def __repr__(self) -> str:
        return f"<TaskShare task={self.task_id} team={self.team_id}>"


# ---------------------------------------------------------------------------
# Partial indexes — must be created via DDL event because SQLAlchemy's
# Index() does not support WHERE clauses portably across all backends.
# ---------------------------------------------------------------------------

@event.listens_for(Base.metadata, "after_create")
def _create_partial_indexes(target, connection, **kw) -> None:
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tasks_deadline "
        "ON tasks(deadline) WHERE deadline IS NOT NULL"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tasks_ai_extracted "
        "ON tasks(ai_extracted) WHERE ai_extracted = TRUE"
    )
