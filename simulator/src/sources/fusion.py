"""Track fusion — merges detections from all sources into unified tracks."""
import random
from datetime import datetime, timezone
from src.models import FusedTrack, GeoPoint
from src.sources import uav, satellite, humint, civilian


def get_fused_tracks(n: int = 50) -> list[FusedTrack]:
    tracks: list[FusedTrack] = []

    for telem in uav.get_snapshot():
        for det in telem.detections:
            tracks.append(FusedTrack(
                timestamp=det.timestamp,
                position=det.position,
                category=det.category,
                contributing_sources=[telem.drone_id],
                confidence=det.confidence,
            ))

    for sat_pass in satellite.get_latest(5):
        for det in sat_pass.detections:
            tracks.append(FusedTrack(
                timestamp=det.timestamp,
                position=det.position,
                category=det.category,
                contributing_sources=[sat_pass.satellite],
                confidence=det.confidence,
            ))

    for radar in humint.get_radar_tracks(10):
        tracks.append(FusedTrack(
            timestamp=radar.timestamp,
            position=radar.position,
            category="vehicle" if radar.rcs_m2 > 1 else "unknown",
            contributing_sources=["radar"],
            confidence=round(min(0.99, 0.5 + radar.rcs_m2 / 100), 2),
        ))

    for rep in civilian.get_reports(10, verified_only=True):
        tracks.append(FusedTrack(
            timestamp=rep.timestamp,
            position=rep.position,
            category="unknown",
            contributing_sources=[rep.source],
            confidence=rep.confidence,
        ))

    # Deduplicate by proximity: very naive — just shuffle and cap
    random.shuffle(tracks)
    return tracks[:n]
