from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models import DailyImagePool
from routers.auth import get_current_user
from services.sync import run_sync

router = APIRouter(prefix="/api/images", tags=["images"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TagOut(BaseModel):
    id: int
    factory_code: str
    amount: Optional[str]
    tag_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageOut(BaseModel):
    id: int
    date: date
    image_url: str
    source: str
    is_locked: bool
    created_at: datetime
    tags: List[TagOut]

    model_config = {"from_attributes": True}


class SyncResult(BaseModel):
    status: str
    date: str
    total: Optional[int] = None
    added: Optional[int] = None
    message: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/sync", response_model=SyncResult)
def sync_today(
    sync_date: Optional[date] = Query(default=None, description="Date to sync, defaults to today"),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = run_sync(db, day=sync_date)
    return SyncResult(**result)


@router.get("", response_model=List[ImageOut])
def list_images(
    query_date: Optional[date] = Query(default=None, alias="date", description="Filter by date, defaults to today"),
    factory_code: Optional[str] = Query(default=None, description="Filter by factory code tag"),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if query_date is None:
        query_date = datetime.now().date()

    stmt = (
        select(DailyImagePool)
        .where(DailyImagePool.date == query_date)
        .options(selectinload(DailyImagePool.tags))
        .order_by(DailyImagePool.id)
    )

    images = list(db.scalars(stmt).all())

    if factory_code:
        images = [
            img for img in images
            if any(t.factory_code == factory_code for t in img.tags)
        ]

    return images


@router.get("/dates", response_model=List[date])
def list_dates(
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    rows = db.scalars(
        select(DailyImagePool.date).distinct().order_by(DailyImagePool.date.desc())
    ).all()
    return rows
