from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

import models


def get_country_by_name(db: Session, name: str):
    return (
        db.query(models.Country)
        .filter(func.lower(models.Country.name) == name.lower())
        .first()
    )


def get_countries(
    db: Session,
    region: str | None = None,
    currency: str | None = None,
    sort: str | None = None,
):
    q = db.query(models.Country)
    if region:
        q = q.filter(func.lower(models.Country.region) == region.lower())
    if currency:
        q = q.filter(func.lower(models.Country.currency_code) == currency.lower())
    if sort == "gdp_desc":
        q = q.order_by(models.Country.estimated_gdp.desc())
    return q.all()


def create_or_update_country(db: Session, country_data: dict):
    now = datetime.now(UTC)
    existing = get_country_by_name(db, country_data["name"])
    if existing:
        for k, v in country_data.items():
            setattr(existing, k, v)
        existing.last_refreshed_at = now
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    country_data["last_refreshed_at"] = now
    new = models.Country(**country_data)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def delete_country(db: Session, name: str):
    c = get_country_by_name(db, name)
    if not c:
        return None
    db.delete(c)
    db.commit()
    return c


def get_status(db: Session):
    total = db.query(models.Country).count()
    last = (
        db.query(models.Country)
        .order_by(models.Country.last_refreshed_at.desc())
        .first()
    )
    return {
        "total_countries": total,
        "last_refreshed_at": last.last_refreshed_at.isoformat()
        if last and last.last_refreshed_at
        else None,
    }
