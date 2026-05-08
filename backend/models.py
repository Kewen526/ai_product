from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Integer, String, Boolean, Date, DateTime, Text,
    ForeignKey, Numeric, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ── Read-only source tables (already exist in DB) ────────────────────────────

class CosUploadRecord(Base):
    __tablename__ = "cos_upload_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origin_url: Mapped[Optional[str]] = mapped_column(Text)
    finish_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class AiTask(Base):
    __tablename__ = "ai_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_image: Mapped[Optional[str]] = mapped_column(Text)
    task_type: Mapped[Optional[str]] = mapped_column(String(64))
    result_images: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(32))
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


# ── Application tables (created by this service) ─────────────────────────────

class DailyImagePool(Base):
    __tablename__ = "daily_image_pool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    # 'cos_zip' = came from cos_upload_records ZIP; 'ai_task' = came from ai_tasks
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    source_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tags: Mapped[list["ImageTag"]] = relationship(
        "ImageTag", back_populates="image", cascade="all, delete-orphan"
    )


class ImageTag(Base):
    __tablename__ = "image_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("daily_image_pool.id", ondelete="CASCADE"), nullable=False, index=True
    )
    factory_code: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Optional[str]] = mapped_column(String(64))
    tag_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    image: Mapped["DailyImagePool"] = relationship("DailyImagePool", back_populates="tags")
