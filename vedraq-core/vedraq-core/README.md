# VEDRAQ Core — Disaster Intelligence and Simulation Engine

VEDRAQ Core provides deterministic scenario, hazard criticality, route,
resource, evacuation, and optional AI capabilities for the VEDRAQ APP backend.
All bundled scenarios are synthetic demonstration data; this project does not
claim a connection to government, NDEM, or live emergency systems.

## Runtime relationship

The APP backend discovers the sibling `vedraq-core` directory and loads its
services in process through `core_adapter.py`. That is the normal local setup.
The standalone HTTP service is optional for developing or inspecting Core. The
React Native Web frontend uses the APP backend at `/api/v1`, not this service.

## Setup and run

Core has a separately pinned FastAPI/Pydantic stack. Create a separate Python
3.13 environment; do not reuse the APP backend environment.

```bash
cd vedraq-core/backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python -m pytest -q

# Optional standalone Core service
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

`./scripts/setup.sh` creates both APP and Core environments. It uses
`python3.13` for Core by default; set `CORE_PYTHON` to a Python 3.13 executable
only when necessary.

## Standalone HTTP endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Service and deterministic-routing health |
| `GET /api/zones` | Active scenario zones and HCI data |
| `GET /api/routes/{zone_id}` | Road-graph route and alternate route |
| `GET /api/priorities` | Current priority ranking |
| `GET /api/recommendations` | Resource allocation recommendations |
| `GET /api/scenarios` | Available synthetic scenarios |
| `POST /api/scenario/switch` | Switch the in-memory Core scenario |
| `GET /api/ai/status` | Groq/deterministic AI availability |

The standalone process binds to `127.0.0.1` by default because its simulation
state-changing endpoints do not implement an external authentication boundary.
Put an authenticated gateway in front of it before any network deployment.

## VEDRAQ routing

Set `OSRM_ENDPOINT` to an OSRM-compatible base URL to enable live OpenStreetMap road geometry. Without it, VEDRAQ uses its deterministic local road graph and clearly displays: "Live road routing unavailable — using demo road graph." This ensures road closures, alternative routes, distance, and ETA remain demonstrable offline.

## Project Structure

```
vedraq-core/
│
├── README.md
│
├── backend/
│   ├── requirements.txt      ← Python 3.13 compatible deps
│   └── app/
│       ├── main.py           ← FastAPI app + all endpoints
│       └── services/
│           ├── criticality.py        ← HCI scoring engine
│           ├── routing.py            ← Dijkstra pathfinder
│           ├── resource_optimizer.py ← Greedy allocation
│           └── simulation.py         ← What-if engine
│
├── data/
│   ├── zones.json            ← 15 synthetic flood zones
│   ├── roads.json            ← Synthetic roads with status
│   ├── facilities.json       ← Hospitals, shelters, depot
│   └── resources.json        ← Resource inventory
│
└── frontend/                 ← Optional Leaflet command-center assets
```

---

## Dependencies (Python 3.13 compatibility)

| Package | Version | Reason |
|---------|---------|--------|
| fastapi | 0.111.0 | Unchanged |
| uvicorn | 0.29.0 | Unchanged |
| pydantic | **2.8.2** | Fixed from 2.7.1 |

**Root cause:** `pydantic==2.7.1` pulls `pydantic-core==2.18.x` which has no
prebuilt Windows/cp313 wheel → pip tries Rust build → fails.
`pydantic==2.8.2` pulls `pydantic-core==2.20.1` which HAS a prebuilt
`cp313-win_amd64.whl` → no Rust needed → installs instantly.

---

## External configuration

Copy `vedraq-core/.env.example` to `vedraq-core/.env` only when configuration
is needed. `GROQ_API_KEY` is optional: without it, Core starts normally and
reports `needs_api_key`, then uses deterministic analysis rather than claiming
that an AI response was generated. `OSRM_ENDPOINT` and `CARTO_API_KEY` are
optional. Never commit a populated `.env` file.

## HCI Formula

```
HCI = Σ (component × weight)

affected_population  × 0.15
damage_severity      × 0.10
medical_access       × 0.20  ← highest weight
water_availability   × 0.18
food_availability    × 0.12
shelter_access       × 0.10
road_accessibility   × 0.10
communication        × 0.05

Score: 0-100  (100 = most critically underserved)
```

---

## Disclaimer
Synthetic demo data. No NDEM/ISRO/government integration claimed.
HCI weights are prototype values, not scientifically validated.
