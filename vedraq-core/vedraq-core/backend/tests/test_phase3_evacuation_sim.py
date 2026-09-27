"""
VEDRAQ — Phase 3 Evacuation Routing, Simulation & Impact Tests
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, sim, ZONES_BASELINE, ROADS_BASELINE, FACILITIES_BASELINE, RESOURCES_BASELINE, ACTIVE_EVACUATION_PLANS
from app.services.routing import RoutingService
from app.services.evacuation import (
    create_evacuation_plan,
    reroute_evacuation_plan,
    handle_safe_zone_overflow,
    step_evacuation_simulation,
    calculate_evacuation_impact,
    upgrade_safe_zone,
    rank_safe_zones_for_zone,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    sim.reset()
    ACTIVE_EVACUATION_PLANS.clear()
    yield
    sim.reset()
    ACTIVE_EVACUATION_PLANS.clear()


def test_safety_first_route_scoring():
    nodes = {z["id"]: z for z in ZONES_BASELINE}
    for s in FACILITIES_BASELINE.get("shelters", []):
        nodes[s["id"]] = s
    service = RoutingService(ROADS_BASELINE, nodes)

    route = service.get_safest_evacuation_route("Z01", "S1", vehicle_type="bus")
    assert route["reachable"] is True
    assert route["corridor_type"] == "EVACUATION"
    assert "route_risk_score" in route
    assert 0 <= route["route_risk_score"] <= 100
    assert route["safety_grade"] in ("SAFE", "MODERATE_RISK", "HAZARDOUS")
    assert route["vehicle_suitability"] in ("OPTIMAL", "ACCEPTABLE", "SUB-OPTIMAL")
    assert len(route["geometry"]) >= 2
    assert route["distance_km"] > 0
    assert route["total_time_min"] > 0


def test_dynamic_rerouting_when_primary_road_blocked(client):
    nodes = {z["id"]: z for z in ZONES_BASELINE}
    safe_zones = [
        upgrade_safe_zone(s, hospitals=FACILITIES_BASELINE.get("hospitals", []))
        for s in FACILITIES_BASELINE.get("shelters", [])
    ]
    for s in safe_zones:
        nodes[s["id"]] = s
    service = RoutingService(ROADS_BASELINE, nodes)

    z01 = next(z for z in ZONES_BASELINE if z["id"] == "Z01")
    plan = create_evacuation_plan(z01, safe_zones, routing_service=service)

    # Initial route road IDs
    primary_roads = plan["destinations"][0]["route"]["road_ids"]
    assert len(primary_roads) > 0
    blocked_road = primary_roads[0]

    # Trigger dynamic rerouting
    res = reroute_evacuation_plan(plan, [blocked_road], service, safe_zones)
    assert res["rerouted"] is True
    assert res["event"] == "EVACUATION_REROUTED"
    assert plan["status"] == "REROUTED"
    assert "EVACUATION_REROUTED" in [e["status"] for e in plan["lifecycleHistory"]] or plan["status"] == "REROUTED"


def test_safe_zone_capacity_overflow_split(client):
    nodes = {z["id"]: z for z in ZONES_BASELINE}
    safe_zones = [
        upgrade_safe_zone(s, hospitals=FACILITIES_BASELINE.get("hospitals", []))
        for s in FACILITIES_BASELINE.get("shelters", [])
    ]
    for s in safe_zones:
        nodes[s["id"]] = s
    service = RoutingService(ROADS_BASELINE, nodes)

    z01 = next(z for z in ZONES_BASELINE if z["id"] == "Z01")
    plan = create_evacuation_plan(z01, safe_zones, routing_service=service)

    # Force the primary safe zone to have small remaining capacity to induce overflow
    primary_sz_id = plan["destinations"][0]["safeZoneId"]
    target_sz = next(s for s in safe_zones if s["safeZoneId"] == primary_sz_id)
    target_sz["availableCapacity"] = 100  # less than the 350 assigned
    target_sz["status"] = "full"

    res = handle_safe_zone_overflow(plan, primary_sz_id, safe_zones, service)
    assert res["handled"] is True

    assert res["event"] == "SAFE_ZONE_FULL"
    assert len(plan["destinations"]) >= 2
    # Verify split allocation preserves total allocated
    total_assigned = sum(d["assignedPeople"] for d in plan["destinations"])
    assert total_assigned == plan["allocation"]["totalAllocated"]


def test_progressive_people_movement_and_waves():
    nodes = {z["id"]: z for z in ZONES_BASELINE}
    safe_zones = [
        upgrade_safe_zone(s, hospitals=FACILITIES_BASELINE.get("hospitals", []))
        for s in FACILITIES_BASELINE.get("shelters", [])
    ]
    for s in safe_zones:
        nodes[s["id"]] = s
    service = RoutingService(ROADS_BASELINE, nodes)

    z01 = next(z for z in ZONES_BASELINE if z["id"] == "Z01")
    plan = create_evacuation_plan(
        z01, safe_zones, routing_service=service,
        available_resources=RESOURCES_BASELINE.get("units", [])
    )
    plan["totalTransportCapacity"] = 300  # Set batch capacity
    initial_risk = plan["peopleAtRisk"]

    # Step 1: Boarding / Pickup
    s1 = step_evacuation_simulation(plan)
    assert s1["event"] == "PICKUP_STARTED"
    assert plan["peopleTracking"]["peoplePickedUp"] == 300
    assert plan["peopleTracking"]["peopleEvacuated"] == 0

    # Step 2: In Transit
    s2 = step_evacuation_simulation(plan)
    assert s2["event"] == "PEOPLE_IN_TRANSIT"
    assert plan["peopleTracking"]["peopleInTransit"] == 300

    # Step 3: Arrived Safe Zone
    s3 = step_evacuation_simulation(plan)
    assert s3["event"] == "PEOPLE_ARRIVED"
    assert plan["peopleTracking"]["peopleEvacuated"] == 300
    assert plan["peopleTracking"]["peopleInTransit"] == 0
    assert plan["peopleTracking"]["peopleRemaining"] == initial_risk - 300
    assert s3["waveInfo"]["currentWave"] >= 1


def test_eight_evacuation_what_if_scenarios(client):
    # 1. PRIMARY_ROAD_BLOCKED
    r1 = client.post("/api/simulation/apply", json={"events": [{"type": "PRIMARY_ROAD_BLOCKED", "road_id": "R11"}]})
    assert r1.status_code == 200
    road_r11 = next(r for r in r1.json()["roads"] if r["id"] == "R11")
    assert road_r11["status"] == "blocked"

    # 2. ALTERNATE_ROAD_BLOCKED
    r2 = client.post("/api/simulation/apply", json={"events": [{"type": "ALTERNATE_ROAD_BLOCKED", "road_id": "R13"}]})
    assert r2.status_code == 200
    road_r13 = next(r for r in r2.json()["roads"] if r["id"] == "R13")
    assert road_r13["status"] == "blocked"

    # 3. SAFE_ZONE_FULL
    r3 = client.post("/api/simulation/apply", json={"events": [{"type": "SAFE_ZONE_FULL", "safe_zone_id": "S1"}]})
    assert r3.status_code == 200
    sz_s1 = next(s for s in r3.json()["safe_zones"] if s["id"] == "S1")
    assert sz_s1["availableCapacity"] == 0

    # 4. SAFE_ZONE_UNAVAILABLE
    r4 = client.post("/api/simulation/apply", json={"events": [{"type": "SAFE_ZONE_UNAVAILABLE", "safe_zone_id": "S1"}]})
    assert r4.status_code == 200
    sz_s1_off = next(s for s in r4.json()["safe_zones"] if s["id"] == "S1")
    assert sz_s1_off["status"] == "unavailable"

    # 5. VEHICLE_BREAKDOWN
    r5 = client.post("/api/simulation/apply", json={"events": [{"type": "VEHICLE_BREAKDOWN"}]})
    assert r5.status_code == 200
    unavail_units = [u for u in r5.json()["resources"]["units"] if u["status"] == "UNAVAILABLE"]
    assert len(unavail_units) >= 1

    # 6. POPULATION_SURGE
    r6 = client.post("/api/simulation/apply", json={"events": [{"type": "POPULATION_SURGE", "zone_id": "Z01", "surge_pct": 30}]})
    assert r6.status_code == 200
    z01_surged = next(z for z in r6.json()["zones"] if z["id"] == "Z01")
    assert z01_surged["peopleAtRisk"] > 3000

    # 7. COMMUNICATION_FAILURE
    r7 = client.post("/api/simulation/apply", json={"events": [{"type": "COMMUNICATION_FAILURE", "zone_id": "Z01"}]})
    assert r7.status_code == 200
    z01_comm = next(z for z in r7.json()["zones"] if z["id"] == "Z01")
    assert z01_comm["communication_status"] == "none"

    # 8. SEVERE_WEATHER
    r8 = client.post("/api/simulation/apply", json={"events": [{"type": "SEVERE_WEATHER", "speed_multiplier": 0.5}]})
    assert r8.status_code == 200
    degraded_roads = [r for r in r8.json()["roads"] if r.get("status") == "degraded"]
    assert len(degraded_roads) >= 1


def test_before_after_impact_api(client):
    # Create plan
    p_res = client.post("/api/evacuation/plan", json={"zone_id": "Z01"})
    assert p_res.status_code == 200
    plan_id = p_res.json()["planId"]

    # Step progress
    step_res = client.post("/api/evacuation/step", json={"plan_id": plan_id})
    assert step_res.status_code == 200

    # Get impact
    imp_res = client.get("/api/evacuation/impact")
    assert imp_res.status_code == 200
    impact = imp_res.json()

    assert "initialPeopleAtRisk" in impact
    assert "peopleEvacuated" in impact
    assert "peopleRemaining" in impact
    assert "completionPercentage" in impact
    assert "safeZoneUtilizationPct" in impact
    assert "criticalZonesCleared" in impact
    assert "hciReduction" in impact
    assert impact["initialPeopleAtRisk"] > 0
