"""Pydantic schemas: request validation and response serialisation."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressBase(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Head Office"])
    street: str = Field(min_length=1, max_length=200, examples=["1 Main Street"])
    city: str = Field(min_length=1, max_length=100, examples=["Berlin"])
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20, examples=["10115"])
    country: str = Field(min_length=1, max_length=100, examples=["Germany"])
    latitude: float = Field(ge=-90, le=90, examples=[52.52])
    longitude: float = Field(ge=-180, le=180, examples=[13.405])

    @field_validator("name", "street", "city", "country")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Strip whitespace and reject strings that are only whitespace."""
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class AddressCreate(AddressBase):
    """Payload for creating an address."""


class AddressUpdate(BaseModel):
    """Payload for a partial update; every field is optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    street: str | None = Field(default=None, min_length=1, max_length=200)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class AddressRead(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class AddressNearby(AddressRead):
    distance_km: float
