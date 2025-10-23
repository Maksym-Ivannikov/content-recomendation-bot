from typing import Any, Optional
from sqlalchemy import Column, BigInteger, Integer, Text, TIMESTAMP, Boolean, ForeignKey, Index, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db import Base


class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class Recommendations(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(16))  # movie/series/book/game
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_recs_created_at", "created_at"),)


class Quizzes(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(16))  # movie/series/book/game
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    questions: Mapped[list["Questions"]] = relationship(
        back_populates="quiz", cascade="all,delete-orphan"
    )


class Questions(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id"))
    text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String(1))  # 'A' | 'B' | 'C'
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    quiz: Mapped["Quizzes"] = relationship(back_populates="questions")

    __table_args__ = (
        Index("ix_questions_quiz", "quiz_id"),
        Index("ix_questions_approved", "is_approved"),
    )


class QuizResults(Base):
    __tablename__ = "quiz_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("quizzes.id"))
    score: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[Any] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_results_quiz", "quiz_id"),
        Index("ix_results_user", "user_id"),
    )
