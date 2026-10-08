"""Database access layer."""
import logging

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import geo, models, schemas

logger = logging.getLogger(__name__)


def get_address(db: Session, address_id: int) -> models.Address | None:
    return db.get(models.Address, address_id)


def list_addresses(db: Session, skip: int = 0, limit: int = 100) -> list[models.Address]:
    stmt = select(models.Address).order_by(models.Address.id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def create_address(db: Session, data: schemas.AddressCreate) -> models.Address:
    address = models.Address(**data.model_dump())
    db.add(address)
    db.commit()
    logger.info("Created address id=%s", address.id)
    return address


def update_address(db: Session, address: models.Address, data: schemas.AddressUpdate) -> models.Address:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(address, field, value)
    db.commit()
    logger.info("Updated address id=%s", address.id)
    return address


def delete_address(db: Session, address: models.Address) -> None:
    db.delete(address)
    db.commit()
    logger.info("Deleted address id=%s", address.id)


def find_nearby(db: Session, lat: float, lon: float, distance_km: float) -> list[tuple[models.Address, float]]:
    """Addresses within ``distance_km`` of the point, nearest first.

    A bounding box narrows the rows in SQL; the haversine formula then gives
    the exact distance.
    """
    min_lat, max_lat, lon_ranges = geo.bounding_box(lat, lon, distance_km)
    stmt = select(models.Address).where(
        models.Address.latitude.between(min_lat, max_lat),
        or_(*(models.Address.longitude.between(lo, hi) for lo, hi in lon_ranges)),
    )

    results = []
    for address in db.scalars(stmt):
        distance = geo.haversine_km(lat, lon, address.latitude, address.longitude)
        if distance <= distance_km:
            results.append((address, distance))
    results.sort(key=lambda pair: pair[1])
    logger.info("Nearby search (%s, %s, %s km) returned %d result(s)", lat, lon, distance_km, len(results))
    return results
