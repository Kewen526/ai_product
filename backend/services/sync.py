"""
Daily sync service.

Flow:
  1. Read cos_upload_records for today → download each ZIP → extract images
  2. Read ai_tasks for today → parse result_images JSON → collect URLs
  3. Merge all image URLs, deduplicate against what's already saved
  4. If the day is already locked (reached DAILY_IMAGE_LIMIT), do nothing
  5. Insert new images; if total >= DAILY_IMAGE_LIMIT, randomly select
     exactly DAILY_IMAGE_LIMIT, delete the rest, mark survivors as locked
"""

import io
import json
import random
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Set

import requests
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config import DAILY_IMAGE_LIMIT, UPLOAD_DIR
from models import AiTask, CosUploadRecord, DailyImagePool


# ── helpers ───────────────────────────────────────────────────────────────────

def _today() -> date:
    return datetime.now().date()


def _day_upload_dir(day: date) -> Path:
    d = Path(UPLOAD_DIR) / str(day)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _is_day_locked(db: Session, day: date) -> bool:
    return db.scalar(
        select(func.count()).where(
            DailyImagePool.date == day,
            DailyImagePool.is_locked == True,
        )
    ) > 0


def _existing_urls(db: Session, day: date) -> Set[str]:
    rows = db.scalars(
        select(DailyImagePool.image_url).where(DailyImagePool.date == day)
    ).all()
    return set(rows)


# ── ZIP download & extract ────────────────────────────────────────────────────

def _download_and_extract_zip(zip_url: str, dest_dir: Path, source_id: int) -> List[str]:
    try:
        resp = requests.get(zip_url, timeout=120)
        resp.raise_for_status()
    except Exception as e:
        print(f"[sync] Failed to download {zip_url}: {e}")
        return []

    extracted_urls: List[str] = []
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for member in zf.namelist():
                lower = member.lower()
                if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                    filename = f"{source_id}_{Path(member).name}"
                    target = dest_dir / filename
                    target.write_bytes(zf.read(member))
                    relative = f"/static/uploads/{dest_dir.name}/{filename}"
                    extracted_urls.append(relative)
    except Exception as e:
        print(f"[sync] Failed to extract {zip_url}: {e}")

    return extracted_urls


# ── ai_tasks parsing ──────────────────────────────────────────────────────────

def _parse_result_images(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [v for v in data.values() if isinstance(v, str) and v.startswith("http")]


# ── core sync ─────────────────────────────────────────────────────────────────

def run_sync(db: Session, day: Optional[date] = None) -> dict:
    if day is None:
        day = _today()

    if _is_day_locked(db, day):
        return {"status": "locked", "date": str(day), "message": "Day is locked, no changes made."}

    existing = _existing_urls(db, day)
    dest_dir = _day_upload_dir(day)
    new_records: List[DailyImagePool] = []

    # ── source 1: cos_upload_records ─────────────────────────────────────────
    cos_rows = db.scalars(
        select(CosUploadRecord).where(
            func.date(CosUploadRecord.created_at) == day,
            CosUploadRecord.finish_url.isnot(None),
        )
    ).all()

    for row in cos_rows:
        url: str = row.finish_url.strip()
        if not url.lower().endswith(".zip"):
            if url not in existing:
                new_records.append(DailyImagePool(
                    date=day, image_url=url, source="cos_zip", source_id=row.id
                ))
            continue

        extracted = _download_and_extract_zip(url, dest_dir, row.id)
        for img_url in extracted:
            if img_url not in existing:
                new_records.append(DailyImagePool(
                    date=day, image_url=img_url, source="cos_zip", source_id=row.id
                ))

    # ── source 2: ai_tasks ───────────────────────────────────────────────────
    task_rows = db.scalars(
        select(AiTask).where(
            func.date(AiTask.created_at) == day,
            AiTask.result_images.isnot(None),
        )
    ).all()

    for row in task_rows:
        for img_url in _parse_result_images(row.result_images):
            if img_url not in existing:
                new_records.append(DailyImagePool(
                    date=day, image_url=img_url, source="ai_task", source_id=row.id
                ))
                existing.add(img_url)

    if not new_records:
        current_count = db.scalar(
            select(func.count()).where(DailyImagePool.date == day)
        )
        return {
            "status": "no_new",
            "date": str(day),
            "total": current_count,
            "added": 0,
        }

    db.add_all(new_records)
    db.flush()

    total_count = db.scalar(
        select(func.count()).where(DailyImagePool.date == day)
    )

    if total_count >= DAILY_IMAGE_LIMIT:
        all_ids: List[int] = list(db.scalars(
            select(DailyImagePool.id).where(DailyImagePool.date == day)
        ).all())

        keep_ids = set(random.sample(all_ids, DAILY_IMAGE_LIMIT))
        remove_ids = [i for i in all_ids if i not in keep_ids]

        if remove_ids:
            db.query(DailyImagePool).filter(DailyImagePool.id.in_(remove_ids)).delete(
                synchronize_session=False
            )

        db.query(DailyImagePool).filter(
            DailyImagePool.id.in_(list(keep_ids))
        ).update({"is_locked": True}, synchronize_session=False)

        db.commit()
        return {
            "status": "locked",
            "date": str(day),
            "total": DAILY_IMAGE_LIMIT,
            "added": len(new_records),
            "message": f"Reached {DAILY_IMAGE_LIMIT} images, day is now locked.",
        }

    db.commit()
    return {
        "status": "ok",
        "date": str(day),
        "total": total_count,
        "added": len(new_records),
    }
