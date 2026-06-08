"""Switzerland bounding box and movement helpers."""
import random
import math

# Switzerland approximate bounds
LAT_MIN, LAT_MAX = 45.8, 47.8
LON_MIN, LON_MAX = 5.9, 10.5

# German staging / launch areas
GERMAN_STAGING = {
    "western_freiburg":   (48.00, 7.85),
    "central_stuttgart":  (48.77, 9.18),
    "eastern_munich":     (48.14, 11.58),
    "missile_launch_w":   (49.00, 8.50),
    "missile_launch_c":   (49.20, 9.00),
    "missile_launch_e":   (49.10, 10.00),
}

# Border crossing points
CROSSING_POINTS = {
    "western_basel":       (47.56, 7.59),
    "central_schaffhausen":(47.70, 8.63),
    "eastern_kreuzlingen": (47.66, 9.18),
}

# Swiss targets
SWISS_TARGETS = {
    "payerne_ab":   (46.843, 6.917),
    "meiringen_ab": (46.742, 8.110),
    "sion_ab":      (46.221, 7.327),
    "dubendorf":    (47.398, 8.621),
    "zurich":       (47.376, 8.541),
    "bern":         (46.948, 7.447),
    "basel":        (47.559, 7.588),
    "lucerne":      (47.050, 8.310),
    "geneva":       (46.204, 6.143),
}

# Swiss defender positions
SWISS_DEFENDER_SITES = {
    "payerne_fa18":  (46.843, 6.917),
    "meiringen_fa18":(46.742, 8.110),
    "sam_zurich":    (47.40, 8.55),
    "sam_bern":      (46.93, 7.45),
    "sam_geneva":    (46.22, 6.15),
    "sam_sion":      (46.22, 7.35),
    "sam_basel":     (47.55, 7.58),
}

# Named areas of interest (cities / military zones)
AREAS = {
    "zurich": (47.376, 8.541),
    "bern": (46.948, 7.447),
    "geneva": (46.204, 6.143),
    "basel": (47.559, 7.588),
    "lucerne": (47.050, 8.310),
    "sion": (46.233, 7.360),
    "chur": (46.850, 9.532),
    "thun": (46.758, 7.629),
}

SATELLITE_NAMES = ["Maxar-WV3", "Maxar-WV2", "Planet-SkySat", "Planet-Dove"]
NATO_ORIGINATORS = ["CHE-J2", "NATO-SHAPE", "DEU-BND-LNO", "FRA-DRM-LNO"]

CIVILIAN_DESCRIPTIONS = [
    "Unusual vehicle convoy observed near forest road",
    "Low-flying aircraft reported by multiple witnesses",
    "Bridge access restricted, military presence noted",
    "Unidentified drone activity over industrial area",
    "Road closure with uniformed personnel at checkpoint",
    "Explosion sound reported, no visual confirmation",
    "Supply trucks observed moving toward northern border",
]

NATO_SUMMARIES = [
    "Track correlation update: 3 new air contacts over Alpine corridor",
    "SIGINT activity elevated in sector 7, possible EW deployment",
    "Ground movement detected near logistics node, 12 vehicles",
    "Airspace deconfliction required for rotary assets in TMA Zurich",
    "Partner feed confirms radar track ID 4421 as friendly rotary",
    "Cyber anomaly detected in partner network, investigation ongoing",
]


def random_swiss_point() -> tuple[float, float]:
    return (
        random.uniform(LAT_MIN, LAT_MAX),
        random.uniform(LON_MIN, LON_MAX),
    )


def random_near(lat: float, lon: float, radius_deg: float = 0.05) -> tuple[float, float]:
    angle = random.uniform(0, 2 * math.pi)
    dist = random.uniform(0, radius_deg)
    return (
        lat + dist * math.cos(angle),
        lon + dist * math.sin(angle),
    )


def clamp_to_switzerland(lat: float, lon: float) -> tuple[float, float]:
    return (
        max(LAT_MIN, min(LAT_MAX, lat)),
        max(LON_MIN, min(LON_MAX, lon)),
    )
