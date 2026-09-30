"""
VEDRAQ — Humanitarian Intelligence & Resource Optimization
FastAPI Backend — Python 3.13 Compatible
================================================================
DISCLAIMER: This prototype uses synthetic demo data.
It does not claim integration with NDEM or any government system.
"""

import json
import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import List, Dict, Any, Optional

import urllib.request
import urllib.error
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env from root or backend directory
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv()

logger = logging.getLogger("vedraq.main")

from app.services.criticality import classify_all_zones, compute_hci
from app.services.routing import (
    compute_all_routes, find_route, get_road_geometry, RoutingService, haversine
)
from app.services.resource_optimizer import build_recommendations
from app.services.simulation import SimulationState, get_cyclone_presets
from app.services import gee_service
from app.services.weather_service import weather_service
from app.services.risk_engine import risk_engine
from app.services.gemini_service import (
    build_systemic_risk_context,
    analyze_systemic_risk,
    query_ai,
    get_ai_status,
    generate_disaster_advisory,
)
from app.services.autonomous_sim import (
    execute_autonomous_step,
    run_full_autonomous_simulation,
    get_unresolved_critical_areas,
)
from app.services.evacuation import (
    extend_affected_zone,
    upgrade_safe_zone,
    calculate_evacuation_priority,
    rank_safe_zones_for_zone,
    allocate_evacuation_capacity,
    create_evacuation_plan,
    assign_resources_to_plan,
    update_evacuation_progress,
    reroute_evacuation_plan,
    handle_safe_zone_overflow,
    step_evacuation_simulation,
    calculate_evacuation_impact,
    LIFECYCLE_STATES,
    PASSENGER_CAPACITIES,
)
from app.services.evacuation_ml import (
    predict_evacuation_priority,
    get_model_info,
    log_evacuation_feedback,
    retrain_model_with_feedback,
    get_feedback_records,
)
from app.models.incident import (
    IncidentCreateRequest,
    IncidentStatusUpdateRequest,
    IncidentResponse,
    IncidentListResponse,
    IncidentStatus,
)
from app.services.incident_service import incident_store

AUTONOMOUS_SESSION: Dict[str, Any] = {
    "scenario_id": None,
    "selected_conditions": [],
    "events": [],
    "sim_state": None,
    "initial_state": None,
    "resolved_ids": set(),
    "history": [],
    "dispatched_vehicles": {},
}

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

AVAILABLE_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "west_bengal": {
        "id": "west_bengal",
        "name": "West Bengal Coastal Cyclone & Surge",
        "region": "Coastal West Bengal & Northern Bay of Bengal, India",
        "description": "Tropical cyclonic storm, 0-5m storm surge inundation, and estuarine flooding across vulnerable coastal communities (Sundarbans, Sagar Island, Kakdwip, Haldia, Digha)",
        "data_dir": DATA_DIR / "scenarios" / "west_bengal",
        "center": [21.95, 88.15],
        "zoom": 10,
        "zones_count": 15,
        "disclaimer": "Synthetic Demo Data — Calibrated for coastal Bengal disaster operations and GDG demonstration."
    },
    "varanasi": {
        "id": "varanasi",
        "name": "Varanasi District Flood",
        "region": "Uttar Pradesh, India",
        "description": "Monsoon riverine flood across 15 vulnerable riverbank and peri-urban sectors",
        "data_dir": DATA_DIR / "scenarios" / "varanasi" if (DATA_DIR / "scenarios" / "varanasi").exists() else DATA_DIR,
        "center": [25.315, 83.065],
        "zoom": 12,
        "zones_count": 15,
        "disclaimer": "Synthetic Demo Data — Not Real NDEM Data. All coordinates and routes are for the VEDRAQ prototype demonstration only."
    },
    "nepal": {
        "id": "nepal",
        "name": "Nepal Alpine Disaster",
        "region": "Bagmati & Sindhupalchok, Nepal",
        "description": "Alpine flash flood and seismic landslide isolating mountain valley communities",
        "data_dir": DATA_DIR / "scenarios" / "nepal",
        "center": [27.750, 85.550],
        "zoom": 11,
        "zones_count": 10,
        "disclaimer": "Synthetic Demo Data — Not Real NDEM Data. All coordinates and routes are for the VEDRAQ prototype demonstration only."
    }
}

CURRENT_SCENARIO_ID = "west_bengal"

def _load_scenario_json(scenario_id: str, filename: str) -> Any:
    sc_info = AVAILABLE_SCENARIOS.get(scenario_id, AVAILABLE_SCENARIOS["west_bengal"])
    sc_dir = sc_info["data_dir"]
    path = sc_dir / filename
    if not path.exists():
        path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def reload_current_scenario_baseline(scenario_id: str = None) -> None:
    global CURRENT_SCENARIO_ID, ZONES_BASELINE, ROADS_BASELINE, FACILITIES_BASELINE, RESOURCES_BASELINE, sim
    target_sc = scenario_id or CURRENT_SCENARIO_ID
    if target_sc not in AVAILABLE_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: '{target_sc}'. Available: {list(AVAILABLE_SCENARIOS.keys())}")
    CURRENT_SCENARIO_ID = target_sc
    ZONES_BASELINE      = _load_scenario_json(target_sc, "zones.json")
    ROADS_BASELINE      = _load_scenario_json(target_sc, "roads.json")
    FACILITIES_BASELINE = _load_scenario_json(target_sc, "facilities.json")
    RESOURCES_BASELINE  = _load_scenario_json(target_sc, "resources.json")
    
    sim = SimulationState(
        ZONES_BASELINE,
        ROADS_BASELINE,
        FACILITIES_BASELINE,
        RESOURCES_BASELINE,
    )

reload_current_scenario_baseline("west_bengal")
ROAD_GEOMETRY_CACHE: Dict[str, Dict[str, Any]] = {}
DISPATCHED_VEHICLES: Dict[str, Dict[str, Any]] = {}
ACTIVE_EVACUATION_PLANS: Dict[str, Dict[str, Any]] = {}

def switch_scenario(scenario_id: str) -> Dict[str, Any]:
    global CURRENT_SCENARIO_ID, ROAD_GEOMETRY_CACHE, DISPATCHED_VEHICLES, AUTONOMOUS_SESSION, ACTIVE_EVACUATION_PLANS
    if scenario_id not in AVAILABLE_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: '{scenario_id}'. Available: {list(AVAILABLE_SCENARIOS.keys())}")
    
    sc_info = AVAILABLE_SCENARIOS[scenario_id]
    CURRENT_SCENARIO_ID = scenario_id
    reload_current_scenario_baseline(scenario_id)
    ROAD_GEOMETRY_CACHE.clear()
    DISPATCHED_VEHICLES.clear()
    ACTIVE_EVACUATION_PLANS.clear()
    AUTONOMOUS_SESSION = {
        "scenario_id": None,
        "selected_conditions": [],
        "events": [],
        "sim_state": None,
        "initial_state": None,
        "resolved_ids": set(),
        "history": [],
        "dispatched_vehicles": {},
    }
    return {
        "status": "success",
        "scenario_id": scenario_id,
        "name": sc_info["name"],
        "region": sc_info["region"],
        "description": sc_info["description"],
        "center": sc_info["center"],
        "zoom": sc_info["zoom"],
        "zones_count": len(ZONES_BASELINE),
        "roads_count": len(ROADS_BASELINE),
        "disclaimer": sc_info["disclaimer"]
    }

app = FastAPI(
    title="VEDRAQ API",
    description="VEDRAQ — Humanitarian Intelligence & Resource Optimization",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    assests_dir = FRONTEND_DIR / "assests"
    if assests_dir.exists():
        app.mount("/assests", StaticFiles(directory=str(assests_dir)), name="assests")


class SimEvent(BaseModel):
    type: str
    road_id: Optional[str] = None
    facility_id: Optional[str] = None
    zone_id: Optional[str] = None
    shelter_id: Optional[str] = None
    safe_zone_id: Optional[str] = None
    road_ids: Optional[List[str]] = None
    unit_id: Optional[str] = None
    surge_pct: Optional[float] = None
    speed_multiplier: Optional[float] = None



class SimulationRequest(BaseModel):
    events: List[SimEvent]


class ParametricCycloneRequest(BaseModel):
    surge_height_m: Optional[float] = 3.0
    wind_speed_kmh: Optional[float] = 130.0
    rainfall_24h_mm: Optional[float] = 200.0
    breach_locations: Optional[List[str]] = None


class ScenarioSwitchRequest(BaseModel):
    scenario_id: str


class DispatchRequest(BaseModel):
    zone_id: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    origin_depot: Optional[str] = None


class RouteQuery(BaseModel):
    origin: str
    destination: str
    resource_type: Optional[str] = None
    resource_speed_kmh: Optional[float] = None
    excluded_roads: Optional[List[str]] = None


class SystemicRiskRequest(BaseModel):
    include_baseline: Optional[bool] = True


class AIQueryRequest(BaseModel):
    question: str
    include_baseline: Optional[bool] = True


class AdvisoryRequest(BaseModel):
    zone_id: Optional[str] = None
    language: Optional[str] = "both"


class AutonomousStepRequest(BaseModel):
    scenario_id: Optional[str] = None
    selected_conditions: Optional[List[str]] = None
    events: Optional[List[Dict[str, Any]]] = None
    reset_session: Optional[bool] = False


class AutonomousRunRequest(BaseModel):
    scenario_id: Optional[str] = None
    selected_conditions: Optional[List[str]] = None
    events: Optional[List[Dict[str, Any]]] = None
    max_steps: Optional[int] = 6


class AutonomousResetRequest(BaseModel):
    scenario_id: Optional[str] = None
    selected_conditions: Optional[List[str]] = None
    events: Optional[List[Dict[str, Any]]] = None


class EvacuationPriorityRequest(BaseModel):
    zone_id: Optional[str] = None
    zone: Optional[Dict[str, Any]] = None
    hci_score: Optional[float] = None
    disaster_type: Optional[str] = "flood"
    disaster_severity: Optional[float] = 0.75


class FeedbackLogRequest(BaseModel):
    zone_id: str
    predicted_priority: float
    action_taken: str
    actual_evacuated: int
    response_time_min: float
    notes: Optional[str] = ""


class RetrainRequest(BaseModel):
    n_samples: Optional[int] = 2500
    seed: Optional[int] = 42


class SafeZoneRecommendRequest(BaseModel):
    zone_id: str


class EvacuationPlanRequest(BaseModel):
    zone_id: str
    people_at_risk: Optional[int] = None
    auto_assign_resources: Optional[bool] = True


class EvacuationAssignRequest(BaseModel):
    plan_id: str
    resource_ids: Optional[List[str]] = None


class EvacuationProgressRequest(BaseModel):
    plan_id: str
    target_status: str
    people_delta: Optional[Dict[str, int]] = None
    note: Optional[str] = None


class EvacuationRouteScoreRequest(BaseModel):
    origin_zone_id: str
    dest_safe_zone_id: str
    vehicle_type: Optional[str] = "bus"
    excluded_road_ids: Optional[List[str]] = None


class EvacuationRerouteRequest(BaseModel):
    plan_id: str
    blocked_road_ids: Optional[List[str]] = None


class EvacuationOverflowRequest(BaseModel):
    plan_id: str
    overflow_safe_zone_id: str


class EvacuationStepRequest(BaseModel):
    plan_id: str
    elapsed_minutes: Optional[float] = 5.0
    vehicle_speed_factor: Optional[float] = 1.0



def _build_nodes() -> Dict[str, Dict]:
    nodes: Dict[str, Dict] = {z["id"]: z for z in sim.zones}
    if sim.facilities.get("depot"):
        nodes["DEPOT"] = sim.facilities["depot"]
    for d in sim.facilities.get("depots", []):
        nodes[d["id"]] = d
    for h in sim.facilities.get("hospitals", []):
        nodes[h["id"]] = h
    for s in sim.facilities.get("shelters", []):
        nodes[s["id"]] = s
    for b in sim.facilities.get("helicopter_bases", []):
        nodes[b["id"]] = b
    return nodes


def _resource_speed(resource_type: str, resource_id: str = None) -> Optional[float]:
    if resource_id:
        for u in (sim.resources.get("units") or []):
            if u["id"] == resource_id:
                return float(u.get("speed_kmh") or 0) or None
    inv = (sim.resources.get("inventory") or {}).get(resource_type) or {}
    return float(inv.get("avg_speed_kmh") or 0) or None


def _full_state() -> Dict[str, Any]:
    state = sim.compute_full_state(active_dispatches=list(DISPATCHED_VEHICLES.values()))
    state["active_evacuation_plans"] = list(ACTIVE_EVACUATION_PLANS.values())
    state["scenario_id"] = CURRENT_SCENARIO_ID
    return state


@app.get("/", include_in_schema=False)
def serve_dashboard():
    html_path = FRONTEND_DIR / "lifeline.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"message": "VEDRAQ API running. Open /docs for API documentation."}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "VEDRAQ",
        "data": "synthetic-demo",
        "routing": "Dijkstra road-graph with real geometry waypoints",
        "routing_engine": "road-graph-dijkstra",
    }


@app.get("/api/config/map")
def get_map_config():
    """Provides map tile configuration for Leaflet / OpenStreetMap (free, no API key required, zero watermarks)."""
    carto_key = os.getenv("CARTO_API_KEY", "").strip()
    map_provider = os.getenv("MAP_PROVIDER", "leaflet").strip().lower()

    if map_provider == "carto" and carto_key:
        tile_url = f"https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png?key={carto_key}"
        return {
            "provider": "carto",
            "has_key": True,
            "tile_url": tile_url,
            "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            "subdomains": "abcd",
            "max_zoom": 19,
            "dark_filter": False,
        }

    # Default: Standard Leaflet / OpenStreetMap tiles (100% free, open, no key, no watermark)
    return {
        "provider": "leaflet",
        "has_key": False,
        "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        "subdomains": "abc",
        "max_zoom": 19,
        "dark_filter": True,
    }


@app.get("/api/zones")
def get_zones():
    state = _full_state()
    return {"zones": state["zones"], "total": len(state["zones"])}


@app.get("/api/zones/{zone_id}")
def get_zone(zone_id: str):
    state = _full_state()
    zone = next((z for z in state["zones"] if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    route = state["routes"].get(zone_id, {})
    nodes = _build_nodes()
    service = RoutingService(sim.roads, nodes)
    best_depot = zone.get("best_depot") or "DEPOT"
    alt = None
    try:
        alt = service.get_alternative_route(best_depot, zone_id,
                                            resource_speed_kmh=_resource_speed("ambulance"))
    except Exception:
        pass
    return {
        **zone,
        "route_from_depot": route,
        "alternate_route": alt,
        "best_depot": best_depot,
        "nearest_accessible_hospital": zone.get("nearest_accessible_hospital"),
        "nearest_accessible_shelter": zone.get("nearest_accessible_shelter"),
    }


@app.get("/api/disaster-history/{zone_id}")
def get_disaster_history(zone_id: str, scenario_id: Optional[str] = None):
    req_sc = (scenario_id or CURRENT_SCENARIO_ID).lower()
    if "nepal" in req_sc:
        target_sc = "nepal"
    elif "varanasi" in req_sc:
        target_sc = "varanasi"
    else:
        target_sc = "west_bengal"

    try:
        history_data = _load_scenario_json(target_sc, "disaster_history.json")
    except Exception as e:
        logger.warning(f"Failed to load disaster history for {target_sc}: {e}")
        history_data = {}

    # Strict isolation between scenarios
    if target_sc == "west_bengal" and not zone_id.startswith("WB"):
        zone_history = []
    elif target_sc == "varanasi" and not zone_id.startswith("Z"):
        zone_history = []
    elif target_sc == "nepal" and not zone_id.startswith("N"):
        zone_history = []
    else:
        zone_history = history_data.get(zone_id, [])

    # Geographically sanitize for India / Varanasi
    if target_sc == "varanasi":
        zone_history = [
            ev for ev in zone_history
            if not any(f in (ev.get("type", "") + " " + ev.get("description", "")).lower()
                       for f in ["snow", "avalanche", "blizzard", "freeze", "frost", "glacial"])
        ]

    return {
        "zone_id": zone_id,
        "scenario_id": target_sc,
        "years_span": "2017-2026",
        "is_synthetic": True,
        "disclaimer": "Synthetic Demo Data for VEDRAQ prototype — Not verified historical data",
        "events": zone_history
    }


@app.get("/api/facilities")
def get_facilities():
    return sim.facilities


@app.get("/api/roads")
def get_roads():
    return {"roads": sim.roads}


@app.get("/api/roads/{road_id}/geometry")
def get_road_visual_geometry(road_id: str):
    road = next((r for r in sim.roads if r["id"] == road_id), None)
    if not road:
        raise HTTPException(status_code=404, detail=f"Road {road_id} not found")
    nodes = _build_nodes()
    cached = ROAD_GEOMETRY_CACHE.get(road_id)
    if cached:
        return {**cached, "status": road["status"]}
    result = get_road_geometry(road, nodes)
    if result.get("geometry"):
        ROAD_GEOMETRY_CACHE[road_id] = result
    return result


@app.get("/api/resources")
def get_resources():
    return sim.resources


@app.get("/api/priorities")
def get_priorities():
    state = _full_state()
    return {
        "priorities": [
            {
                "rank":               z["priority_rank"],
                "id":                 z["id"],
                "name":               z["name"],
                "hci_score":          z["hci_score"],
                "classification":     z["classification"],
                "affected_population":z["affected_population"],
                "bottlenecks":        z["bottlenecks"][:3],
                "best_depot":         z.get("best_depot"),
                "response_accessibility": z.get("response_accessibility"),
                "response_plan_mode": z.get("response_plan", {}).get("mode"),
            }
            for z in state["zones"]
        ]
    }


@app.get("/api/recommendations")
def get_recommendations():
    state = _full_state()
    return state["recommendations"]


@app.get("/api/routes/{zone_id}")
def get_zone_route(zone_id: str, origin: Optional[str] = None):
    # Retrieve dynamic routes through the simulation state helper
    return sim.get_zone_routes(zone_id, origin=origin)


@app.post("/api/routes/query")
def query_route(q: RouteQuery):
    nodes = _build_nodes()
    svc = RoutingService(sim.roads, nodes)
    speed = q.resource_speed_kmh or _resource_speed(q.resource_type or "")
    primary = svc.get_route(q.origin, q.destination, resource_speed_kmh=speed,
                            excluded_road_ids=q.excluded_roads, use_snap=True)
    alternate = None
    if primary["reachable"]:
        try:
            alternate = svc.get_alternative_route(q.origin, q.destination,
                                                   resource_speed_kmh=speed,
                                                   excluded_road_ids=q.excluded_roads)
        except Exception:
            alternate = None
    return {"primary": primary, "alternate": alternate}


@app.get("/api/routes/helicopter/{zone_id}")
def helicopter_route(zone_id: str, origin_base: Optional[str] = None):
    zone = next((z for z in sim.zones if z["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    bases = sim.facilities.get("helicopter_bases") or []
    heli_units = [u for u in (sim.resources.get("units") or [])
                  if u["type"] == "helicopter" and u["status"] == "AVAILABLE"]
    if not bases:
        raise HTTPException(status_code=404, detail="No helicopter bases available")
    if origin_base is None:
        if heli_units:
            origin_base = heli_units[0].get("base_id") or bases[0]["id"]
        else:
            origin_base = bases[0]["id"]
    base = next((b for b in bases if b["id"] == origin_base), bases[0])
    heli = heli_units[0] if heli_units else {"speed_kmh": 180, "id": "H01"}
    nodes = _build_nodes()
    svc = RoutingService(sim.roads, nodes)
    route = svc.get_helicopter_route(
        base["latitude"], base["longitude"],
        zone["latitude"], zone["longitude"],
        helicopter_speed_kmh=float(heli.get("speed_kmh", 180)),
    )
    return {
        "zone_id": zone_id,
        "zone_name": zone["name"],
        "base": base,
        "helicopter": {
            "id": heli.get("id"),
            "call_sign": heli.get("call_sign"),
            "crew": heli.get("crew"),
            "capacity": heli.get("capacity"),
        },
        "route": route,
    }


@app.get("/api/dispatch/allocation/{zone_id}")
def dispatch_allocation(zone_id: str, resource_type: str, needed: int = 1):
    nodes = _build_nodes()
    allocation = sim._multi_depot_allocation(zone_id, resource_type, needed, nodes)
    return {"zone_id": zone_id, "resource_type": resource_type,
            "needed": needed, "allocations": allocation}


@app.post("/api/dispatch/send")
def dispatch_vehicle(req: DispatchRequest):
    zone = next((z for z in sim.zones if z["id"] == req.zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {req.zone_id} not found")
    nodes = _build_nodes()
    svc = RoutingService(sim.roads, nodes)
    if req.resource_id:
        unit = next((u for u in (sim.resources.get("units") or [])
                     if u["id"] == req.resource_id), None)
        if not unit:
            raise HTTPException(status_code=404, detail=f"Resource {req.resource_id} not found")
        if unit.get("status") != "AVAILABLE":
            return {
                "status": "UNAVAILABLE",
                "reason": f"Resource unit {req.resource_id} is currently unavailable (status: {unit.get('status')}). Please wait for its return.",
                "zone_id": req.zone_id,
                "resource_id": req.resource_id,
            }
        rtype = unit["type"]
        rid = unit["id"]
        origin = unit.get("base_id") or req.origin_depot or "DEPOT"
        speed = float(unit.get("speed_kmh", 25))
    elif req.resource_type:
        rtype = req.resource_type
        origin = req.origin_depot or zone.get("best_depot") or "DEPOT"
        avail = [u for u in (sim.resources.get("units") or [])
                 if u["type"] == rtype and u["status"] == "AVAILABLE"
                 and (u.get("base_id") == origin if origin else True)]
        if not avail:
            avail = [u for u in (sim.resources.get("units") or [])
                     if u["type"] == rtype and u["status"] == "AVAILABLE"]
        if not avail:
            return {
                "status": "UNAVAILABLE",
                "reason": f"No available {rtype} units found in inventory. All units of this type are currently deployed or in maintenance — please wait for a unit to return.",
                "zone_id": req.zone_id,
                "resource_type": rtype,
            }
        unit = avail[0]
        rid = unit["id"]
        origin = unit.get("base_id") or origin
        speed = float(unit.get("speed_kmh", 25))
    else:
        raise HTTPException(status_code=400, detail="resource_id or resource_type is required")
    is_air = unit.get("mode") == "AIR" or rtype == "helicopter"
    if is_air:
        bases = sim.facilities.get("helicopter_bases") or []
        base = next((b for b in bases if b["id"] == unit.get("base_id")),
                    bases[0] if bases else None)
        if not base:
            raise HTTPException(status_code=400, detail="No helicopter base found")
        route = svc.get_helicopter_route(base["latitude"], base["longitude"],
                                          zone["latitude"], zone["longitude"],
                                          helicopter_speed_kmh=speed)
    else:
        three_routes = svc.get_three_routes(origin, req.zone_id, resource_speed_kmh=speed)
        if not three_routes.get("reachable"):
            return {
                "status": "GROUND_ACCESS_UNAVAILABLE",
                "reason": "ALL GROUND ROUTES BLOCKED — AERIAL RESPONSE REQUIRED",
                "recommendation": "EVALUATE HELICOPTER FALLBACK or alternate depot.",
                "all_blocked": True,
                "aerial_fallback_available": True,
                "zone_id": req.zone_id,
                "resource_type": rtype,
                "resource_id": rid,
            }
        route = three_routes["active_route"]
        def _route_summary(r):
            if not r: return None
            return {
                "path_type": r.get("path_type"),
                "road_ids": r.get("road_ids", []),
                "distance_km": r.get("distance_km"),
                "total_time_min": r.get("total_time_min"),
                "geometry": r.get("geometry", []),
                "reachable": r.get("reachable", True),
            }
        route["three_routes_bundle"] = {
            "active_path_type": three_routes.get("active_path_type", "PRIMARY"),
            "primary": _route_summary(three_routes.get("primary")),
            "alternate": _route_summary(three_routes.get("alternate")),
            "fallback": _route_summary(three_routes.get("fallback")),
        }
    DISPATCHED_VEHICLES[rid] = {
        "resource_id": rid,
        "resource_type": rtype,
        "mode": unit.get("mode", "GROUND"),
        "origin": origin,
        "zone_id": req.zone_id,
        "zone_name": zone["name"],
        "route": route,
        "distance_km": route.get("air_distance_km") if is_air else route.get("distance_km"),
        "eta_min": route.get("flight_time_min") if is_air else route.get("total_time_min"),
        "status": "EN_ROUTE",
        "dispatched_at": __import__("datetime").datetime.now().isoformat(),
        "progress_pct": 0,
        "is_air": is_air,
    }
    for u in sim.resources.get("units", []):
        if u["id"] == rid:
            u["status"] = "DEPLOYED"
            u["current_assignment"] = req.zone_id
    if sim.resources.get("inventory", {}).get(rtype):
        sim.resources["inventory"][rtype]["available"] = max(0,
            sim.resources["inventory"][rtype]["available"] - 1)
    res = {
        "status": "DISPATCHED",
        "resource_id": rid,
        "resource_type": rtype,
        "mode": unit.get("mode", "GROUND"),
        "origin": origin,
        "zone": {"id": zone["id"], "name": zone["name"]},
        "route": route,
        "distance_km": DISPATCHED_VEHICLES[rid]["distance_km"],
        "eta_min": DISPATCHED_VEHICLES[rid]["eta_min"],
        "avg_speed_kmh": route.get("avg_speed_kmh"),
    }

    # Mirror dispatch to Operations backend on port 8000 if active
    try:
        type_map = {
            "ambulance": "MEDICAL",
            "rescue_van": "RESCUE",
            "bus": "EVACUATION",
            "water_tanker": "WATER",
            "food_unit": "FOOD",
            "helicopter": "HELICOPTER",
        }
        op_payload = {
            "type": type_map.get(rtype, "RESCUE"),
            "zone_id": req.zone_id,
            "location_name": zone.get("name", req.zone_id),
            "latitude": zone.get("latitude"),
            "longitude": zone.get("longitude"),
            "assigned_vehicle_id": rid,
            "assigned_vehicle_type": rtype,
            "priority": "HIGH",
            "status": "DISPATCHED",
            "source": "VEDRAQ_CORE",
            "notes": f"Dispatched from Core Command Center to {zone.get('name', req.zone_id)}",
            "idempotency_key": f"core-dispatch-{rid}-{int(__import__('datetime').datetime.now().timestamp())}"
        }
        code, op_data = _proxy_to_operations("/api/operations", method="POST", data=json.dumps(op_payload).encode("utf-8"))
        if op_data and isinstance(op_data, dict) and "data" in op_data and "operationId" in op_data["data"]:
            op_id = op_data["data"]["operationId"]
            res["operation_id"] = op_id
            DISPATCHED_VEHICLES[rid]["operation_id"] = op_id
    except Exception as e:
        logger.debug(f"Could not mirror dispatch to port 8000 operations backend: {e}")

    return res


@app.get("/api/dispatch/active")
def get_active_dispatches():
    return {"dispatches": list(DISPATCHED_VEHICLES.values())}


@app.post("/api/dispatch/{resource_id}/update")
def update_dispatch_progress(resource_id: str, progress: int = 0):
    if resource_id not in DISPATCHED_VEHICLES:
        raise HTTPException(status_code=404, detail=f"Dispatch {resource_id} not found")
    DISPATCHED_VEHICLES[resource_id]["progress_pct"] = max(0, min(100, progress))
    if progress >= 100:
        DISPATCHED_VEHICLES[resource_id]["status"] = "ARRIVED"

    # Forward progress to port 8000 if operation_id is known
    op_id = DISPATCHED_VEHICLES[resource_id].get("operation_id") or resource_id
    try:
        new_status = "ARRIVED" if progress >= 100 else ("EN_ROUTE" if progress > 0 else "DISPATCHED")
        _proxy_to_operations(
            f"/api/operations/{op_id}/status",
            method="POST",
            data=json.dumps({
                "status": new_status,
                "notes": f"Vehicle reached {progress}% progress",
                "source": "VEDRAQ_CORE"
            }).encode("utf-8")
        )
    except Exception:
        pass

    return DISPATCHED_VEHICLES[resource_id]


# ═════════════════════════════════════════════════════════════════════════════
# OPERATIONS PROXY (Port 8001 -> Port 8000 Unified Hub)
# ═════════════════════════════════════════════════════════════════════════════
def _proxy_to_operations(path: str, method: str = "GET", data: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None) -> tuple[int, Any]:
    url = f"http://127.0.0.1:8000{path}"
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        for k, v in headers.items():
            if k.lower() not in ["host", "content-length"]:
                req_headers[k] = v
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err)
        except Exception:
            return e.code, {"detail": err}
    except Exception as e:
        return 503, {"detail": f"Operations backend on port 8000 unreachable: {e}"}


@app.api_route("/api/operations", methods=["GET", "POST"])
@app.api_route("/api/v1/operations", methods=["GET", "POST"])
async def proxy_operations_root(request: Request):
    body = await request.body()
    qs = str(request.query_params)
    path = f"/api/operations{f'?{qs}' if qs else ''}"
    code, data = _proxy_to_operations(path, method=request.method, data=body if body else None)
    return JSONResponse(status_code=code, content=data)


@app.api_route("/api/operations/{operation_id}", methods=["GET", "PATCH"])
@app.api_route("/api/v1/operations/{operation_id}", methods=["GET", "PATCH"])
async def proxy_operation_by_id(operation_id: str, request: Request):
    body = await request.body()
    code, data = _proxy_to_operations(f"/api/operations/{operation_id}", method=request.method, data=body if body else None)
    return JSONResponse(status_code=code, content=data)


@app.post("/api/operations/{operation_id}/status")
@app.post("/api/v1/operations/{operation_id}/status")
async def proxy_operation_status(operation_id: str, request: Request):
    body = await request.body()
    code, data = _proxy_to_operations(f"/api/operations/{operation_id}/status", method="POST", data=body if body else None)
    return JSONResponse(status_code=code, content=data)


@app.post("/api/operations/{operation_id}/assign")
@app.post("/api/v1/operations/{operation_id}/assign")
async def proxy_operation_assign(operation_id: str, request: Request):
    body = await request.body()
    code, data = _proxy_to_operations(f"/api/operations/{operation_id}/assign", method="POST", data=body if body else None)
    return JSONResponse(status_code=code, content=data)


@app.post("/api/operations/{operation_id}/cancel")
@app.post("/api/v1/operations/{operation_id}/cancel")
async def proxy_operation_cancel(operation_id: str, request: Request):
    body = await request.body()
    code, data = _proxy_to_operations(f"/api/operations/{operation_id}/cancel", method="POST", data=body if body else None)
    return JSONResponse(status_code=code, content=data)


@app.get("/api/operations/{operation_id}/audit")
@app.get("/api/v1/operations/{operation_id}/audit")
async def proxy_operation_audit(operation_id: str, request: Request):
    code, data = _proxy_to_operations(f"/api/operations/{operation_id}/audit", method="GET")
    return JSONResponse(status_code=code, content=data)


# ═════════════════════════════════════════════════════════════════════════════
# INCIDENT REPORTING & MANAGEMENT ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

def _get_all_authoritative_zones() -> List[Dict[str, Any]]:
    """
    Returns all authoritative zones across all defined scenarios.
    Ensures incidents reported in any scenario's city (Varanasi or Nepal)
    correctly resolve to that city's nearest tactical zone, preventing cross-city mismatch.
    """
    all_zones = []
    active_ids = set()
    for z in getattr(sim, "zones", []):
        all_zones.append(z)
        active_ids.add(z.get("id"))

    for sc_id, sc_info in AVAILABLE_SCENARIOS.items():
        try:
            sc_zones = _load_scenario_json(sc_id, "zones.json")
            for z in sc_zones:
                if z.get("id") not in active_ids:
                    all_zones.append(z)
                    active_ids.add(z.get("id"))
        except Exception:
            pass
    return all_zones if all_zones else ZONES_BASELINE


@app.get("/api/locations")
def list_locations():
    """
    Authoritative list of scenario centers and tactical operational zones
    extracted directly from Core datasets without external dependencies.
    """
    catalog = []
    for sc_id, sc in AVAILABLE_SCENARIOS.items():
        catalog.append({
            "id": f"{sc_id}_center",
            "name": f"{sc['name']} (Central)",
            "city": sc["name"].split()[0],
            "region": sc["region"],
            "latitude": sc["center"][0],
            "longitude": sc["center"][1],
            "type": "SCENARIO_CENTER",
            "scenario_id": sc_id,
        })
    for z in _get_all_authoritative_zones():
        catalog.append({
            "id": z["id"],
            "name": z["name"],
            "city": "Varanasi" if z["id"].startswith("Z") else ("Nepal" if z["id"].startswith("N") else "Tactical"),
            "region": "Uttar Pradesh, India" if z["id"].startswith("Z") else "Bagmati & Sindhupalchok, Nepal",
            "latitude": z["latitude"],
            "longitude": z["longitude"],
            "type": "TACTICAL_ZONE",
        })
    return {"locations": catalog, "total": len(catalog)}


@app.post("/api/incidents", response_model=IncidentResponse, status_code=201)
def create_incident(req: IncidentCreateRequest):
    """
    Register an authoritative emergency incident report.
    Validates payload, assigns unique server ID and UTC timestamp,
    determines nearest zone metadata across authoritative scenarios,
    and persists to the incident store.
    """
    authoritative_zones = _get_all_authoritative_zones()
    incident = incident_store.create_incident(req, active_zones=authoritative_zones)
    return incident


@app.get("/api/incidents", response_model=IncidentListResponse)
def list_incidents(status: Optional[str] = None):
    """
    Retrieve all registered emergency incidents, ordered newest first.
    Optionally filter by status: REPORTED, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CANCELLED.
    """
    incidents = incident_store.get_all(status_filter=status)
    return {"incidents": incidents, "total": len(incidents)}


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str):
    """
    Fetch a specific emergency incident by its authoritative ID.
    """
    incident = incident_store.get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return incident


@app.patch("/api/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident_status(incident_id: str, req: IncidentStatusUpdateRequest):
    """
    Controlled update of incident lifecycle status (REPORTED, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CANCELLED).
    """
    updated = incident_store.update_status(incident_id, new_status=req.status, note=req.note)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return updated


# ═════════════════════════════════════════════════════════════════════════════
# EVACUATION LOGIC & ENDPOINTS (PHASE 1)
# Workflow: Disaster -> Zone -> People at Risk -> Priority -> Safe Zone ->
#           Capacity Check -> Resource Assignment -> Route -> Evacuation -> Safe Arrival
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/api/evacuation/affected-zones")
def get_affected_zones():
    """
    Get all affected zones enriched with people at risk, remaining population,
    vulnerable counts, road accessibility, and calculated evacuation priority.
    """
    state = sim.compute_full_state(active_dispatches=list(DISPATCHED_VEHICLES.values()))
    safe_zones = state.get("safe_zones", [])
    extended_zones = [extend_affected_zone(z, safe_zones=safe_zones) for z in state.get("zones", [])]
    return {
        "scenario_id": CURRENT_SCENARIO_ID,
        "count": len(extended_zones),
        "zones": extended_zones
    }


@app.get("/api/evacuation/safe-zones")
def get_safe_zones():
    """
    Get all safe zones (upgraded shelters) with available capacity, occupancy,
    safety score, food, water, and medical support.
    """
    hospitals = sim.facilities.get("hospitals", [])
    safe_zones = [
        upgrade_safe_zone(s, hospitals=hospitals)
        for s in sim.facilities.get("shelters", [])
    ]
    return {
        "scenario_id": CURRENT_SCENARIO_ID,
        "count": len(safe_zones),
        "safe_zones": safe_zones
    }


@app.post("/api/evacuation/priority")
def calculate_priority_endpoint(req: EvacuationPriorityRequest):
    """
    Calculate real-time evacuation priority and urgency for a zone.
    """
    if req.zone_id:
        zone = next((z for z in sim.zones if z["id"] == req.zone_id), None)
        if not zone:
            raise HTTPException(status_code=404, detail=f"Zone {req.zone_id} not found")
    elif req.zone:
        zone = req.zone
    else:
        raise HTTPException(status_code=400, detail="zone_id or zone object is required")
        
    return calculate_evacuation_priority(zone, hci_score=req.hci_score)


@app.post("/api/evacuation/recommend-safe-zone")
def recommend_safe_zone_endpoint(req: SafeZoneRecommendRequest):
    """
    Select and rank the most suitable Safe Zones for an affected zone based on
    safety score, available capacity, travel time, and route security.
    """
    zone = next((z for z in sim.zones if z["id"] == req.zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {req.zone_id} not found")
        
    nodes = _build_nodes()
    svc = RoutingService(sim.roads, nodes)
    safe_zones = [
        upgrade_safe_zone(s, hospitals=sim.facilities.get("hospitals", []))
        for s in sim.facilities.get("shelters", [])
    ]
    ranked = rank_safe_zones_for_zone(zone, safe_zones, routing_service=svc)
    return {
        "zone_id": req.zone_id,
        "zone_name": zone.get("name"),
        "ranked_safe_zones": ranked
    }


@app.post("/api/evacuation/plan")
def create_evacuation_plan_endpoint(req: EvacuationPlanRequest):
    """
    Create a complete evacuation plan with automated capacity checks and split allocation.
    """
    zone = next((z for z in sim.zones if z["id"] == req.zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {req.zone_id} not found")
        
    zone_copy = deepcopy(zone)
    if req.people_at_risk is not None:
        zone_copy["affected_population"] = req.people_at_risk
        
    nodes = _build_nodes()
    svc = RoutingService(sim.roads, nodes)
    safe_zones = [
        upgrade_safe_zone(s, hospitals=sim.facilities.get("hospitals", []))
        for s in sim.facilities.get("shelters", [])
    ]
    avail_resources = sim.resources.get("units", []) if req.auto_assign_resources else None
    
    plan = create_evacuation_plan(
        zone_copy, safe_zones,
        routing_service=svc,
        available_resources=avail_resources
    )
    ACTIVE_EVACUATION_PLANS[plan["planId"]] = plan
    return plan


@app.post("/api/evacuation/assign")
def assign_evacuation_resources_endpoint(req: EvacuationAssignRequest):
    """
    Assign evacuation transport resources (buses, vans, ambulances, helicopters, boats) to an evacuation plan.
    """
    if req.plan_id not in ACTIVE_EVACUATION_PLANS:
        raise HTTPException(status_code=404, detail=f"Evacuation plan {req.plan_id} not found")
        
    plan = ACTIVE_EVACUATION_PLANS[req.plan_id]
    all_units = sim.resources.get("units", [])
    if req.resource_ids:
        eligible = [u for u in all_units if u["id"] in req.resource_ids]
    else:
        eligible = all_units
        
    updated_plan = assign_resources_to_plan(plan, eligible)
    ACTIVE_EVACUATION_PLANS[req.plan_id] = updated_plan
    return updated_plan


@app.get("/api/evacuation/status/{plan_id}")
def get_evacuation_status_endpoint(plan_id: str):
    """
    Get real-time lifecycle status and state-driven people tracking for an evacuation plan.
    """
    if plan_id not in ACTIVE_EVACUATION_PLANS:
        raise HTTPException(status_code=404, detail=f"Evacuation plan {plan_id} not found")
    return ACTIVE_EVACUATION_PLANS[plan_id]


@app.post("/api/evacuation/progress")
def update_evacuation_progress_endpoint(req: EvacuationProgressRequest):
    """
    Progress the evacuation lifecycle and update people tracking.
    """
    if req.plan_id not in ACTIVE_EVACUATION_PLANS:
        raise HTTPException(status_code=404, detail=f"Evacuation plan {req.plan_id} not found")
        
    plan = ACTIVE_EVACUATION_PLANS[req.plan_id]
    try:
        updated_plan = update_evacuation_progress(
            plan,
            target_status=req.target_status,
            people_delta=req.people_delta,
            note=req.note or ""
        )
        ACTIVE_EVACUATION_PLANS[req.plan_id] = updated_plan
        return updated_plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/evacuation/plans")
def list_evacuation_plans_endpoint():
    """
    List all active evacuation plans.
    """
    return {"plans": list(ACTIVE_EVACUATION_PLANS.values())}


# ── PHASE 3: ROUTE SAFETY SCORING, REROUTING, OVERFLOW & IMPACT ──────────
@app.post("/api/evacuation/routes/score")
def score_evacuation_route_endpoint(req: EvacuationRouteScoreRequest):
    """
    Calculate safety-first route between an affected zone and a safe zone.
    Returns composite risk score, safety grade, and primary + alternate corridors.
    """
    nodes = _build_nodes()
    service = RoutingService(sim.roads, nodes)
    corridor = service.get_evacuation_corridor(
        req.origin_zone_id,
        req.dest_safe_zone_id,
        vehicle_type=req.vehicle_type or "bus",
        excluded_road_ids=req.excluded_road_ids
    )
    return corridor


@app.post("/api/evacuation/reroute")
def reroute_evacuation_plan_endpoint(req: EvacuationRerouteRequest):
    """
    Trigger dynamic rerouting for an evacuation plan when road segments are blocked.
    """
    if req.plan_id not in ACTIVE_EVACUATION_PLANS:
        raise HTTPException(status_code=404, detail=f"Evacuation plan {req.plan_id} not found")
    plan = ACTIVE_EVACUATION_PLANS[req.plan_id]
    nodes = _build_nodes()
    service = RoutingService(sim.roads, nodes)
    safe_zones = [
        upgrade_safe_zone(s, hospitals=sim.facilities.get("hospitals", []))
        for s in sim.facilities.get("shelters", [])
    ]
    blocked_ids = req.blocked_road_ids or [r["id"] for r in sim.roads if r.get("status") == "blocked"]
    result = reroute_evacuation_plan(plan, blocked_ids, service, safe_zones)
    ACTIVE_EVACUATION_PLANS[req.plan_id] = result["plan"]
    return result


@app.post("/api/evacuation/overflow")
def handle_safe_zone_overflow_endpoint(req: EvacuationOverflowRequest):
    """
    Trigger safe zone capacity overflow diversion and split allocation.
    """
    if req.plan_id not in ACTIVE_EVACUATION_PLANS:
        raise HTTPException(status_code=404, detail=f"Evacuation plan {req.plan_id} not found")
    plan = ACTIVE_EVACUATION_PLANS[req.plan_id]
    nodes = _build_nodes()
    service = RoutingService(sim.roads, nodes)
    safe_zones = [
        upgrade_safe_zone(s, hospitals=sim.facilities.get("hospitals", []))
        for s in sim.facilities.get("shelters", [])
    ]
    result = handle_safe_zone_overflow(plan, req.overflow_safe_zone_id, safe_zones, service)
    ACTIVE_EVACUATION_PLANS[req.plan_id] = result["plan"]
    return result


@app.post("/api/evacuation/step")
def step_evacuation_simulation_endpoint(req: EvacuationStepRequest):
    """
    Advance progressive people movement simulation:
    At Risk -> Assigned -> Picked Up -> In Transit -> Safe
    Calculates convoy trips and waves dynamically.
    """
    if req.plan_id not in ACTIVE_EVACUATION_PLANS:
        raise HTTPException(status_code=404, detail=f"Evacuation plan {req.plan_id} not found")
    plan = ACTIVE_EVACUATION_PLANS[req.plan_id]
    result = step_evacuation_simulation(
        plan,
        elapsed_minutes=req.elapsed_minutes or 5.0,
        vehicle_speed_factor=req.vehicle_speed_factor or 1.0
    )
    ACTIVE_EVACUATION_PLANS[req.plan_id] = result["plan"]
    return result


@app.get("/api/evacuation/impact")
def get_evacuation_impact_endpoint():
    """
    Compute authentic Before vs After humanitarian impact derived strictly from active state.
    """
    safe_zones = [
        upgrade_safe_zone(s, hospitals=sim.facilities.get("hospitals", []))
        for s in sim.facilities.get("shelters", [])
    ]
    impact = calculate_evacuation_impact(
        baseline_zones=ZONES_BASELINE,
        current_zones=sim.zones,
        active_plans=list(ACTIVE_EVACUATION_PLANS.values()),
        safe_zones=safe_zones,
        resources=sim.resources
    )
    return impact



@app.get("/api/state")
def get_full_state():
    state = _full_state()
    state["active_dispatches"] = list(DISPATCHED_VEHICLES.values())
    return state


@app.get("/api/baseline")
def get_baseline():
    nodes: Dict[str, Dict] = {z["id"]: z for z in ZONES_BASELINE}
    if FACILITIES_BASELINE.get("depot"):
        nodes["DEPOT"] = FACILITIES_BASELINE["depot"]
    for d in FACILITIES_BASELINE.get("depots", []):
        nodes[d["id"]] = d
    scored = classify_all_zones(ZONES_BASELINE)
    routes = compute_all_routes(ZONES_BASELINE, ROADS_BASELINE, nodes=nodes)
    depot_ids = [d["id"] for d in FACILITIES_BASELINE.get("depots", [])] or ["DEPOT"]
    routes_by_origin = {}
    for d_id in depot_ids:
        try:
            routes_by_origin[d_id] = compute_all_routes(
                ZONES_BASELINE, ROADS_BASELINE, source=d_id, nodes=nodes
            )
        except Exception:
            routes_by_origin[d_id] = {}
    recs = build_recommendations(
        ZONES_BASELINE, scored,
        RESOURCES_BASELINE["inventory"],
        routes,
        RESOURCES_BASELINE.get("units", []),
        routes_by_origin,
    )
    return {
        "scenario_id":     CURRENT_SCENARIO_ID,
        "zones":           scored,
        "roads":           ROADS_BASELINE,
        "facilities":      FACILITIES_BASELINE,
        "routes":          routes,
        "routes_by_origin": routes_by_origin,
        "recommendations": recs,
        "active_events":   [],
    }


def interpolate_coords(geometry: List[List[float]], progress_pct: float) -> List[float]:
    if not geometry:
        return [0.0, 0.0]
    if len(geometry) < 2:
        return geometry[0]
    p = max(0.0, min(100.0, progress_pct)) / 100.0
    dists = []
    total = 0.0
    for i in range(1, len(geometry)):
        a, b = geometry[i-1], geometry[i]
        d = haversine(a[0], a[1], b[0], b[1])
        dists.append(d)
        total += d
    if total == 0.0:
        return geometry[0]
    target = p * total
    for i, d in enumerate(dists):
        if target <= d or i == len(dists) - 1:
            frac = target / d if d > 0 else 1.0
            a, b = geometry[i], geometry[i+1]
            return [a[0] + frac * (b[0] - a[0]), a[1] + frac * (b[1] - a[1])]
        target -= d
    return geometry[-1]


@app.post("/api/simulation/apply")
def apply_simulation(req: SimulationRequest):
    events = [e.model_dump(exclude_none=True) for e in req.events]
    global DISPATCHED_VEHICLES
    updated = sim.apply_events(events, active_dispatches=list(DISPATCHED_VEHICLES.values()))
    for rid, d in list(DISPATCHED_VEHICLES.items()):
        if d.get("status") == "ARRIVED":
            continue
        nodes = _build_nodes()
        svc = RoutingService(sim.roads, nodes)
        if not d.get("is_air") and d.get("mode") != "AIR" and d.get("resource_type") != "helicopter":
            geom = d.get("route", {}).get("geometry", [])
            prog = d.get("progress_pct", 0)
            curr_loc = interpolate_coords(geom, prog)
            curr_loc_str = f"{curr_loc[0]},{curr_loc[1]}"
            blocked_roads = [r["id"] for r in sim.roads if r["status"] == "blocked"]
            snap_info = svc.snap_location(curr_loc[0], curr_loc[1], allow_blocked=True)
            snap_road = snap_info.get("road_id")
            if snap_road in blocked_roads:
                from_n = snap_info.get("from_node")
                new_route = svc.get_route(from_n, d["zone_id"], excluded_road_ids=blocked_roads, use_snap=False) if from_n else {"reachable": False}
            else:
                new_route = svc.get_route(curr_loc_str, d["zone_id"],
                                          excluded_road_ids=blocked_roads, use_snap=True)
            if not new_route.get("reachable"):
                d["status"] = "ROUTE_BLOCKED"
                d["route_recalc_note"] = "Original route blocked — ground route recalculation failed."
                d["distance_km"] = 0.0
                d["eta_min"] = 0.0
                if geom:
                    stop_idx = max(2, int(len(geom) * prog / 100))
                    d["route"]["geometry"] = geom[:stop_idx]
            else:
                old_ids = d.get("route", {}).get("road_ids", [])
                new_ids = new_route.get("road_ids", [])
                d["route"] = new_route
                d["distance_km"] = new_route.get("distance_km")
                d["eta_min"] = new_route.get("total_time_min")
                d["origin"] = curr_loc_str
                if set(old_ids) != set(new_ids):
                    d["status"] = "REROUTED"
                    d["route_recalc_note"] = "Different route assigned due to sector status updates."
    updated["active_dispatches"] = list(DISPATCHED_VEHICLES.values())
    return updated


@app.post("/api/simulation/reset")
def reset_simulation():
    global DISPATCHED_VEHICLES
    sim.reset()
    DISPATCHED_VEHICLES = {}
    return {"status": "reset", "message": "Simulation restored to baseline; all dispatches cleared."}


@app.get("/api/simulation/cyclone-presets")
def list_cyclone_presets():
    return {"presets": get_cyclone_presets()}


@app.post("/api/simulation/parametric-cyclone")
def run_parametric_cyclone(req: ParametricCycloneRequest):
    global DISPATCHED_VEHICLES
    result = sim.apply_parametric_cyclone(
        surge_height_m=req.surge_height_m if req.surge_height_m is not None else 3.0,
        wind_speed_kmh=req.wind_speed_kmh if req.wind_speed_kmh is not None else 130.0,
        rainfall_24h_mm=req.rainfall_24h_mm if req.rainfall_24h_mm is not None else 200.0,
        breach_locations=req.breach_locations,
        active_dispatches=list(DISPATCHED_VEHICLES.values())
    )
    result["active_dispatches"] = list(DISPATCHED_VEHICLES.values())
    return result


@app.get("/api/scenarios")
def list_scenarios():
    return {
        "current_scenario": CURRENT_SCENARIO_ID,
        "scenarios": [
            {
                "id": sc["id"],
                "name": sc["name"],
                "region": sc["region"],
                "description": sc["description"],
                "center": sc["center"],
                "zoom": sc["zoom"],
                "zones_count": sc["zones_count"],
                "is_active": (sc["id"] == CURRENT_SCENARIO_ID),
                "disclaimer": sc["disclaimer"]
            }
            for sc in AVAILABLE_SCENARIOS.values()
        ]
    }


@app.post("/api/scenario/switch")
def switch_active_scenario(req: ScenarioSwitchRequest):
    return switch_scenario(req.scenario_id)


@app.get("/api/scenario/info")
def scenario_info():
    sc_info = AVAILABLE_SCENARIOS.get(CURRENT_SCENARIO_ID, AVAILABLE_SCENARIOS["varanasi"])
    return {
        "scenario_id":   CURRENT_SCENARIO_ID,
        "scenario":      sc_info["name"],
        "region":        sc_info["region"],
        "description":   sc_info["description"],
        "disclaimer":    sc_info["disclaimer"],
        "center":        sc_info["center"],
        "zoom":          sc_info["zoom"],
        "zones":         len(ZONES_BASELINE),
        "roads":         len(ROADS_BASELINE),
        "hospitals":     len(FACILITIES_BASELINE.get("hospitals", [])),
        "shelters":      len(FACILITIES_BASELINE.get("shelters", [])),
        "depots":        len(FACILITIES_BASELINE.get("depots", [])),
        "helicopter_bases": len(FACILITIES_BASELINE.get("helicopter_bases", [])),
        "active_events": len(sim.active_events),
        "active_dispatches": len(DISPATCHED_VEHICLES),
        "routing_method": "Road-graph Dijkstra with geometry waypoints, road snapping, alternate routes, helicopter fallback.",
    }


@app.get("/api/events")
def get_scenario_events():
    sc_info = AVAILABLE_SCENARIOS.get(CURRENT_SCENARIO_ID, AVAILABLE_SCENARIOS["varanasi"])
    sc_dir = sc_info["data_dir"]
    path = sc_dir / "events.json"
    if not path.exists():
        path = DATA_DIR / "events.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return {"scenario_id": CURRENT_SCENARIO_ID, "events": json.load(f)}
    return {"scenario_id": CURRENT_SCENARIO_ID, "events": []}


@app.get("/api/ai/status")
def ai_status():
    return get_ai_status()


@app.post("/api/ai/systemic-risk")
def systemic_risk_analysis(req: Optional[SystemicRiskRequest] = None):
    include_baseline = req.include_baseline if req else True
    current_state = _full_state()
    baseline_state = get_baseline() if include_baseline else None
    sc_info = AVAILABLE_SCENARIOS.get(CURRENT_SCENARIO_ID, AVAILABLE_SCENARIOS["varanasi"])

    context = build_systemic_risk_context(current_state, baseline_state, scenario_info=sc_info)
    analysis = analyze_systemic_risk(context)

    return {
        "status": "success",
        "analysis": analysis,
        "context_summary": {
            "total_zones": context.get("overview", {}).get("total_zones", 0),
            "critical_zones": context.get("overview", {}).get("critical_zones_count", 0),
            "blocked_roads": len(context.get("road_network", {}).get("blocked_road_ids", [])),
            "active_events": len(context.get("active_what_if_events", [])),
        },
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }


@app.post("/api/ai/ask")
def ask_ai(req: AIQueryRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    current_state = _full_state()
    baseline_state = get_baseline() if req.include_baseline else None
    sc_info = AVAILABLE_SCENARIOS.get(CURRENT_SCENARIO_ID, AVAILABLE_SCENARIOS["varanasi"])
    context = build_systemic_risk_context(current_state, baseline_state, scenario_info=sc_info)

    answer_obj = query_ai(req.question.strip(), context)
    return {
        "question": req.question.strip(),
        "response": answer_obj,
        "answered_at": __import__("datetime").datetime.now().isoformat(),
    }


@app.post("/api/ai/advisory")
def generate_ai_advisory(req: Optional[AdvisoryRequest] = None):
    """
    Google Gemini Multimodal Early Warning & Community Advisory Engine (Phase 3).
    Synthesizes SRTM elevation, Dynamic World LULC, real-time cyclonic weather,
    and composite Geo-Risk scores into actionable bilingual advisories.
    """
    zone_id = req.zone_id if req and req.zone_id else None
    current_state = _full_state()
    zones = current_state.get("zones", [])
    
    zone_data = next((z for z in zones if z.get("id") == zone_id), None) if zone_id else None
    if not zone_data and zones:
        # Default to highest criticality zone
        zone_data = zones[0]
        zone_id = zone_data.get("id")

    # Local shelters & roads
    facilities = current_state.get("facilities", {})
    shelters = facilities.get("shelters", [])
    roads = current_state.get("roads", [])

    # Real-time meteorological data
    weather_data = weather_service.get_current_weather()

    # Zone composite risk assessment
    risk_assessment = risk_engine.compute_zone_risk(zone_data, roads, weather_data) if zone_data else None

    # Earth Engine context
    gee_summary = gee_service.get_gee_status()

    advisory = generate_disaster_advisory(
        zone_id=zone_id,
        zone_data=zone_data,
        weather_data=weather_data,
        risk_data=risk_assessment,
        gee_data=gee_summary,
        shelters=shelters,
        roads=roads,
    )
    return advisory



# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4: ADAPTIVE AI EVACUATION INTELLIGENCE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/ai/evacuation-priority")
@app.post("/ai/evacuation-priority")
def ai_evacuation_priority_endpoint(req: EvacuationPriorityRequest):
    """
    Adaptive AI Evacuation Priority Prediction & Decision Optimization (Phase 4).
    Uses Tabular GBDT ML Model to predict evacuation priority, risk classification,
    Explainable AI (XAI) feature attributions, and calibrated confidence.
    """
    if req.zone:
        zone = req.zone
    elif req.zone_id:
        zone = next((z for z in sim.zones if z.get("id") == req.zone_id), None)
        if not zone:
            zone = next((z for z in ZONES_BASELINE if z.get("id") == req.zone_id), None)
        if not zone:
            raise HTTPException(status_code=404, detail=f"Zone {req.zone_id} not found")
    else:
        raise HTTPException(status_code=400, detail="zone_id or zone object is required")

    safe_zones = FACILITIES_BASELINE.get("shelters", [])
    prediction = predict_evacuation_priority(
        zone,
        disaster_type=req.disaster_type or "flood",
        disaster_severity=req.disaster_severity if req.disaster_severity is not None else 0.75,
        safe_zones=safe_zones,
        available_roads=sim.roads,
    )
    return prediction


@app.get("/api/ai/evacuation-priority/model-info")
def ai_evacuation_model_info():
    """
    Retrieve metadata, algorithm details, training history, and evaluation metrics
    for the active Evacuation ML model.
    """
    return get_model_info()


@app.post("/api/ai/evacuation-priority/feedback")
def ai_evacuation_log_feedback(req: FeedbackLogRequest):
    """
    Log actual evacuation mission outcome into feedback store for controlled retraining.
    """
    return log_evacuation_feedback(
        zone_id=req.zone_id,
        predicted_priority=req.predicted_priority,
        action_taken=req.action_taken,
        actual_evacuated=req.actual_evacuated,
        response_time_min=req.response_time_min,
        notes=req.notes or "",
    )


@app.get("/api/ai/evacuation-priority/feedback")
def ai_evacuation_get_feedback():
    """
    Retrieve logged feedback records from the feedback store.
    """
    return {"feedback_records": get_feedback_records()}


@app.post("/api/ai/evacuation-priority/retrain")
def ai_evacuation_retrain_model(req: Optional[RetrainRequest] = None):
    """
    Trigger controlled retraining pipeline incorporating recorded feedback data.
    """
    samples = req.n_samples if req else 2500
    seed = req.seed if req else 42
    return retrain_model_with_feedback(n_samples=samples, seed=seed)


def get_or_create_autonomous_session(
    scenario_id: Optional[str] = None,
    events: Optional[List[Dict[str, Any]]] = None,
    selected_conditions: Optional[List[str]] = None,
    force_reset: bool = False,
) -> Dict[str, Any]:
    global AUTONOMOUS_SESSION, DISPATCHED_VEHICLES, sim

    sc_id = scenario_id or CURRENT_SCENARIO_ID
    active_events = events if events is not None else [e.copy() for e in sim.active_events]
    conditions = selected_conditions or []

    # If an existing session matches this scenario_id and not force_reset, reuse it
    if (
        not force_reset
        and AUTONOMOUS_SESSION.get("sim_state") is not None
        and AUTONOMOUS_SESSION.get("scenario_id") == sc_id
    ):
        return AUTONOMOUS_SESSION

    logger.info(f"=== INITIALIZING AUTONOMOUS AI SIMULATION SESSION: {sc_id} ===")
    logger.info(f"Active What-If Conditions ({len(conditions)}): {conditions}")
    logger.info(f"Events to apply ({len(active_events)}): {active_events}")

    # Reconstruct clean, authoritative SimulationState starting from baseline + What-If events
    new_sim = SimulationState(
        deepcopy(ZONES_BASELINE),
        deepcopy(ROADS_BASELINE),
        deepcopy(FACILITIES_BASELINE),
        deepcopy(RESOURCES_BASELINE),
    )
    if active_events:
        new_sim.apply_events(active_events)

    # Server-side authoritative initial What-If calculation
    initial_full_state = new_sim.compute_full_state()
    initial_crits = [z["name"] for z in initial_full_state["zones"] if z.get("classification") == "CRITICAL"]
    logger.info(
        f"Initial Critical Area Ranking: {[z['name'] + ' (HCI ' + str(z['hci_score']) + ')' for z in initial_full_state['zones'][:3]]}"
    )

    AUTONOMOUS_SESSION = {
        "scenario_id": sc_id,
        "selected_conditions": conditions,
        "events": active_events,
        "sim_state": new_sim,
        "initial_state": initial_full_state,
        "resolved_ids": set(),
        "concluded_ids": set(),
        "active_target_id": None,
        "target_step_count": 0,
        "stagnation_counter": 0,
        "history": [],
        "dispatched_vehicles": {},
        "is_active": True,
    }
    return AUTONOMOUS_SESSION


@app.post("/api/simulation/autonomous/step")
def autonomous_simulation_step(req: Optional[AutonomousStepRequest] = None):
    global AUTONOMOUS_SESSION, sim
    req_scenario_id = req.scenario_id if req else None
    req_events = req.events if req else None
    req_conditions = req.selected_conditions if req else None
    force_reset = req.reset_session if req else False

    session = get_or_create_autonomous_session(
        scenario_id=req_scenario_id,
        events=req_events,
        selected_conditions=req_conditions,
        force_reset=force_reset,
    )

    step_num = len(session["history"]) + 1
    scenario_context = {
        "scenario_id": session["scenario_id"],
        "selected_conditions": session["selected_conditions"],
        "events": session["events"],
    }

    step_result = execute_autonomous_step(
        session["sim_state"],
        session["resolved_ids"],
        step_num,
        session["history"],
        session["dispatched_vehicles"],
        scenario_context=scenario_context,
        active_target_id=session.get("active_target_id"),
        target_step_count=session.get("target_step_count", 0),
        concluded_ids=session.get("concluded_ids"),
        stagnation_counter=session.get("stagnation_counter", 0),
    )
    session["history"].append(step_result)

    # Update session target tracking for Resolve-Then-Advance
    session["active_target_id"] = step_result.get("active_target_id")
    session["target_step_count"] = step_result.get("target_step_count", 0)
    session["concluded_ids"] = set(step_result.get("concluded_ids", []))
    session["stagnation_counter"] = step_result.get("stagnation_counter", 0)
    session["resolved_ids"] = set(step_result.get("resolved_ids", []))

    # Synchronize global sim with current autonomous state so map and UI stay completely in sync
    sim.zones = deepcopy(session["sim_state"].zones)
    sim.roads = deepcopy(session["sim_state"].roads)
    sim.facilities = deepcopy(session["sim_state"].facilities)
    sim.resources = deepcopy(session["sim_state"].resources)
    sim.active_events = deepcopy(session["sim_state"].active_events)

    return {
        "status": "success",
        "step": step_result,
        "scenario": {
            "scenario_id": session["scenario_id"],
            "selected_conditions": session["selected_conditions"],
            "active_events_count": len(session["events"]),
        },
        "total_steps_so_far": len(session["history"]),
        "active_target_id": session["active_target_id"],
        "continue_same_target": step_result.get("continue_same_target", False),
        "target_status": step_result.get("target_status"),
        "target_status_label": step_result.get("target_status_label"),
        "resolved_ids": list(session["resolved_ids"]),
        "concluded_ids": list(session["concluded_ids"]),
        "initial_critical_zones": [
            z["name"] for z in session["initial_state"]["zones"] if z.get("classification") == "CRITICAL"
        ],
    }


@app.post("/api/simulation/autonomous/run")
def autonomous_simulation_run(req: Optional[AutonomousRunRequest] = None):
    global AUTONOMOUS_SESSION, sim
    req_scenario_id = req.scenario_id if req else None
    req_events = req.events if req else None
    req_conditions = req.selected_conditions if req else None
    max_steps = req.max_steps if req and req.max_steps else 10

    # Clean session for full run
    session = get_or_create_autonomous_session(
        scenario_id=req_scenario_id,
        events=req_events,
        selected_conditions=req_conditions,
        force_reset=True,
    )

    scenario_context = {
        "scenario_id": session["scenario_id"],
        "selected_conditions": session["selected_conditions"],
        "events": session["events"],
    }

    res = run_full_autonomous_simulation(
        session["sim_state"],
        max_steps=max_steps,
        dispatched_vehicles=session["dispatched_vehicles"],
        scenario_context=scenario_context,
    )

    for step in res["steps"]:
        if step.get("is_target_resolved") and step.get("target_area"):
            session["resolved_ids"].add(step["target_area"]["id"])
    session["history"] = res["steps"]

    # Synchronize global sim with final autonomous state
    sim.zones = deepcopy(session["sim_state"].zones)
    sim.roads = deepcopy(session["sim_state"].roads)
    sim.facilities = deepcopy(session["sim_state"].facilities)
    sim.resources = deepcopy(session["sim_state"].resources)
    sim.active_events = deepcopy(session["sim_state"].active_events)

    return res


@app.post("/api/simulation/autonomous/reset")
def autonomous_simulation_reset(req: Optional[AutonomousResetRequest] = None):
    global AUTONOMOUS_SESSION, sim
    req_scenario_id = req.scenario_id if req else None
    req_events = req.events if req else None
    req_conditions = req.selected_conditions if req else None

    # Reset the session back to the clean What-If state (re-applying What-If events)
    session = get_or_create_autonomous_session(
        scenario_id=req_scenario_id,
        events=req_events,
        selected_conditions=req_conditions,
        force_reset=True,
    )

    # Restore global sim back to the clean What-If state as well
    sim.zones = deepcopy(session["sim_state"].zones)
    sim.roads = deepcopy(session["sim_state"].roads)
    sim.facilities = deepcopy(session["sim_state"].facilities)
    sim.resources = deepcopy(session["sim_state"].resources)
    sim.active_events = deepcopy(session["sim_state"].active_events)

    return {
        "status": "success",
        "message": "Autonomous simulation reset back to active What-If scenario.",
        "scenario_id": session["scenario_id"],
        "active_conditions": session["selected_conditions"],
        "initial_state": session["initial_state"],
    }


# =====================================================================
# GOOGLE EARTH ENGINE (GEE) SATELLITE & GEOSPATIAL INTELLIGENCE
# =====================================================================

@app.get("/api/gee/status")
def get_earth_engine_status():
    """Returns Google Earth Engine connectivity, active auth method, and dataset capabilities."""
    return gee_service.get_gee_status()


@app.get("/api/gee/elevation")
def get_elevation_analytics(
    min_lng: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lng: Optional[float] = None,
    max_lat: Optional[float] = None
):
    """
    SRTM Digital Elevation Model (30m) analysis.
    Identifies low-lying coastal terrain (<3m) exposed to cyclonic storm surge inundation.
    """
    kwargs = {}
    if min_lng is not None: kwargs["min_lng"] = min_lng
    if min_lat is not None: kwargs["min_lat"] = min_lat
    if max_lng is not None: kwargs["max_lng"] = max_lng
    if max_lat is not None: kwargs["max_lat"] = max_lat
    return gee_service.get_elevation_data(**kwargs)


@app.get("/api/gee/land-cover")
def get_land_cover_analytics(
    min_lng: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lng: Optional[float] = None,
    max_lat: Optional[float] = None,
    date_start: Optional[str] = "2024-01-01",
    date_end: Optional[str] = "2024-12-31"
):
    """
    Dynamic World (10m Near Real-Time) Land Use & Land Cover classification.
    Evaluates mangrove bio-shields, exposed built-up settlements, and water bodies.
    """
    kwargs = {"date_start": date_start, "date_end": date_end}
    if min_lng is not None: kwargs["min_lng"] = min_lng
    if min_lat is not None: kwargs["min_lat"] = min_lat
    if max_lng is not None: kwargs["max_lng"] = max_lng
    if max_lat is not None: kwargs["max_lat"] = max_lat
    return gee_service.get_land_cover_data(**kwargs)


@app.get("/api/gee/rainfall")
def get_rainfall_analytics(
    min_lng: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lng: Optional[float] = None,
    max_lat: Optional[float] = None
):
    """
    CHIRPS Daily Precipitation and historical rainfall anomaly analysis.
    Monitors cyclonic cloudburst precipitation and estuarine flash-flood potential.
    """
    kwargs = {}
    if min_lng is not None: kwargs["min_lng"] = min_lng
    if min_lat is not None: kwargs["min_lat"] = min_lat
    if max_lng is not None: kwargs["max_lng"] = max_lng
    if max_lat is not None: kwargs["max_lat"] = max_lat
    return gee_service.get_rainfall_data(**kwargs)


@app.get("/api/gee/layers")
def get_gee_map_layers():
    """Returns available satellite raster and vector layers for Leaflet GIS visualization."""
    return gee_service.get_map_layers()


# ═════════════════════════════════════════════════════════════════════
# METEOROLOGICAL & PREDICTIVE GEO-RISK ENGINE (PHASE 2)
# ═════════════════════════════════════════════════════════════════════

@app.get("/api/weather/current")
def get_current_meteorological_telemetry(
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """
    Returns real-time or calibrated meteorological telemetry for Bay of Bengal.
    Includes barometric pressure, wind gusts, rainfall rate, and coastal station readings.
    """
    kwargs = {}
    if lat is not None: kwargs["lat"] = lat
    if lon is not None: kwargs["lon"] = lon
    return weather_service.get_current_weather(**kwargs)


@app.get("/api/weather/forecast")
def get_cyclone_forecast_timeline(
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """
    Returns 24h-72h cyclonic projection, estimated landfall timing, and peak surge outlook.
    """
    kwargs = {}
    if lat is not None: kwargs["lat"] = lat
    if lon is not None: kwargs["lon"] = lon
    return weather_service.get_weather_forecast(**kwargs)


@app.get("/api/weather/stations")
def get_coastal_weather_stations():
    """Returns observation telemetry across all coastal West Bengal meteorological stations."""
    return {"stations": weather_service.get_station_readings()}


@app.get("/api/risk/assessment")
def get_geo_risk_assessment():
    """
    Computes multi-criteria predictive risk across all active scenario zones:
    Risk = (0.40 * Hazard) + (0.35 * Exposure) + (0.25 * Vulnerability).
    Integrates GEE SRTM Elevation, Dynamic World LULC, and live meteorological feeds.
    """
    zones = getattr(sim, "zones", [])
    roads = getattr(sim, "roads", [])
    return risk_engine.assess_all_zones(zones, roads)


@app.get("/api/risk/hazard-map")
def get_hazard_map_geojson():
    """
    Returns standard GeoJSON FeatureCollection for rendering risk heat-zones on Leaflet.
    """
    zones = getattr(sim, "zones", [])
    roads = getattr(sim, "roads", [])
    return risk_engine.get_hazard_geojson(zones, roads)


