"""Singleton scenario engine — manages scenario time and entity state."""
from __future__ import annotations
from datetime import datetime, timezone
from src.entities.base import Entity
from src.scenario.waves import build_all_entities

# Total scenario duration: time at which the last entity reaches its target.
# Computed once from the wave data; engine auto-loops when elapsed exceeds this.
_SCENARIO_DURATION: float | None = None


def _compute_duration(entities: list[Entity]) -> float:
    end = 0.0
    for e in entities:
        e._ensure_segments()
        travel = e._total_length / e.speed_ms if e.speed_ms > 0 else 0.0
        end = max(end, e.spawn_time + travel)
    return end


class ScenarioEngine:
    _instance: ScenarioEngine | None = None

    def __init__(self):
        self.time_scale: float = 1.0
        self.start_wall_time: datetime = datetime.now(timezone.utc)
        self.entities: list[Entity] = []
        self._duration: float = 0.0
        self._load_entities()

    @classmethod
    def get(cls) -> ScenarioEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_entities(self):
        self.entities = build_all_entities()
        self._duration = _compute_duration(self.entities)

    @property
    def elapsed(self) -> float:
        delta = (datetime.now(timezone.utc) - self.start_wall_time).total_seconds()
        raw = delta * self.time_scale
        # Auto-loop: wrap elapsed time within scenario duration
        if self._duration > 0:
            return raw % self._duration
        return raw

    def reset(self, time_scale: float = 1.0):
        self.time_scale = time_scale
        self.start_wall_time = datetime.now(timezone.utc)
        self._load_entities()

    def set_time_scale(self, scale: float):
        # Preserve elapsed scenario time across scale change
        current_elapsed = self.elapsed
        self.time_scale = scale
        delta_wall = current_elapsed / scale if scale != 0 else 0
        from datetime import timedelta
        self.start_wall_time = datetime.now(timezone.utc) - timedelta(seconds=delta_wall)

    def active_entities(self) -> list[Entity]:
        t = self.elapsed
        return [e for e in self.entities if e.spawn_time <= t]

    def snapshot(self) -> list[dict]:
        t = self.elapsed
        result = []
        for e in self.entities:
            if e.spawn_time > t:
                continue
            pos = e.position_at(t)
            if pos is None:
                continue
            heading = e.heading_at(t)
            arrived = e.is_arrived(t)
            status = "arrived" if arrived else "active"
            result.append({
                "id": e.id,
                "name": e.name,
                "entity_type": e.entity_type,
                "faction": e.faction,
                "wave": e.wave,
                "status": status,
                "position": {"lat": round(pos[0], 6), "lon": round(pos[1], 6), "alt_m": round(pos[2], 1)},
                "heading_deg": round(heading, 1),
                "speed_kmh": round(e.speed_ms * 3.6, 1),
            })
        return result

    def status(self) -> dict:
        t = self.elapsed
        active = self.active_entities()

        active_by_type: dict[str, int] = {}
        for e in active:
            active_by_type[e.entity_type] = active_by_type.get(e.entity_type, 0) + 1

        active_attackers = sum(1 for e in active if e.faction == "attacker")
        active_defenders = sum(1 for e in active if e.faction == "defender")

        # Determine current wave based on elapsed time
        wave_times = [0, 120, 300, 600, 900, 1800]
        current_wave = 0
        for i, wt in enumerate(wave_times):
            if t >= wt:
                current_wave = i + 1

        return {
            "elapsed_seconds": round(t, 2),
            "scenario_duration_seconds": round(self._duration, 2),
            "loop_progress_pct": round(t / self._duration * 100, 1) if self._duration else 0,
            "time_scale": self.time_scale,
            "current_wave": current_wave,
            "total_entities": len(self.entities),
            "active_by_type": active_by_type,
            "active_attackers": active_attackers,
            "active_defenders": active_defenders,
        }
