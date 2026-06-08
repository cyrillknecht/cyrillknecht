"""Satellite pass simulator — periodic imagery snapshots over Swiss areas."""
import random
from datetime import datetime, timezone
from src.models import SatellitePass, Detection, GeoPoint
from src.geo import AREAS, SATELLITE_NAMES, random_near, random_swiss_point

# History of last N passes, newest first
_passes: list[SatellitePass] = []
MAX_HISTORY = 50


def _generate_pass() -> SatellitePass:
    satellite = random.choice(SATELLITE_NAMES)
    center_name, (clat, clon) = random.choice(list(AREAS.items()))
    spread = 0.3
    min_lon = round(clon - spread, 4)
    min_lat = round(clat - spread, 4)
    max_lon = round(clon + spread, 4)
    max_lat = round(clat + spread, 4)

    num_detections = random.randint(0, 6)
    detections = []
    for _ in range(num_detections):
        dlat, dlon = random_near(clat, clon, spread * 0.8)
        detections.append(Detection(
            timestamp=datetime.now(timezone.utc),
            position=GeoPoint(lat=round(dlat, 6), lon=round(dlon, 6), alt_m=0),
            category=random.choice(["vehicle", "structure", "unknown"]),
            confidence=round(random.uniform(0.55, 0.99), 2),
            source=satellite,
        ))

    return SatellitePass(
        satellite=satellite,
        timestamp=datetime.now(timezone.utc),
        bbox=(min_lon, min_lat, max_lon, max_lat),
        resolution_m=round(random.uniform(0.3, 3.0), 2),
        detections=detections,
    )


def refresh() -> SatellitePass:
    """Generate a new pass and push it into history."""
    p = _generate_pass()
    _passes.insert(0, p)
    if len(_passes) > MAX_HISTORY:
        _passes.pop()
    return p


def get_latest(n: int = 10) -> list[SatellitePass]:
    while len(_passes) < min(n, 5):
        refresh()
    return _passes[:n]
