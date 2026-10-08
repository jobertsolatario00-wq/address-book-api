import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

BERLIN = {"name": "Berlin", "street": "1 Main St", "city": "Berlin", "country": "Germany",
          "latitude": 52.52, "longitude": 13.405}
POTSDAM = {**BERLIN, "name": "Potsdam", "city": "Potsdam", "latitude": 52.3906, "longitude": 13.0645}
PARIS = {**BERLIN, "name": "Paris", "city": "Paris", "country": "France", "latitude": 48.8566, "longitude": 2.3522}


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_crud_lifecycle(client):
    created = client.post("/addresses", json=BERLIN)
    assert created.status_code == 201
    aid = created.json()["id"]
    assert client.get(f"/addresses/{aid}").json()["city"] == "Berlin"
    patched = client.patch(f"/addresses/{aid}", json={"city": "Mitte"})
    assert patched.json()["city"] == "Mitte" and patched.json()["street"] == "1 Main St"
    assert client.delete(f"/addresses/{aid}").status_code == 204
    assert client.get(f"/addresses/{aid}").status_code == 404


@pytest.mark.parametrize("bad", [{"latitude": 91}, {"longitude": -181}, {"name": "   "}, {"country": ""}])
def test_validation(client, bad):
    assert client.post("/addresses", json={**BERLIN, **bad}).status_code == 422


def test_nearby(client):
    for a in (BERLIN, POTSDAM, PARIS):
        client.post("/addresses", json=a)
    res = client.get("/addresses/nearby", params={"latitude": 52.52, "longitude": 13.405, "distance_km": 50})
    assert [a["name"] for a in res.json()] == ["Berlin", "Potsdam"]
    assert res.json()[1]["distance_km"] == pytest.approx(27, abs=2)


def test_nearby_across_antimeridian(client):
    client.post("/addresses", json={**BERLIN, "name": "Fiji W", "latitude": -17.0, "longitude": 179.9})
    client.post("/addresses", json={**BERLIN, "name": "Fiji E", "latitude": -17.0, "longitude": -179.9})
    res = client.get("/addresses/nearby", params={"latitude": -17.0, "longitude": 179.95, "distance_km": 50})
    assert {a["name"] for a in res.json()} == {"Fiji W", "Fiji E"}


def test_nearby_invalid_params(client):
    assert client.get("/addresses/nearby", params={"latitude": 0, "longitude": 0, "distance_km": -1}).status_code == 422
