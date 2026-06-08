"""Civilian / OSINT report simulator."""
import random
from datetime import datetime, timezone
from src.models import CivilianReport, GeoPoint
from src.geo import random_swiss_point, random_near, AREAS, CIVILIAN_DESCRIPTIONS

_reports: list[CivilianReport] = []
MAX_HISTORY = 200
SOURCES = ["osint", "verified_user", "ngo"]


def _gen_report() -> CivilianReport:
    if random.random() < 0.7:
        _, (clat, clon) = random.choice(list(AREAS.items()))
        lat, lon = random_near(clat, clon, 0.2)
    else:
        lat, lon = random_swiss_point()

    verified = random.random() > 0.4
    return CivilianReport(
        timestamp=datetime.now(timezone.utc),
        position=GeoPoint(lat=round(lat, 6), lon=round(lon, 6)),
        description=random.choice(CIVILIAN_DESCRIPTIONS),
        verified=verified,
        confidence=round(random.uniform(0.6, 0.95) if verified else random.uniform(0.2, 0.6), 2),
        source=random.choice(SOURCES),
    )


def get_reports(n: int = 30, verified_only: bool = False) -> list[CivilianReport]:
    while len(_reports) < n:
        _reports.insert(0, _gen_report())
    new = [_gen_report() for _ in range(random.randint(1, 5))]
    _reports[:0] = new
    del _reports[MAX_HISTORY:]
    result = _reports[:n * 3]
    if verified_only:
        result = [r for r in result if r.verified]
    return result[:n]
