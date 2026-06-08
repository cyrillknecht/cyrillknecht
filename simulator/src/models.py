from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
import uuid


class GeoPoint(BaseModel):
    lat: float
    lon: float
    alt_m: float | None = None


class UAVTelemetry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    drone_id: str
    timestamp: datetime
    position: GeoPoint
    heading_deg: float
    speed_kmh: float
    mode: Literal["recon", "fpv", "loiter"]
    detections: list[Detection] = []


class Detection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    position: GeoPoint
    category: Literal["vehicle", "person", "structure", "unknown"]
    confidence: float  # 0.0–1.0
    source: str


class SatellitePass(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    satellite: str
    timestamp: datetime
    bbox: tuple[float, float, float, float]  # min_lon, min_lat, max_lon, max_lat
    resolution_m: float
    detections: list[Detection] = []


class SignalIntercept(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    position: GeoPoint
    frequency_mhz: float
    signal_type: Literal["radio", "radar", "jamming", "datalink"]
    strength_dbm: float
    bearing_deg: float | None = None


class RadarTrack(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    position: GeoPoint
    velocity_kmh: float
    heading_deg: float
    rcs_m2: float  # radar cross section — proxy for target size


class NATOReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    classification: Literal["UNCLASSIFIED", "RESTRICTED", "CONFIDENTIAL"]
    stanag_type: Literal["4559", "2525"]
    originator: str
    summary: str
    tracks: list[RadarTrack] = []


class CivilianReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    position: GeoPoint
    description: str
    verified: bool
    confidence: float
    source: Literal["osint", "verified_user", "ngo"]


class FusedTrack(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    position: GeoPoint
    category: str
    contributing_sources: list[str]
    confidence: float


class EntitySnapshot(BaseModel):
    id: str
    name: str
    entity_type: str
    faction: str
    wave: int
    status: str
    position: GeoPoint
    heading_deg: float
    speed_kmh: float


class ScenarioStatus(BaseModel):
    elapsed_seconds: float
    scenario_duration_seconds: float
    loop_progress_pct: float
    time_scale: float
    current_wave: int
    total_entities: int
    active_by_type: dict[str, int]
    active_attackers: int
    active_defenders: int
