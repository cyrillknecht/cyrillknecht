"""NATO intel report simulator (STANAG-style)."""
import random
from datetime import datetime, timezone
from src.models import NATOReport, RadarTrack, GeoPoint
from src.geo import NATO_ORIGINATORS, NATO_SUMMARIES, random_swiss_point

_reports: list[NATOReport] = []
MAX_HISTORY = 30
CLASSIFICATIONS = ["UNCLASSIFIED", "RESTRICTED", "CONFIDENTIAL"]
STANAG_TYPES = ["4559", "2525"]


def _gen_report() -> NATOReport:
    num_tracks = random.randint(0, 4)
    tracks = []
    for _ in range(num_tracks):
        lat, lon = random_swiss_point()
        tracks.append(RadarTrack(
            timestamp=datetime.now(timezone.utc),
            position=GeoPoint(lat=round(lat, 6), lon=round(lon, 6), alt_m=round(random.uniform(0, 10000), 0)),
            velocity_kmh=round(random.uniform(0, 800), 1),
            heading_deg=round(random.uniform(0, 360), 1),
            rcs_m2=round(random.uniform(0.1, 40), 3),
        ))
    return NATOReport(
        timestamp=datetime.now(timezone.utc),
        classification=random.choice(CLASSIFICATIONS),
        stanag_type=random.choice(STANAG_TYPES),
        originator=random.choice(NATO_ORIGINATORS),
        summary=random.choice(NATO_SUMMARIES),
        tracks=tracks,
    )


def get_reports(n: int = 10, api_key: str | None = None) -> list[NATOReport]:
    if not api_key:
        raise PermissionError("NATO feed requires API key")
    while len(_reports) < n:
        _reports.insert(0, _gen_report())
    new = [_gen_report() for _ in range(random.randint(0, 2))]
    _reports[:0] = new
    del _reports[MAX_HISTORY:]
    return _reports[:n]
