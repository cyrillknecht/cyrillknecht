from __future__ import annotations
import math
from dataclasses import dataclass, field

DLAT_M = 111_000.0
DLON_M = 75_700.0  # cos(47°) * 111_000


def _segment_length_m(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    dlat = (b[0] - a[0]) * DLAT_M
    dlon = (b[1] - a[1]) * DLON_M
    dalt = b[2] - a[2]
    return math.sqrt(dlat ** 2 + dlon ** 2 + dalt ** 2)


def _heading_between(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    dlat = (b[0] - a[0]) * DLAT_M
    dlon = (b[1] - a[1]) * DLON_M
    angle = math.degrees(math.atan2(dlon, dlat)) % 360
    return angle


@dataclass
class Entity:
    id: str
    name: str
    entity_type: str
    faction: str  # "attacker" | "defender"
    spawn_time: float
    waypoints: list[tuple[float, float, float]]  # (lat, lon, alt_m)
    speed_ms: float
    wave: int
    status: str = "pending"

    # precomputed segment lengths (filled on first use)
    _seg_lengths: list[float] = field(default_factory=list, repr=False)
    _total_length: float = field(default=0.0, repr=False)

    def _ensure_segments(self):
        if not self._seg_lengths and len(self.waypoints) >= 2:
            self._seg_lengths = [
                _segment_length_m(self.waypoints[i], self.waypoints[i + 1])
                for i in range(len(self.waypoints) - 1)
            ]
            self._total_length = sum(self._seg_lengths)

    def position_at(self, t: float) -> tuple[float, float, float] | None:
        if t < self.spawn_time:
            return None

        self._ensure_segments()

        if not self.waypoints:
            return None

        if len(self.waypoints) == 1:
            return self.waypoints[0]

        elapsed_since_spawn = t - self.spawn_time
        distance_covered = elapsed_since_spawn * self.speed_ms

        if distance_covered >= self._total_length:
            return self.waypoints[-1]

        remaining = distance_covered
        for i, seg_len in enumerate(self._seg_lengths):
            if remaining <= seg_len:
                frac = remaining / seg_len if seg_len > 0 else 1.0
                a = self.waypoints[i]
                b = self.waypoints[i + 1]
                lat = a[0] + frac * (b[0] - a[0])
                lon = a[1] + frac * (b[1] - a[1])
                alt = a[2] + frac * (b[2] - a[2])
                return (lat, lon, alt)
            remaining -= seg_len

        return self.waypoints[-1]

    def heading_at(self, t: float) -> float:
        if t < self.spawn_time or len(self.waypoints) < 2:
            return 0.0

        self._ensure_segments()
        elapsed_since_spawn = t - self.spawn_time
        distance_covered = elapsed_since_spawn * self.speed_ms

        remaining = distance_covered
        for i, seg_len in enumerate(self._seg_lengths):
            if remaining <= seg_len:
                a = self.waypoints[i]
                b = self.waypoints[i + 1]
                return _heading_between(a, b)
            remaining -= seg_len

        # Arrived — return heading of last segment
        return _heading_between(self.waypoints[-2], self.waypoints[-1])

    def is_arrived(self, t: float) -> bool:
        if t < self.spawn_time:
            return False
        self._ensure_segments()
        elapsed_since_spawn = t - self.spawn_time
        distance_covered = elapsed_since_spawn * self.speed_ms
        return distance_covered >= self._total_length
