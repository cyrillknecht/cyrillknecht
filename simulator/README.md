# datasource-simulator

Simulated multi-source ISR data feeds (UAV, satellite, HUMINT, NATO intel, civilian reports) with a live COP map. Models a fictional 6-wave attack on Switzerland from Germany.

## Run

```bash
cd simulator
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Open **http://localhost:8000** for the live COP map.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /scenario/status` | Wave, elapsed, entity counts |
| `GET /scenario/entities` | All active entities with positions |
| `WS /scenario/stream` | Live 1 Hz entity feed |
| `POST /scenario/time_scale` | Change speed `{"scale": 60}` |
| `POST /scenario/reset` | Restart scenario |
| `GET /sources/uav/snapshot` | UAV telemetry |
| `GET /sources/satellite/passes` | Satellite detections |
| `GET /sources/humint/signals` | SIGINT intercepts |
| `GET /sources/humint/radar` | Radar tracks |
| `GET /sources/nato/reports` | NATO reports (needs `X-API-Key: test-nato-key-1`) |
| `GET /sources/civilian/reports` | OSINT / civilian sightings |
| `GET /sources/fused` | Fused track output |

## Waves

| Wave | T | Content |
|------|---|---------|
| 1 | T+0s | 25 cruise missiles, 6 ballistic missiles |
| 2 | T+120s | 10 fighters, 4 EW aircraft, 25 recon UAVs |
| 3 | T+300s | 14 attack aircraft, 50 FPV UAVs, 12 loitering munitions, 6 bombers |
| 4 | T+600s | 25 tanks, 35 APCs, 25 trucks, 16 helicopters |
| 5 | T+900s | 15 tanks, 25 APCs, 12 MLRS, 3 trains, 70 UAV swarm |
| 6 | T+1800s | 10 tanks, 20 APCs, 30 trucks, 2 trains, 30 UAVs |
| Defenders | T+180s | 12 Swiss F/A-18 interceptors + 5 SAM sites |

Full loop duration: ~41,300s. Use `time_scale=60` for an ~11 min loop.
