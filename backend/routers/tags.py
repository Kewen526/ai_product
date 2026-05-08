from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import DailyImagePool, ImageTag
from routers.auth import get_current_user

router = APIRouter(prefix="/api/tags", tags=["tags"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    image_id: int
    factory_code: str
    amount: str | None = None
    tag_date: date | None = None  # defaults to today if omitted


class TagOut(BaseModel):
    id: int
    image_id: int
    factory_code: str
    amount: str | None
    tag_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def add_tag(
    body: TagCreate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    image = db.get(DailyImagePool, body.image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    tag = ImageTag(
        image_id=body.image_id,
        factory_code=body.factory_code.strip(),
        amount=body.amount.strip() if body.amount else None,
        tag_date=body.tag_date or datetime.now().date(),
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    tag = db.get(ImageTag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()


@router.get("", response_model=list[TagOut])
def list_tags(
    factory_code: str | None = Query(default=None),
    tag_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    stmt = select(ImageTag)
    if factory_code:
        stmt = stmt.where(ImageTag.factory_code == factory_code)
    if tag_date:
        stmt = stmt.where(ImageTag.tag_date == tag_date)
    stmt = stmt.order_by(ImageTag.created_at.desc())
    return db.scalars(stmt).all()


@router.get("/factory-codes", response_model=list[str])
def list_factory_codes(
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Return all distinct factory codes (for filter dropdowns)."""
    rows = db.scalars(
        select(ImageTag.factory_code).distinct().order_by(ImageTag.factory_code)
    ).all()
    return rows
