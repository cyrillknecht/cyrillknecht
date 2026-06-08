"""HUMINT / SIGINT / radar simulator."""
import random
from datetime import datetime, timezone
from src.models import SignalIntercept, RadarTrack, GeoPoint
from src.geo import random_swiss_point, random_near, AREAS

SIGNAL_TYPES = ["radio", "radar", "jamming", "datalink"]

_intercepts: list[SignalIntercept] = []
_tracks: list[RadarTrack] = []
MAX_HISTORY = 100


def _gen_intercept() -> SignalIntercept:
    lat, lon = random_swiss_point()
    return SignalIntercept(
        timestamp=datetime.now(timezone.utc),
        position=GeoPoint(lat=round(lat, 6), lon=round(lon, 6)),
        frequency_mhz=round(random.uniform(30, 3000), 2),
        signal_type=random.choice(SIGNAL_TYPES),
        strength_dbm=round(random.uniform(-110, -40), 1),
        bearing_deg=round(random.uniform(0, 360), 1) if random.random() > 0.4 else None,
    )


def _gen_radar_track() -> RadarTrack:
    _, (clat, clon) = random.choice(list(AREAS.items()))
    tlat, tlon = random_near(clat, clon, 0.15)
    return RadarTrack(
        timestamp=datetime.now(timezone.utc),
        position=GeoPoint(lat=round(tlat, 6), lon=round(tlon, 6), alt_m=round(random.uniform(0, 8000), 0)),
        velocity_kmh=round(random.uniform(0, 900), 1),
        heading_deg=round(random.uniform(0, 360), 1),
        rcs_m2=round(random.uniform(0.01, 50), 3),
    )


def get_intercepts(n: int = 20) -> list[SignalIntercept]:
    while len(_intercepts) < n:
        _intercepts.insert(0, _gen_intercept())
    new = [_gen_intercept() for _ in range(random.randint(1, 3))]
    _intercepts[:0] = new
    del _intercepts[MAX_HISTORY:]
    return _intercepts[:n]


def get_radar_tracks(n: int = 20) -> list[RadarTrack]:
    while len(_tracks) < n:
        _tracks.insert(0, _gen_radar_track())
    new = [_gen_radar_track() for _ in range(random.randint(1, 4))]
    _tracks[:0] = new
    del _tracks[MAX_HISTORY:]
    return _tracks[:n]
