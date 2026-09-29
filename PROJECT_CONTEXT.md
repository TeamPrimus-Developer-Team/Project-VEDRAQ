# 🌊 Project VEDRAQ — Permanent Repository Context Guide

> **Notice for AI Agents:** Read this file to obtain immediate, full context of Project VEDRAQ without re-reading source trees.

---

## 📌 1. System Overview
**VEDRAQ** (*Enabled Evaluation & Disaster Relocation*) is an end-to-end multi-hazard disaster decision-support platform. It processes spatial, meteorological, and field telemetry into prioritized, evidence-based evacuation and resource dispatch decisions following the pipeline:
**`Data ➔ Understanding ➔ Priority ➔ Action ➔ Feedback`**

- **Problem Addressed:** Proactive multi-hazard red-zoning, 29-indicator resettlement carrying capacity, altitudinal and flood-aware routing, closed-loop incident intelligence between ground responders and command center.
- **Key Scenarios:** 
  - **West Bengal / Bay of Bengal Coastal Belt (Primary GDG Showcase):** Cyclone, storm-surge inundation, and estuarine flooding across vulnerable coastal zones (Sundarbans, South 24 Parganas, Sagar Island, Haldia, Digha). Built for GEE elevation, land-cover, radar flood analysis, and real-time Bay of Bengal cyclone meteorology.
  - **Varanasi Riverine Flood (15 zones):** Inland Gangetic plain flood response.
  - **Nepal Mountainous Disaster:** High-altitude seismic & landslide response.
- **Status:** Functional prototype with synthetic demo data (not connected to live NDEM/government systems).

---

## 📂 2. Repository Layout & Component Map

```text
VEDRAQ/
├── 📱 VedraqApp/                      # Android Field Response Client (Kotlin, Jetpack Compose, Retrofit)
│   ├── app/src/main/java/com/vedraq/app/
│   │   ├── core/                     # LocationClient, NetworkModule, NetworkConfig, SyncManager
│   │   ├── data/                     # VedraqApiService, DTOs, Mappers, Repositories
│   │   ├── domain/                   # Incident, DisasterAlert, SosBeacon, TacticalFacility models
│   │   └── presentation/             # Jetpack Compose Screens (Home, Map, Alerts, Emergency, SOS)
│   └── build.gradle.kts              # Android build configuration (SDK 34)
│
├── ⚙️ vedraq-core/vedraq-core/         # Core Analytics Backend & Command Center
│   ├── backend/
│   │   ├── requirements.txt          # Python 3.10-3.14 compatible (fastapi, uvicorn, pydantic>=2.9, groq)
│   │   ├── app/
│   │   │   ├── main.py               # Master FastAPI application (~60 REST endpoints)
│   │   │   ├── models/               # Pydantic schemas (incident.py) & trained ML models
│   │   │   └── services/
│   │   │       ├── criticality.py    # Humanitarian Criticality Index (HCI 0-100) scoring
│   │   │       ├── routing.py        # Dijkstra road-network pathfinder + helicopter air-bridge
│   │   │       ├── resource_optimizer.py # Greedy inventory asset allocation
│   │   │       ├── evacuation.py     # Shelter capacity allocation & lifecycle state management
│   │   │       ├── evacuation_ml.py  # Tabular GBDT machine learning & XAI attributions
│   │   │       ├── groq_service.py   # Groq LLM integration (systemic risk & Q&A)
│   │   │       ├── incident_service.py # In-memory & synchronized incident store
│   │   │       ├── simulation.py     # What-If cascading disaster event processor
│   │   │       └── autonomous_sim.py # Multi-step autonomous Resolve-Then-Advance loop
│   │   └── tests/                    # 9 Pytest test suites covering all services
│   │
│   ├── frontend/
│   │   └── lifeline.html             # 520KB Leaflet GIS command center dashboard
│   │
│   ├── data/                         # Synthetic demo datasets
│   │   ├── zones.json                # 15 flood-affected sectors
│   │   ├── roads.json                # Road segment graph with status (OPEN/DEGRADED/BLOCKED)
│   │   ├── facilities.json           # Shelters, hospitals, depots, heliports
│   │   ├── resources.json            # 35 fleet assets (ambulances, water tankers, boats, helis)
│   │   ├── feedback_store.json       # Field response feedback logs for ML retraining
│   │   └── scenarios/                # "west_bengal" (flagship GDG scenario), "varanasi", "nepal"
│   │
│   ├── START_WINDOWS.ps1             # PowerShell 1-click startup script (venv + uvicorn)
│   └── START_WINDOWS.bat             # Batch launcher
│
├── .env.example                      # Environment variables template
├── PROJECT_CONTEXT.md                # Permanent root context for coding agents
└── README.md                         # Project documentation
```

---

## 🎯 3. Core Algorithms & Formulas

### A. Humanitarian Criticality Index (HCI)
Located in [`vedraq-core/vedraq-core/backend/app/services/criticality.py`](file:///d:/Projects/VEDRAQ/vedraq-core/vedraq-core/backend/app/services/criticality.py):
Produces a **0–100** score (100 = most critically underserved).
- **Weights:** Medical Access (0.20), Water Availability (0.18), Affected Population (0.15), Food Availability (0.12), Damage Severity (0.10), Shelter Access (0.10), Road Accessibility (0.10), Communication (0.05).
- **Thresholds:** CRITICAL ($\ge 80$), HIGH ($\ge 60$), MODERATE ($\ge 40$), LOWER ($< 40$).

### B. Resettlement Suitability Index (RSI - 29 Indicators)
Evaluates safe resettlement sites across 5 dimensions: Terrain Geological Stability (TGS), Natural Ecological Comfort (NEC), Economic Vitality (EDV), Transport Access (LTA), Public Service & Lifeline Redundancy (PSC).

### C. Dynamic Routing & Helicopter Fallback
Located in [`vedraq-core/vedraq-core/backend/app/services/routing.py`](file:///d:/Projects/VEDRAQ/vedraq-core/vedraq-core/backend/app/services/routing.py):
- Dijkstra pathfinding on road network graph.
- Automatically reroutes when links are tagged `BLOCKED` or `FLOODED`.
- Provides secondary alternate road corridors.
- If ground access is completely cut off, falls back to direct aerial air-bridge routing from the nearest helicopter base.

### D. Adaptive Tabular Evacuation ML & XAI
Located in [`vedraq-core/vedraq-core/backend/app/services/evacuation_ml.py`](file:///d:/Projects/VEDRAQ/vedraq-core/vedraq-core/backend/app/services/evacuation_ml.py):
- Decoupled from LLMs for numerical rigor.
- 21 engineered tabular features; Gradient Boosted Decision Tree (GBDT) model.
- Tree-path feature attribution Explainable AI (XAI).
- Controlled retraining incorporating field logs from `feedback_store.json`.

---

## 🌐 4. Essential API Endpoints

FastAPI server runs on `http://127.0.0.1:8001` (or `0.0.0.0:8001`):
- **Health & Scenarios:** `GET /api/health`, `GET /api/scenarios`, `POST /api/scenario/switch`
- **Zones & Criticality:** `GET /api/zones`, `GET /api/zones/{zone_id}`, `GET /api/priorities`
- **Infrastructure:** `GET /api/facilities`, `GET /api/roads`, `GET /api/resources`
- **Routing:** `GET /api/routes/{zone_id}`, `GET /api/routes/helicopter/{zone_id}`
- **Fleet Dispatch:** `POST /api/dispatch/send`, `GET /api/dispatch/active`, `POST /api/dispatch/{id}/update`
- **Field Incidents:** `POST /api/incidents`, `GET /api/incidents`, `PATCH /api/incidents/{id}`
- **Evacuation Plans:** `GET /api/evacuation/affected-zones`, `POST /api/evacuation/plan`, `POST /api/evacuation/step`
- **AI & Simulations:** `POST /api/ai/systemic-risk`, `POST /api/ai/ask`, `POST /api/ai/evacuation-priority`, `POST /api/simulation/autonomous/step`

---

## 🚀 5. Developer Quickstart

```powershell
# Backend
cd d:\Projects\VEDRAQ\vedraq-core\vedraq-core\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Dashboard
# Open http://localhost:8001/ or directly open lifeline.html in browser

# Test Suite
$env:PYTHONPATH="."
pytest -v
```
