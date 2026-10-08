"""Address endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/addresses", tags=["addresses"])
DbSession = Annotated[Session, Depends(get_db)]


def _get_or_404(db: Session, address_id: int) -> models.Address:
    address = crud.get_address(db, address_id)
    if address is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Address {address_id} not found")
    return address


@router.post("", response_model=schemas.AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(data: schemas.AddressCreate, db: DbSession):
    """Create a new address."""
    return crud.create_address(db, data)


# Declared before "/{address_id}" so "nearby" is not parsed as an id.
@router.get("/nearby", response_model=list[schemas.AddressNearby])
def get_nearby_addresses(
    db: DbSession,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    distance_km: Annotated[float, Query(gt=0, le=20040, description="Search radius in kilometres")],
):
    """Return addresses within ``distance_km`` of the given coordinates, nearest first."""
    return [
        schemas.AddressNearby(**schemas.AddressRead.model_validate(a).model_dump(), distance_km=round(d, 3))
        for a, d in crud.find_nearby(db, latitude, longitude, distance_km)
    ]


@router.get("", response_model=list[schemas.AddressRead])
def list_addresses(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """List addresses (paginated)."""
    return crud.list_addresses(db, skip, limit)


@router.get("/{address_id}", response_model=schemas.AddressRead)
def get_address(address_id: int, db: DbSession):
    """Retrieve one address."""
    return _get_or_404(db, address_id)


@router.patch("/{address_id}", response_model=schemas.AddressRead)
def update_address(address_id: int, data: schemas.AddressUpdate, db: DbSession):
    """Partially update an address."""
    return crud.update_address(db, _get_or_404(db, address_id), data)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, db: DbSession):
    """Delete an address."""
    crud.delete_address(db, _get_or_404(db, address_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
