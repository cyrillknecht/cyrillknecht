"""Define all entity spawns for the 6-wave attack scenario."""
from __future__ import annotations
import random
from src.entities.base import Entity
from src.geo import GERMAN_STAGING, CROSSING_POINTS, SWISS_TARGETS, SWISS_DEFENDER_SITES

random.seed(42)

SPECS: dict[str, dict] = {
    "cruise_missile":       {"speed_ms": 220,  "alt_m": 80},
    "ballistic_missile":    {"speed_ms": 1500, "alt_m": 60000},
    "fighter_jet":          {"speed_ms": 280,  "alt_m": 8000},
    "attack_aircraft":      {"speed_ms": 200,  "alt_m": 300},
    "ew_aircraft":          {"speed_ms": 200,  "alt_m": 8000},
    "bomber":               {"speed_ms": 180,  "alt_m": 10000},
    "helicopter_attack":    {"speed_ms": 70,   "alt_m": 50},
    "helicopter_transport": {"speed_ms": 60,   "alt_m": 100},
    "uav_recon":            {"speed_ms": 50,   "alt_m": 1000},
    "uav_fpv":              {"speed_ms": 30,   "alt_m": 30},
    "uav_loiter":           {"speed_ms": 40,   "alt_m": 500},
    "tank":                 {"speed_ms": 12,   "alt_m": 0},
    "apc":                  {"speed_ms": 15,   "alt_m": 0},
    "truck":                {"speed_ms": 18,   "alt_m": 0},
    "mlrs":                 {"speed_ms": 10,   "alt_m": 0},
    "train":                {"speed_ms": 40,   "alt_m": 0},
    "interceptor":          {"speed_ms": 350,  "alt_m": 9000},
    "sam_site":             {"speed_ms": 0,    "alt_m": 0},
}

# Corridor assignments: (staging_key, crossing_key)
CORRIDORS = [
    ("western_freiburg",  "western_basel"),
    ("central_stuttgart", "central_schaffhausen"),
    ("eastern_munich",    "eastern_kreuzlingen"),
]

MISSILE_LAUNCHES = [
    GERMAN_STAGING["missile_launch_w"],
    GERMAN_STAGING["missile_launch_c"],
    GERMAN_STAGING["missile_launch_e"],
]

TARGET_LIST = list(SWISS_TARGETS.values())
TARGET_NAMES = list(SWISS_TARGETS.keys())

_entity_counter: dict[str, int] = {}


def _next_name(prefix: str) -> str:
    _entity_counter[prefix] = _entity_counter.get(prefix, 0) + 1
    return f"{prefix}-{_entity_counter[prefix]:02d}"


def _jitter(lat: float, lon: float, radius: float = 0.05) -> tuple[float, float]:
    return (lat + random.uniform(-radius, radius), lon + random.uniform(-radius, radius))


def _air_waypoints(
    launch: tuple[float, float],
    crossing: tuple[float, float],
    target: tuple[float, float],
    alt_m: float,
) -> list[tuple[float, float, float]]:
    return [
        (launch[0], launch[1], alt_m),
        (crossing[0], crossing[1], alt_m),
        (target[0], target[1], alt_m),
    ]


def _ballistic_waypoints(
    launch: tuple[float, float],
    target: tuple[float, float],
) -> list[tuple[float, float, float]]:
    apex_lat = (launch[0] + target[0]) / 2
    apex_lon = (launch[1] + target[1]) / 2
    return [
        (launch[0], launch[1], 0),
        (apex_lat, apex_lon, 60000),
        (target[0], target[1], 0),
    ]


def _ground_waypoints(
    staging: tuple[float, float],
    crossing: tuple[float, float],
    target: tuple[float, float],
) -> list[tuple[float, float, float]]:
    # Intermediate road waypoints
    mid1 = ((staging[0] + crossing[0]) / 2, (staging[1] + crossing[1]) / 2)
    mid2 = ((crossing[0] + target[0]) / 2, (crossing[1] + target[1]) / 2)
    return [
        (staging[0], staging[1], 0),
        (mid1[0], mid1[1], 0),
        (crossing[0], crossing[1], 0),
        (mid2[0], mid2[1], 0),
        (target[0], target[1], 0),
    ]


def _train_waypoints(
    staging: tuple[float, float],
    crossing: tuple[float, float],
    target: tuple[float, float],
) -> list[tuple[float, float, float]]:
    return [
        (staging[0], staging[1], 0),
        (crossing[0], crossing[1], 0),
        (target[0], target[1], 0),
    ]


def _pick_corridor(i: int) -> tuple[tuple[float, float], tuple[float, float]]:
    s_key, c_key = CORRIDORS[i % 3]
    staging = GERMAN_STAGING[s_key]
    crossing = CROSSING_POINTS[c_key]
    return staging, crossing


def _spawn_attacker(
    entity_type: str,
    prefix: str,
    wave: int,
    spawn_time: float,
    waypoints: list[tuple[float, float, float]],
) -> Entity:
    eid = f"{entity_type}_{wave}_{_entity_counter.get(prefix, 0) + 1}"
    name = _next_name(prefix)
    spec = SPECS[entity_type]
    return Entity(
        id=eid,
        name=name,
        entity_type=entity_type,
        faction="attacker",
        spawn_time=spawn_time,
        waypoints=waypoints,
        speed_ms=spec["speed_ms"],
        wave=wave,
    )


def build_wave_1(entities: list[Entity]):
    t = 0.0
    ab_targets = [
        SWISS_TARGETS["payerne_ab"],
        SWISS_TARGETS["meiringen_ab"],
        SWISS_TARGETS["sion_ab"],
        SWISS_TARGETS["dubendorf"],
        SWISS_TARGETS["zurich"],
    ]

    # 25 cruise missiles
    for i in range(25):
        launch = MISSILE_LAUNCHES[i % 3]
        launch_j = _jitter(*launch, 0.1)
        corridor_crossing = list(CROSSING_POINTS.values())[i % 3]
        target = ab_targets[i % len(ab_targets)]
        target_j = _jitter(*target, 0.03)
        wps = _air_waypoints(launch_j, corridor_crossing, target_j, SPECS["cruise_missile"]["alt_m"])
        entities.append(_spawn_attacker("cruise_missile", "WOLF", 1, t, wps))

    # 6 ballistic missiles
    bm_targets = [
        SWISS_TARGETS["payerne_ab"],
        SWISS_TARGETS["meiringen_ab"],
        SWISS_TARGETS["dubendorf"],
        SWISS_TARGETS["zurich"],
        SWISS_TARGETS["bern"],
        SWISS_TARGETS["sion_ab"],
    ]
    for i in range(6):
        launch = MISSILE_LAUNCHES[i % 3]
        launch_j = _jitter(*launch, 0.1)
        target = bm_targets[i]
        wps = _ballistic_waypoints(launch_j, target)
        entities.append(_spawn_attacker("ballistic_missile", "STORM", 1, t, wps))


def build_wave_2(entities: list[Entity]):
    t = 120.0

    # 10 fighter jets
    for i in range(10):
        staging, crossing = _pick_corridor(i)
        staging_j = _jitter(*staging, 0.1)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        target_j = _jitter(*target, 0.05)
        wps = _air_waypoints(staging_j, crossing, target_j, SPECS["fighter_jet"]["alt_m"])
        entities.append(_spawn_attacker("fighter_jet", "VIPER", 2, t, wps))

    # 4 EW aircraft
    for i in range(4):
        staging, crossing = _pick_corridor(i)
        staging_j = _jitter(*staging, 0.1)
        # EW aircraft orbit near border
        orbit = _jitter(*crossing, 0.15)
        wps = [
            (staging_j[0], staging_j[1], SPECS["ew_aircraft"]["alt_m"]),
            (crossing[0], crossing[1], SPECS["ew_aircraft"]["alt_m"]),
            (orbit[0], orbit[1], SPECS["ew_aircraft"]["alt_m"]),
        ]
        entities.append(_spawn_attacker("ew_aircraft", "JAMMER", 2, t, wps))

    # 25 recon UAVs
    for i in range(25):
        staging, crossing = _pick_corridor(i)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        target_j = _jitter(*target, 0.08)
        wps = _air_waypoints(_jitter(*staging, 0.1), crossing, target_j, SPECS["uav_recon"]["alt_m"])
        entities.append(_spawn_attacker("uav_recon", "EYE", 2, t, wps))


def build_wave_3(entities: list[Entity]):
    t = 300.0

    # 14 attack aircraft
    for i in range(14):
        staging, crossing = _pick_corridor(i)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        target_j = _jitter(*target, 0.04)
        wps = _air_waypoints(_jitter(*staging, 0.1), crossing, target_j, SPECS["attack_aircraft"]["alt_m"])
        entities.append(_spawn_attacker("attack_aircraft", "RAPTOR", 3, t, wps))

    # 50 FPV UAVs
    for i in range(50):
        staging, crossing = _pick_corridor(i)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        target_j = _jitter(*target, 0.06)
        wps = _air_waypoints(_jitter(*staging, 0.05), crossing, target_j, SPECS["uav_fpv"]["alt_m"])
        entities.append(_spawn_attacker("uav_fpv", "DART", 3, t, wps))

    # 12 loitering munitions
    for i in range(12):
        launch = MISSILE_LAUNCHES[i % 3]
        launch_j = _jitter(*launch, 0.08)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        target_j = _jitter(*target, 0.05)
        crossing = list(CROSSING_POINTS.values())[i % 3]
        wps = _air_waypoints(launch_j, crossing, target_j, SPECS["uav_loiter"]["alt_m"])
        entities.append(_spawn_attacker("uav_loiter", "BLADE", 3, t, wps))

    # 6 bombers
    for i in range(6):
        staging, crossing = _pick_corridor(i)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        wps = _air_waypoints(_jitter(*staging, 0.15), crossing, _jitter(*target, 0.03), SPECS["bomber"]["alt_m"])
        entities.append(_spawn_attacker("bomber", "TITAN", 3, t, wps))


def build_wave_4(entities: list[Entity]):
    t = 600.0
    ground_targets = [
        SWISS_TARGETS["basel"],
        SWISS_TARGETS["zurich"],
        SWISS_TARGETS["bern"],
        SWISS_TARGETS["lucerne"],
        SWISS_TARGETS["dubendorf"],
    ]

    # 25 tanks
    for i in range(25):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        target_j = _jitter(*target, 0.05)
        staging_j = _jitter(*staging, 0.08)
        crossing_j = _jitter(*crossing, 0.03)
        wps = _ground_waypoints(staging_j, crossing_j, target_j)
        entities.append(_spawn_attacker("tank", "PANZER", 4, t, wps))

    # 35 APCs
    for i in range(35):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        staging_j = _jitter(*staging, 0.08)
        crossing_j = _jitter(*crossing, 0.03)
        wps = _ground_waypoints(staging_j, crossing_j, _jitter(*target, 0.05))
        entities.append(_spawn_attacker("apc", "LYNX", 4, t, wps))

    # 25 trucks
    for i in range(25):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        staging_j = _jitter(*staging, 0.08)
        crossing_j = _jitter(*crossing, 0.03)
        wps = _ground_waypoints(staging_j, crossing_j, _jitter(*target, 0.06))
        entities.append(_spawn_attacker("truck", "SUPPLY", 4, t, wps))

    # 10 attack helicopters
    for i in range(10):
        staging, crossing = _pick_corridor(i)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        wps = _air_waypoints(_jitter(*staging, 0.1), crossing, _jitter(*target, 0.04), SPECS["helicopter_attack"]["alt_m"])
        entities.append(_spawn_attacker("helicopter_attack", "WASP", 4, t, wps))

    # 6 transport helicopters
    for i in range(6):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        wps = _air_waypoints(_jitter(*staging, 0.1), crossing, _jitter(*target, 0.04), SPECS["helicopter_transport"]["alt_m"])
        entities.append(_spawn_attacker("helicopter_transport", "CONDOR", 4, t, wps))


def build_wave_5(entities: list[Entity]):
    t = 900.0
    ground_targets = [
        SWISS_TARGETS["bern"],
        SWISS_TARGETS["zurich"],
        SWISS_TARGETS["lucerne"],
        SWISS_TARGETS["sion_ab"],
        SWISS_TARGETS["geneva"],
    ]

    # 15 tanks
    for i in range(15):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        wps = _ground_waypoints(_jitter(*staging, 0.06), _jitter(*crossing, 0.03), _jitter(*target, 0.05))
        entities.append(_spawn_attacker("tank", "PANZER", 5, t, wps))

    # 25 APCs
    for i in range(25):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        wps = _ground_waypoints(_jitter(*staging, 0.06), _jitter(*crossing, 0.03), _jitter(*target, 0.05))
        entities.append(_spawn_attacker("apc", "LYNX", 5, t, wps))

    # 12 MLRS
    for i in range(12):
        staging, crossing = _pick_corridor(i)
        # MLRS stops near border to fire
        fire_pos = _jitter(*crossing, 0.1)
        wps = [
            (_jitter(*staging, 0.06)[0], _jitter(*staging, 0.06)[1], 0),
            (fire_pos[0], fire_pos[1], 0),
        ]
        entities.append(_spawn_attacker("mlrs", "ROCKET", 5, t, wps))

    # 3 logistics trains
    train_routes = [
        (GERMAN_STAGING["western_freiburg"], CROSSING_POINTS["western_basel"], SWISS_TARGETS["basel"]),
        (GERMAN_STAGING["central_stuttgart"], CROSSING_POINTS["central_schaffhausen"], SWISS_TARGETS["zurich"]),
        (GERMAN_STAGING["eastern_munich"], CROSSING_POINTS["eastern_kreuzlingen"], SWISS_TARGETS["dubendorf"]),
    ]
    for i, (staging, crossing, target) in enumerate(train_routes):
        wps = _train_waypoints(staging, crossing, target)
        entities.append(_spawn_attacker("train", "CARGO", 5, t, wps))

    # 70 UAV swarm
    for i in range(70):
        staging, crossing = _pick_corridor(i)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        target_j = _jitter(*target, 0.08)
        wps = _air_waypoints(_jitter(*staging, 0.05), crossing, target_j, SPECS["uav_fpv"]["alt_m"])
        entities.append(_spawn_attacker("uav_fpv", "SWARM", 5, t, wps))


def build_wave_6(entities: list[Entity]):
    t = 1800.0
    ground_targets = [
        SWISS_TARGETS["geneva"],
        SWISS_TARGETS["bern"],
        SWISS_TARGETS["zurich"],
        SWISS_TARGETS["lucerne"],
    ]

    # 10 tanks
    for i in range(10):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        wps = _ground_waypoints(_jitter(*staging, 0.07), _jitter(*crossing, 0.03), _jitter(*target, 0.05))
        entities.append(_spawn_attacker("tank", "PANZER", 6, t, wps))

    # 20 APCs
    for i in range(20):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        wps = _ground_waypoints(_jitter(*staging, 0.07), _jitter(*crossing, 0.03), _jitter(*target, 0.05))
        entities.append(_spawn_attacker("apc", "LYNX", 6, t, wps))

    # 30 trucks
    for i in range(30):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        wps = _ground_waypoints(_jitter(*staging, 0.07), _jitter(*crossing, 0.03), _jitter(*target, 0.06))
        entities.append(_spawn_attacker("truck", "SUPPLY", 6, t, wps))

    # 2 trains
    for i in range(2):
        staging, crossing = _pick_corridor(i)
        target = ground_targets[i % len(ground_targets)]
        wps = _train_waypoints(staging, crossing, target)
        entities.append(_spawn_attacker("train", "CARGO", 6, t, wps))

    # 30 UAVs
    for i in range(30):
        staging, crossing = _pick_corridor(i)
        target = TARGET_LIST[i % len(TARGET_LIST)]
        wps = _air_waypoints(_jitter(*staging, 0.05), crossing, _jitter(*target, 0.06), SPECS["uav_recon"]["alt_m"])
        entities.append(_spawn_attacker("uav_recon", "EYE", 6, t, wps))


def build_defenders(entities: list[Entity]):
    # T=180: 8 F/A-18 interceptors from Payerne and Meiringen
    payerne = SWISS_DEFENDER_SITES["payerne_fa18"]
    meiringen = SWISS_DEFENDER_SITES["meiringen_fa18"]

    intercept_headings_w = (47.5, 7.3)   # toward western border
    intercept_headings_c = (47.6, 8.3)   # toward central border
    intercept_headings_e = (47.6, 9.0)   # toward eastern border

    patrol_points = [intercept_headings_w, intercept_headings_c, intercept_headings_e]

    for i in range(4):
        patrol = patrol_points[i % 3]
        wps = [
            (payerne[0], payerne[1], SPECS["interceptor"]["alt_m"]),
            (patrol[0], patrol[1], SPECS["interceptor"]["alt_m"]),
        ]
        e = Entity(
            id=f"interceptor_def_{i+1}",
            name=f"EAGLE-{i+1:02d}",
            entity_type="interceptor",
            faction="defender",
            spawn_time=180.0,
            waypoints=wps,
            speed_ms=SPECS["interceptor"]["speed_ms"],
            wave=0,
        )
        entities.append(e)

    for i in range(4):
        patrol = patrol_points[i % 3]
        wps = [
            (meiringen[0], meiringen[1], SPECS["interceptor"]["alt_m"]),
            (patrol[0], patrol[1], SPECS["interceptor"]["alt_m"]),
        ]
        e = Entity(
            id=f"interceptor_def_{i+5}",
            name=f"EAGLE-{i+5:02d}",
            entity_type="interceptor",
            faction="defender",
            spawn_time=180.0,
            waypoints=wps,
            speed_ms=SPECS["interceptor"]["speed_ms"],
            wave=0,
        )
        entities.append(e)

    # T=180: 4 more F/A-18s
    for i in range(4):
        patrol = patrol_points[i % 3]
        base = payerne if i % 2 == 0 else meiringen
        wps = [
            (base[0], base[1], SPECS["interceptor"]["alt_m"]),
            (patrol[0] + 0.1, patrol[1] + 0.1, SPECS["interceptor"]["alt_m"]),
        ]
        e = Entity(
            id=f"interceptor_def_{i+9}",
            name=f"HAWK-{i+1:02d}",
            entity_type="interceptor",
            faction="defender",
            spawn_time=180.0,
            waypoints=wps,
            speed_ms=SPECS["interceptor"]["speed_ms"],
            wave=0,
        )
        entities.append(e)

    # T=180: 6 SAM sites (static)
    sam_sites = [
        ("sam_zurich",  "SAM-ZURICH"),
        ("sam_bern",    "SAM-BERN"),
        ("sam_geneva",  "SAM-GENEVA"),
        ("sam_sion",    "SAM-SION"),
        ("sam_basel",   "SAM-BASEL"),
    ]
    for i, (site_key, site_name) in enumerate(sam_sites):
        pos = SWISS_DEFENDER_SITES[site_key]
        wps = [(pos[0], pos[1], 0)]
        e = Entity(
            id=f"sam_site_{i+1}",
            name=site_name,
            entity_type="sam_site",
            faction="defender",
            spawn_time=180.0,
            waypoints=wps,
            speed_ms=0.0,
            wave=0,
        )
        entities.append(e)

    # T=700: 4 more interceptors
    for i in range(4):
        patrol = patrol_points[i % 3]
        base = payerne if i % 2 == 0 else meiringen
        wps = [
            (base[0], base[1], SPECS["interceptor"]["alt_m"]),
            (patrol[0], patrol[1] - 0.2, SPECS["interceptor"]["alt_m"]),
        ]
        e = Entity(
            id=f"interceptor_def_{i+13}",
            name=f"FALCON-{i+1:02d}",
            entity_type="interceptor",
            faction="defender",
            spawn_time=700.0,
            waypoints=wps,
            speed_ms=SPECS["interceptor"]["speed_ms"],
            wave=0,
        )
        entities.append(e)


def build_all_entities() -> list[Entity]:
    _entity_counter.clear()
    entities: list[Entity] = []
    build_wave_1(entities)
    build_wave_2(entities)
    build_wave_3(entities)
    build_wave_4(entities)
    build_wave_5(entities)
    build_wave_6(entities)
    build_defenders(entities)
    return entities
