"""UAV feed simulator — drones performing random-walk recon over Switzerland."""
import random
import math
from datetime import datetime, timezone
from src.models import UAVTelemetry, Detection, GeoPoint
from src.geo import random_swiss_point, clamp_to_switzerland, random_near


class DroneState:
    def __init__(self, drone_id: str, mode: str):
        self.drone_id = drone_id
        self.mode = mode
        lat, lon = random_swiss_point()
        self.lat = lat
        self.lon = lon
        self.alt_m = random.uniform(100, 1500)
        self.heading = random.uniform(0, 360)
        self.speed_kmh = random.uniform(40, 120) if mode == "recon" else random.uniform(80, 160)

    def step(self) -> UAVTelemetry:
        # Gentle random walk on heading
        self.heading += random.uniform(-15, 15)
        self.heading %= 360

        # Move in heading direction (approx degrees per step at this speed)
        step_deg = self.speed_kmh / 111000 * 10  # ~10s step
        rad = math.radians(self.heading)
        self.lat += step_deg * math.cos(rad)
        self.lon += step_deg * math.sin(rad)
        self.lat, self.lon = clamp_to_switzerland(self.lat, self.lon)
        self.alt_m = max(50, self.alt_m + random.uniform(-20, 20))

        detections = []
        if random.random() < 0.3:
            dlat, dlon = random_near(self.lat, self.lon, 0.01)
            detections.append(Detection(
                timestamp=datetime.now(timezone.utc),
                position=GeoPoint(lat=dlat, lon=dlon, alt_m=0),
                category=random.choice(["vehicle", "person", "structure", "unknown"]),
                confidence=round(random.uniform(0.5, 0.98), 2),
                source=self.drone_id,
            ))

        return UAVTelemetry(
            drone_id=self.drone_id,
            timestamp=datetime.now(timezone.utc),
            position=GeoPoint(lat=round(self.lat, 6), lon=round(self.lon, 6), alt_m=round(self.alt_m, 1)),
            heading_deg=round(self.heading, 1),
            speed_kmh=round(self.speed_kmh, 1),
            mode=self.mode,
            detections=detections,
        )


DRONES: dict[str, DroneState] = {
    "UAV-01": DroneState("UAV-01", "recon"),
    "UAV-02": DroneState("UAV-02", "recon"),
    "FPV-01": DroneState("FPV-01", "fpv"),
    "FPV-02": DroneState("FPV-02", "fpv"),
    "UAV-03": DroneState("UAV-03", "loiter"),
}


def get_snapshot() -> list[UAVTelemetry]:
    return [state.step() for state in DRONES.values()]


def get_drone(drone_id: str) -> UAVTelemetry | None:
    state = DRONES.get(drone_id)
    return state.step() if state else None
