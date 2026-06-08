import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


# ── Legacy source tests ────────────────────────────────────────────────────────

def test_uav_snapshot():
    r = client.get("/sources/uav/snapshot")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1


def test_uav_single_drone():
    r = client.get("/sources/uav/UAV-01")
    assert r.status_code == 200
    assert r.json()["drone_id"] == "UAV-01"


def test_uav_missing_drone():
    r = client.get("/sources/uav/GHOST-99")
    assert r.status_code == 404


def test_satellite_passes():
    r = client.get("/sources/satellite/passes?n=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 5
    assert all("satellite" in p for p in data)


def test_satellite_refresh():
    r = client.post("/sources/satellite/refresh")
    assert r.status_code == 200
    assert "satellite" in r.json()


def test_humint_signals():
    r = client.get("/sources/humint/signals?n=10")
    assert r.status_code == 200
    assert len(r.json()) == 10


def test_humint_radar():
    r = client.get("/sources/humint/radar?n=5")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_nato_no_key():
    r = client.get("/sources/nato/reports")
    assert r.status_code == 403


def test_nato_bad_key():
    r = client.get("/sources/nato/reports", headers={"X-API-Key": "wrong"})
    assert r.status_code == 403


def test_nato_valid_key():
    r = client.get("/sources/nato/reports?n=3", headers={"X-API-Key": "test-nato-key-1"})
    assert r.status_code == 200
    assert len(r.json()) <= 3


def test_civilian_reports():
    r = client.get("/sources/civilian/reports?n=10")
    assert r.status_code == 200
    assert len(r.json()) <= 10


def test_civilian_verified_only():
    r = client.get("/sources/civilian/reports?verified_only=true&n=20")
    assert r.status_code == 200
    assert all(rep["verified"] for rep in r.json())


def test_fused():
    r = client.get("/sources/fused?n=20")
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 20
    assert all("contributing_sources" in t for t in data)


# ── Scenario tests ─────────────────────────────────────────────────────────────

def test_scenario_status():
    r = client.get("/scenario/status")
    assert r.status_code == 200
    data = r.json()
    assert "elapsed_seconds" in data
    assert "time_scale" in data
    assert "current_wave" in data
    assert "total_entities" in data
    assert "active_attackers" in data
    assert "active_defenders" in data


def test_scenario_entities():
    r = client.get("/scenario/entities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    if data:
        e = data[0]
        assert "id" in e
        assert "name" in e
        assert "entity_type" in e
        assert "faction" in e
        assert "position" in e
        assert "heading_deg" in e
        assert "speed_kmh" in e


def test_scenario_attackers():
    r = client.get("/scenario/entities/attackers")
    assert r.status_code == 200
    data = r.json()
    assert all(e["faction"] == "attacker" for e in data)


def test_scenario_defenders():
    r = client.get("/scenario/entities/defenders")
    assert r.status_code == 200
    data = r.json()
    assert all(e["faction"] == "defender" for e in data)


def test_scenario_by_type():
    r = client.get("/scenario/entities/type/cruise_missile")
    assert r.status_code == 200
    data = r.json()
    assert all(e["entity_type"] == "cruise_missile" for e in data)


def test_scenario_wave_1():
    r = client.get("/scenario/wave/1")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert all(e["wave"] == 1 for e in data)


def test_scenario_reset():
    r = client.post("/scenario/reset", json={"time_scale": 1.0})
    assert r.status_code == 200
    assert r.json()["status"] == "reset"


def test_scenario_time_scale():
    r = client.post("/scenario/time_scale", json={"scale": 5.0})
    assert r.status_code == 200
    assert r.json()["time_scale"] == 5.0
    # Reset back to 1.0 so other tests are unaffected
    client.post("/scenario/time_scale", json={"scale": 1.0})


def test_scenario_total_entities():
    r = client.get("/scenario/status")
    data = r.json()
    assert data["total_entities"] > 0
