from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint, Index, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # リレーション
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    document_url = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())

    # リレーション
    user = relationship("User", back_populates="projects")
    members = relationship("Member", back_populates="project", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    email = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())

    # Check制約
    __table_args__ = (
        CheckConstraint("role IN ('Member', 'PM', 'PL')", name="check_role"),
        Index("idx_members_project_id", "project_id"),
    )

    # リレーション
    project = relationship("Project", back_populates="members")
    scores = relationship("Score", back_populates="member", cascade="all, delete-orphan")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())

    # Check制約
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
        Index("idx_scores_member_id", "member_id"),
        Index("idx_scores_created_at", "created_at"),
    )

    # リレーション
    member = relationship("Member", back_populates="scores")
