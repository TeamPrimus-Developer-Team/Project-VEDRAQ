<div align="center">

# 🌊 VEDRAQ
### ⚡ **Enabled Evaluation & Disaster Relocation** ⚡

*A production-grade, multi-hazard disaster decision-support platform designed for emergency authorities and tactical response teams.*

---

[![GitHub License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&logo=open-source-initiative&logoColor=white)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PostGIS](https://img.shields.io/badge/PostGIS-Spatial_DB-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgis.net/)
[![Android](https://img.shields.io/badge/Android-FieldApp-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://developer.android.com/)
[![Groq AI](https://img.shields.io/badge/Groq-AI_LLM-F05032?style=for-the-badge&logo=brain&logoColor=white)](https://groq.com/)

---

### 🎯 **"Data → Understanding → Priority → Action → Feedback"**

[Explore Pipeline](#-core-decision-pipeline) • [System Architecture](#-system-architecture) • [Getting Started](#-getting-started) • [Tech Stack](#-technology-stack)

</div>

---

## 🧭 Core Decision Pipeline

```mermaid
flowchart LR
    H["🚨 HAZARD"] --> V["🔍 VULNERABILITY"]
    V --> C["📊 CRITICALITY"]
    C --> K["🏛️ CAPACITY"]
    K --> P["🏷️ PRIORITY"]
    P --> A["🚑 ACTION"]
    A --> R["🗺️ ROUTE"]
    R --> F["📱 FIELD FEEDBACK"]
    F -.->|Continuous Update| H

    style H fill:#ff4d4d,stroke:#990000,stroke-width:2px,color:#fff
    style V fill:#ff9933,stroke:#cc5200,stroke-width:2px,color:#fff
    style C fill:#e6b800,stroke:#997a00,stroke-width:2px,color:#000
    style K fill:#33cc33,stroke:#1f7a1f,stroke-width:2px,color:#fff
    style P fill:#3399ff,stroke:#0059b3,stroke-width:2px,color:#fff
    style A fill:#9933ff,stroke:#5c0099,stroke-width:2px,color:#fff
    style R fill:#00cc99,stroke:#00664d,stroke-width:2px,color:#fff
    style F fill:#ff3399,stroke:#99004d,stroke-width:2px,color:#fff

```

---

## 📌 Project Overview

**VEDRAQ** (*Enabled Evaluation & Disaster Relocation*) ek modern disaster decision-support ecosystem hai jo raw spatial aur meteorological data ko actionable ground intelligence mein convert karta hai.

Yeh simple static disaster mapping ke bajaye direct operational decision-making pipeline solve karta hai:

* 🚨 **Multi-Hazard Red-Zoning:** Real-time threat inputs se unsafe habitations pinpoint karna.


* 👥 **Grassroots Vulnerability:** Habitational structural profiling aur coping capacity assessment.


* 🏕️ **Relocation Carrying Capacity:** 29-indicator verified shelter site assessment.


* 🔀 **Dynamic Graph Routing:** Road blockage aur waterlogging-aware emergency corridor navigation.


* 🔄 **Closed-Loop Ground Intelligence:** Command Centre se Android field application (`VedraqApp`) ka live feedback link.



---

## ⚠️ Core Problem & Solutions

| ❌ Existing Emergency Deficits | ✅ VEDRAQ Solution Architecture |
| --- | --- |
| **Unsafe Habitations:** Families live in high-risk zones without proactive warnings.

 | **Dynamic Red-Zoning:** Automated AHP Multi-Hazard Indexing for immediate threat tagging.

 |
| **Reactive Decisions:** Evacuations begin only after damage occurs.

 | **Proactive Planning:** 48-hour proactive warning and planning horizons.

 |
| **Blind Relocations:** People sent to shelters without resource verification.

 | **29-Indicator Carrying Capacity:** Verifies water stock, solar microgrids, and triage beds.

 |
| **Static Navigation:** Standard GPS uses shortest roads, ignoring floods or landslides.

 | **Z-Axis Elevation & Graph Routing:** Altitudinal pathfinding avoiding blocked links.

 |

---

## ❓ Three Fundamental Questions

VEDRAQ directly answers three operational imperatives during any disaster:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. WHO should move first?     👉 Priority I Red-Zone vulnerable habitations │
│ 2. WHERE should they move?    👉 Verified high RSI safe-capacity shelters   │
│ 3. WHAT resources to deploy?  👉 Greedy-optimized priority asset dispatch   │
└─────────────────────────────────────────────────────────────────────────────┘

```

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Data_Ingestion ["📥 1. DATA INGESTION LAYER"]
        H1["☔ Rain Gauge / AWS Telemetry"]
        H2["🛰️ Satellite Inundation / GIS Boundaries"]
        H3["📝 Unstructured Field Logs"]
    end

    subgraph Core_Engine ["⚙️ 2. VEDRAQ CORE ANALYTICS BACKEND (FastAPI)"]
        direction TB
        M1["🚨 Hazard Intelligence Engine (AHP Multi-Hazard)"]
        M2["📊 Vulnerability Engine (CVI Indexing)"]
        M3["🎯 Humanitarian Criticality & Priority Engine"]
        M4["🏕️ Relocation & Capacity Engine (RSI 29 Indicators)"]
        M5["🔀 Dynamic Routing Engine (NetworkX / OSRM)"]
        M6["🤖 Groq AI LLM Field Data Structuring"]
    end

    subgraph Spatial_Database ["💾 3. GEOSPATIAL DATABASE STORAGE"]
        DB[("🐘 PostgreSQL + PostGIS<br/>Spatial Tables & Scenarios")]
    end

    subgraph Control_Center ["🖥️ 4. COMMAND CENTER DASHBOARD (React.js)"]
        UI1["🌍 3D CesiumJS / Mapbox Geospatial Viewer"]
        UI2["📊 Priority Action Matrix"]
        UI3["🔄 What-If Simulation Workbench"]
    end

    subgraph Field_App ["📱 5. ON-GROUND FIELD RESPONSE"]
        APP["📱 VedraqApp (Android Field Client)"]
        LOG["🚧 Road Blockage / Damage Telemetry"]
    end

    H1 --> M1
    H2 --> M1
    H3 --> M6
    M1 --> M2
    M2 --> DB
    DB --> M3
    M3 --> M4
    M4 --> M5
    M5 --> UI1
    M5 --> UI2
    M6 --> UI2
    UI3 -->|Scenario Repath| M5
    
    APP -->|Logs Ground Intelligence| LOG
    LOG -->|Closed-Loop Feedback| M1

```

---

## 🧩 Core Modules

### 1. 🚨 Multi-Hazard Intelligence

Combines hazard-related vectors using an Analytic Hierarchy Process (AHP) Multi-Hazard Index ($MHI$) approach to identify high-risk areas:

$$MHI = \frac{H_f + H_l + H_{fi}}{3}$$

*(Where $H_f$ = Flood Height, $H_l$ = Landslide Susceptibility, $H_{fi}$ = Urban Fire Spread)*

### 2. 👥 Grassroots Vulnerability Assessment

Evaluates population vulnerability across Social, Economic, and Environmental dimensions using the JRC Composite Vulnerability Index (CVI).

### 3. 📊 Humanitarian Criticality Index

Calculates intervention urgency by combining population affected, vulnerability profiles, hazard severity, infrastructure accessibility, and live field intelligence.

### 4. 🏕️ Relocation & Carrying Capacity

Evaluates safe resettlement sites using 29 distinct indicators across 5 dimensions via the Resettlement Suitability Index ($RSI$):

$$RSI = a_8 \cdot TGS + b_8 \cdot NEC + c_8 \cdot EDV + d_8 \cdot LTA + e_8 \cdot PSC$$

* **TGS:** Terrain Geological Stability


* **NEC:** Natural Ecological Comfort


* **EDV:** Economic Vitality


* **LTA:** Transport Access


* **PSC:** Public Service & Lifeline Redundancy (Solar microgrids, water stocks, triage beds)



### 5. 🚑 Resource Optimisation

Deploy resources systematically based on urgency:

```text
Priority Area Identified ➔ Resource Need Calculated ➔ Asset Inventory Matched ➔ Optimised Deployment

```

### 6. 🔀 Dynamic Routing & Z-Axis Elevation

Uses NetworkX and OSRM graph modeling to recalculate routes dynamically based on flood elevations and road blockages:

```mermaid
graph LR
    A["Start Node"] --> B{"Road Flood Check"}
    B -->|Waterlogged| C["Dynamic Detour Route - Safe Corridor"]
    B -->|Clear| D["Shortest Path - Direct Route"]
    C --> E["Destination Shelter"]
    D --> E

```

### 7. 🧪 Cascading What-If Simulation

Models various emergency scenarios:

* *What if a key bridge collapses?*

* *What if shelter capacity drops by 50%?*
* *What if flood levels rise past safe thresholds?*

---

## 📱 Field Intelligence — `VedraqApp`

The `VedraqApp/` directory contains an Android application designed for ground response teams. It enables real-time reporting of road conditions, shelter statuses, and local hazards directly to the central command dashboard.

```mermaid
sequenceDiagram
    autonumber
    actor Dashboard as Command Dashboard
    actor App as VedraqApp
    actor Team as Ground Team
    participant Core as VEDRAQ Core Backend

    Dashboard->>App: Deploy Evacuation Task
    App->>Team: View Tactical Route & Objectives
    Team-->>App: Log Road Blockage / Flooding
    App->>Core: Push Real-Time Ground Intelligence
    Core->>Dashboard: Update Maps & Re-route Units

```

---

## 🤖 AI Intelligence Layer

VEDRAQ includes **Groq-powered LLM capabilities** to process unstructured reports, ground telemetry, and incoming emergency logs.

> **Note:** The AI layer acts strictly as an assistive tool to process unstructured data; official operational decisions remain with authorized personnel.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| --- | --- |
| **Frontend** | React.js, Mapbox GL JS, Leaflet, CesiumJS (3D Spatial Viewer)

 |
| **Backend** | FastAPI, Uvicorn (ASGI Async Engine)

 |
| **Database** | PostgreSQL, PostGIS (Geospatial Extensions)

 |
| **Routing** | NetworkX, OSRM, OpenStreetMap Graph Topologies

 |
| **Field Client** | Android App (`VedraqApp`)

 |
| **AI Workflows** | Groq-powered LLM Processing

 |
| **Testing** | Pytest (Automated Engine Testing)

 |

---

## 📂 Repository Structure

```text
VEDRAQ/
├── 📱 VedraqApp/                # Android field-response application
│   ├── app/                    # Source files and user interfaces
│   └── gradle/                 # Gradle build files
│
├── ⚙️ vedraq-core/               # Core decision platform
│   └── vedraq-core/
│       ├── 🐍 backend/          # FastAPI server & route solvers
│       │   └── tests/          # Pytest unit & integration tests
│       │
│       ├── 💻 frontend/         # React.js operations dashboard
│       │   └── assets/         # Map styles and UI assets
│       │
│       ├── 📊 data/             # System datasets
│       │   ├── roads.json      # Network graph data
│       │   ├── resources.json  # Serialized asset inventory
│       │   ├── facilities.json # Shelter infrastructure database
│       │   └── scenarios/      # Simulation presets
│       │
│       ├── .env.example        # Environment configuration template
│       └── README.md           # Core module setup docs
│
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project documentation

```

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* Node.js & npm
* PostgreSQL with PostGIS extension
* Android Studio (optional, for field app compilation)

### Quick Installation

```bash
# Clone the repository
git clone [https://github.com/YuvrajSaxena2512/VEDRAQ.git](https://github.com/YuvrajSaxena2512/VEDRAQ.git)
cd VEDRAQ

```

#### Backend Setup

```bash
cd vedraq-core/vedraq-core/backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
# source venv/bin/activate

pip install -r requirements.txt

```

Create a `.env` file using `.env.example`:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/vedraq_db

```

Run the backend server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000

```

#### Frontend Setup

```bash
cd ../frontend
npm install
npm run dev

```

#### Android Field App

Open `VedraqApp/` in Android Studio, sync Gradle files, and build the project.

---

## 📊 Prototype Performance Targets

*Note: The targets below represent design goals for prototype validation:*

* **Proactive Warning Window:** Up to 48-hour planning horizon.


* **Evacuation Routing Target:** Designed for high-success altitudinal pathfinding.


* **Response Loop Compression:** Targeted 30-minute operational decision loop.


* **Carrying Capacity Index:** 29 verified relocation indicators.



---

## 🔮 Future Scope

* Live IoT sensor and weather telemetry integrations.
* Multimodal field input processing (audio, image, and text).
* Offline-first sync capabilities for `VedraqApp` in remote zones.
* Regional disaster digital twin modeling for retrospective analysis.

---

## 💡 Design Philosophy

> **VEDRAQ converts raw disaster data into structured operational steps:**
> **DATA $\rightarrow$ UNDERSTANDING $\rightarrow$ PRIORITY $\rightarrow$ ACTION $\rightarrow$ FEEDBACK**
> *The goal is explainable, evidence-driven decision support.*

---

## 📄 Disclaimer

VEDRAQ is a decision-support prototype built for disaster management simulation and research. Operational decisions in real-world scenarios should always be validated alongside certified local authorities and official meteorological advisories.

---

**Built and Maintained by the VEDRAQ Core Engineering Team**
