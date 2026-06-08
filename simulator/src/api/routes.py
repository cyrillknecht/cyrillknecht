"""FastAPI route definitions."""
from __future__ import annotations
import asyncio
import random
from datetime import datetime, timezone
from fastapi import APIRouter, Query, Header, WebSocket, WebSocketDisconnect, HTTPException
from src.sources import uav, satellite, humint, nato, civilian, fusion
from src.scenario.engine import ScenarioEngine
from src.models import (
    EntitySnapshot, ScenarioStatus, GeoPoint,
    SatellitePass, Detection, SignalIntercept, RadarTrack, CivilianReport,
)
from src.geo import SATELLITE_NAMES, CIVILIAN_DESCRIPTIONS, random_near

router = APIRouter()
scenario_router = APIRouter()

NATO_API_KEYS = {"test-nato-key-1", "test-nato-key-2"}


# ── UAV ────────────────────────────────────────────────────────────────────────

@router.get("/uav/snapshot", summary="All drone telemetry (one step per drone)")
def uav_snapshot():
    engine = ScenarioEngine.get()
    snap = engine.snapshot()
    uav_types = {"uav_recon", "uav_fpv", "uav_loiter"}
    attacker_uavs = [s for s in snap if s["entity_type"] in uav_types and s["faction"] == "attacker"]
    if attacker_uavs:
        return [
            {
                "drone_id": e["name"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "position": e["position"],
                "heading_deg": e["heading_deg"],
                "speed_kmh": e["speed_kmh"],
                "mode": "fpv" if e["entity_type"] == "uav_fpv" else ("loiter" if e["entity_type"] == "uav_loiter" else "recon"),
                "detections": [],
            }
            for e in attacker_uavs[:5]
        ]
    return uav.get_snapshot()


@router.get("/uav/{drone_id}", summary="Single drone telemetry")
def uav_drone(drone_id: str):
    result = uav.get_drone(drone_id)
    if result is None:
        raise HTTPException(404, f"Drone '{drone_id}' not found")
    return result


@router.websocket("/uav/stream/{drone_id}")
async def uav_stream(websocket: WebSocket, drone_id: str):
    """Streams telemetry for one drone at ~1 Hz."""
    await websocket.accept()
    state = uav.DRONES.get(drone_id)
    if state is None:
        await websocket.close(code=4004, reason=f"Drone '{drone_id}' not found")
        return
    try:
        while True:
            telem = state.step()
            await websocket.send_text(telem.model_dump_json())
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


# ── Satellite ─────────────────────────────────────────────────────────────────

@router.get("/satellite/passes", summary="Recent satellite passes with detections")
def sat_passes(n: int = Query(10, ge=1, le=50)):
    engine = ScenarioEngine.get()
    snap = engine.snapshot()
    ground_entities = [s for s in snap if s["position"]["alt_m"] <= 100]

    if not ground_entities:
        return satellite.get_latest(n)

    passes = []
    for _ in range(min(n, 5)):
        sat_name = random.choice(SATELLITE_NAMES)
        spread = 0.4
        center = random.choice(ground_entities)
        clat, clon = center["position"]["lat"], center["position"]["lon"]
        detections = []
        for entity in ground_entities:
            if random.random() < 0.8:
                pos = entity["position"]
                nlat, nlon = random_near(pos["lat"], pos["lon"], 0.01)
                confidence = round(random.uniform(0.70, 0.95), 2)
                detections.append(Detection(
                    timestamp=datetime.now(timezone.utc),
                    position=GeoPoint(lat=round(nlat, 6), lon=round(nlon, 6), alt_m=0),
                    category="vehicle",
                    confidence=confidence,
                    source=sat_name,
                ))
        passes.append(SatellitePass(
            satellite=sat_name,
            timestamp=datetime.now(timezone.utc),
            bbox=(round(clon - spread, 4), round(clat - spread, 4), round(clon + spread, 4), round(clat + spread, 4)),
            resolution_m=round(random.uniform(0.3, 2.0), 2),
            detections=detections[:10],
        ))
    return passes if passes else satellite.get_latest(n)


@router.post("/satellite/refresh", summary="Force a new satellite pass")
def sat_refresh():
    return satellite.refresh()


# ── HUMINT / SIGINT ────────────────────────────────────────────────────────────

@router.get("/humint/signals", summary="Recent SIGINT intercepts")
def humint_signals(n: int = Query(20, ge=1, le=100)):
    engine = ScenarioEngine.get()
    snap = engine.snapshot()
    airborne_types = {"cruise_missile", "ballistic_missile", "fighter_jet", "attack_aircraft",
                      "ew_aircraft", "bomber", "helicopter_attack", "helicopter_transport",
                      "uav_recon", "uav_fpv", "uav_loiter", "interceptor"}
    airborne = [s for s in snap if s["entity_type"] in airborne_types]

    if not airborne:
        return humint.get_intercepts(n)

    intercepts = []
    for entity in airborne[:n]:
        if random.random() < 0.7:
            pos = entity["position"]
            nlat, nlon = random_near(pos["lat"], pos["lon"], 0.05)
            sig_type = "jamming" if entity["entity_type"] == "ew_aircraft" else (
                "radar" if entity["entity_type"] in {"fighter_jet", "interceptor"} else "datalink"
            )
            intercepts.append(SignalIntercept(
                timestamp=datetime.now(timezone.utc),
                position=GeoPoint(lat=round(nlat, 6), lon=round(nlon, 6), alt_m=pos.get("alt_m")),
                frequency_mhz=round(random.uniform(100, 18000), 2),
                signal_type=sig_type,
                strength_dbm=round(random.uniform(-95, -30), 1),
                bearing_deg=round(random.uniform(0, 360), 1) if random.random() > 0.3 else None,
            ))
    while len(intercepts) < n:
        intercepts.extend(humint.get_intercepts(n - len(intercepts)))
    return intercepts[:n]


@router.get("/humint/radar", summary="Recent radar tracks")
def humint_radar(n: int = Query(20, ge=1, le=100)):
    engine = ScenarioEngine.get()
    snap = engine.snapshot()
    airborne_types = {"cruise_missile", "ballistic_missile", "fighter_jet", "attack_aircraft",
                      "ew_aircraft", "bomber", "helicopter_attack", "helicopter_transport",
                      "uav_recon", "uav_fpv", "uav_loiter", "interceptor"}
    airborne = [s for s in snap if s["entity_type"] in airborne_types]

    if not airborne:
        return humint.get_radar_tracks(n)

    tracks = []
    for entity in airborne[:n]:
        pos = entity["position"]
        nlat, nlon = random_near(pos["lat"], pos["lon"], 0.02)
        tracks.append(RadarTrack(
            timestamp=datetime.now(timezone.utc),
            position=GeoPoint(lat=round(nlat, 6), lon=round(nlon, 6), alt_m=pos.get("alt_m")),
            velocity_kmh=round(entity["speed_kmh"] + random.uniform(-20, 20), 1),
            heading_deg=round(entity["heading_deg"] + random.uniform(-10, 10), 1) % 360,
            rcs_m2=round(random.uniform(0.1, 40), 3),
        ))
    while len(tracks) < n:
        tracks.extend(humint.get_radar_tracks(n - len(tracks)))
    return tracks[:n]


# ── NATO ───────────────────────────────────────────────────────────────────────

@router.get("/nato/reports", summary="NATO partner intel reports (requires X-API-Key)")
def nato_reports(
    n: int = Query(10, ge=1, le=30),
    x_api_key: str | None = Header(default=None),
):
    if x_api_key not in NATO_API_KEYS:
        raise HTTPException(403, "Invalid or missing X-API-Key for NATO feed")
    try:
        return nato.get_reports(n, api_key=x_api_key)
    except PermissionError as e:
        raise HTTPException(403, str(e))


# ── Civilian ───────────────────────────────────────────────────────────────────

@router.get("/civilian/reports", summary="Civilian / OSINT incident reports")
def civilian_reports(
    n: int = Query(30, ge=1, le=100),
    verified_only: bool = Query(False),
):
    engine = ScenarioEngine.get()
    snap = engine.snapshot()
    ground_low = [s for s in snap if s["position"]["alt_m"] <= 200]

    base = civilian.get_reports(n, verified_only=verified_only)
    if not ground_low:
        return base

    extra: list[CivilianReport] = []
    for entity in ground_low[:20]:
        if random.random() < 0.4:
            pos = entity["position"]
            nlat, nlon = random_near(pos["lat"], pos["lon"], 0.03)
            verified = random.random() > 0.6
            if verified_only and not verified:
                continue
            extra.append(CivilianReport(
                timestamp=datetime.now(timezone.utc),
                position=GeoPoint(lat=round(nlat, 6), lon=round(nlon, 6)),
                description=random.choice(CIVILIAN_DESCRIPTIONS),
                verified=verified,
                confidence=round(random.uniform(0.3, 0.7), 2),
                source=random.choice(["osint", "verified_user", "ngo"]),
            ))

    combined = extra + list(base)
    return combined[:n]


# ── Fused ──────────────────────────────────────────────────────────────────────

@router.get("/fused", summary="Track-fused output from all sources")
def fused(n: int = Query(50, ge=1, le=200)):
    return fusion.get_fused_tracks(n)


# ── Scenario ───────────────────────────────────────────────────────────────────

def _entity_to_snapshot(e: dict) -> EntitySnapshot:
    pos = e["position"]
    return EntitySnapshot(
        id=e["id"],
        name=e["name"],
        entity_type=e["entity_type"],
        faction=e["faction"],
        wave=e["wave"],
        status=e["status"],
        position=GeoPoint(lat=pos["lat"], lon=pos["lon"], alt_m=pos.get("alt_m")),
        heading_deg=e["heading_deg"],
        speed_kmh=e["speed_kmh"],
    )


@scenario_router.get("/status", response_model=ScenarioStatus)
def scenario_status():
    return ScenarioEngine.get().status()


@scenario_router.get("/entities", response_model=list[EntitySnapshot])
def scenario_entities():
    snap = ScenarioEngine.get().snapshot()
    return [_entity_to_snapshot(e) for e in snap]


@scenario_router.get("/entities/attackers", response_model=list[EntitySnapshot])
def scenario_attackers():
    snap = ScenarioEngine.get().snapshot()
    return [_entity_to_snapshot(e) for e in snap if e["faction"] == "attacker"]


@scenario_router.get("/entities/defenders", response_model=list[EntitySnapshot])
def scenario_defenders():
    snap = ScenarioEngine.get().snapshot()
    return [_entity_to_snapshot(e) for e in snap if e["faction"] == "defender"]


@scenario_router.get("/entities/type/{entity_type}", response_model=list[EntitySnapshot])
def scenario_by_type(entity_type: str):
    snap = ScenarioEngine.get().snapshot()
    return [_entity_to_snapshot(e) for e in snap if e["entity_type"] == entity_type]


@scenario_router.get("/wave/{n}", response_model=list[EntitySnapshot])
def scenario_wave(n: int):
    engine = ScenarioEngine.get()
    t = engine.elapsed
    wave_entities = [e for e in engine.entities if e.wave == n and e.spawn_time <= t]
    result = []
    for e in wave_entities:
        pos = e.position_at(t)
        if pos is None:
            continue
        heading = e.heading_at(t)
        arrived = e.is_arrived(t)
        result.append(EntitySnapshot(
            id=e.id,
            name=e.name,
            entity_type=e.entity_type,
            faction=e.faction,
            wave=e.wave,
            status="arrived" if arrived else "active",
            position=GeoPoint(lat=round(pos[0], 6), lon=round(pos[1], 6), alt_m=round(pos[2], 1)),
            heading_deg=round(heading, 1),
            speed_kmh=round(e.speed_ms * 3.6, 1),
        ))
    return result


@scenario_router.post("/reset")
def scenario_reset(body: dict = None):
    time_scale = 1.0
    if body and "time_scale" in body:
        time_scale = float(body["time_scale"])
    ScenarioEngine.get().reset(time_scale)
    return {"status": "reset", "time_scale": time_scale}


@scenario_router.post("/time_scale")
def scenario_time_scale(body: dict):
    scale = float(body.get("scale", 1.0))
    ScenarioEngine.get().set_time_scale(scale)
    return {"status": "ok", "time_scale": scale}


@scenario_router.websocket("/stream")
async def scenario_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            snap = ScenarioEngine.get().snapshot()
            entities = [_entity_to_snapshot(e) for e in snap]
            data = [e.model_dump_json() for e in entities]
            await websocket.send_text(f"[{','.join(data)}]")
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
