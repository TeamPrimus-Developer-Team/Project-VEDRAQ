"""
Test Suite for VEDRAQ Core Evacuation Logic — Phase 1
=====================================================
Tests:
- Scenario A: 3800 people, Safe Zone capacity 5000 -> One safe zone sufficient
- Scenario B: 3800 people, S03 capacity 2900, S05 capacity 2200 -> Split evacuation
- Scenario C: No safe zone has enough capacity -> Insufficient capacity condition
- Scenario D: Critical zone has higher priority than moderate zone -> Critical ranked first
- Scenario E: Safe zone is closer but dangerous -> Safer suitable zone preferred
- Resource assignment, lifecycle transitions, and state-driven people tracking
- Full REST API endpoints verification
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.evacuation import (
    extend_affected_zone,
    upgrade_safe_zone,
    calculate_evacuation_priority,
    rank_safe_zones_for_zone,
    allocate_evacuation_capacity,
    create_evacuation_plan,
    assign_resources_to_plan,
    update_evacuation_progress,
)


@pytest.fixture
def client():
    return TestClient(app)


# ── SCENARIO A: 3800 PEOPLE, SAFE ZONE CAPACITY 5000 -> ONE SAFE ZONE SUFFICIENT ─
def test_scenario_a_single_safe_zone_sufficient():
    people_at_risk = 3800
    safe_zones = [
        {
            "safeZoneId": "SZ01",
            "name": "Mega Regional Safe Complex",
            "availableCapacity": 5000,
            "totalCapacity": 6000,
            "safetyScore": 95.0,
            "distanceKm": 4.5,
            "etaMin": 12.0,
            "reachable": True,
            "roadAccessibility": "open"
        }
    ]
    
    alloc = allocate_evacuation_capacity(people_at_risk, safe_zones)
    
    assert alloc["isSufficient"] is True
    assert alloc["isSplit"] is False
    assert alloc["destinationsCount"] == 1
    assert alloc["destinations"][0]["safeZoneId"] == "SZ01"
    assert alloc["destinations"][0]["assignedPeople"] == 3800
    assert alloc["destinations"][0]["remainingAfterAllocation"] == 1200
    assert alloc["totalAllocated"] == 3800
    assert alloc["unallocatedDeficit"] == 0
    assert alloc["condition"] == "CAPACITY_SATISFIED"


# ── SCENARIO B: 3800 PEOPLE, S03 CAP 2900, S05 CAP 2200 -> SPLIT EVACUATION ─────
def test_scenario_b_split_evacuation():
    people_at_risk = 3800
    safe_zones = [
        {
            "safeZoneId": "S03",
            "name": "Lahartara Flood Camp",
            "availableCapacity": 2900,
            "totalCapacity": 3000,
            "safetyScore": 94.0,
            "distanceKm": 3.2,
            "etaMin": 18.0,
            "reachable": True,
            "roadAccessibility": "open"
        },
        {
            "safeZoneId": "S05",
            "name": "Govindpur School Shelter",
            "availableCapacity": 2200,
            "totalCapacity": 2500,
            "safetyScore": 88.0,
            "distanceKm": 5.1,
            "etaMin": 24.0,
            "reachable": True,
            "roadAccessibility": "open"
        }
    ]
    
    alloc = allocate_evacuation_capacity(people_at_risk, safe_zones)
    
    assert alloc["isSufficient"] is True
    assert alloc["isSplit"] is True
    assert alloc["destinationsCount"] == 2
    
    # S03 absorbs 2900
    assert alloc["destinations"][0]["safeZoneId"] == "S03"
    assert alloc["destinations"][0]["assignedPeople"] == 2900
    assert alloc["destinations"][0]["remainingAfterAllocation"] == 0
    
    # S05 absorbs remaining 900
    assert alloc["destinations"][1]["safeZoneId"] == "S05"
    assert alloc["destinations"][1]["assignedPeople"] == 900
    assert alloc["destinations"][1]["remainingAfterAllocation"] == 1300
    
    assert alloc["totalAllocated"] == 3800
    assert alloc["unallocatedDeficit"] == 0


# ── SCENARIO C: NO SAFE ZONE HAS ENOUGH CAPACITY -> INSUFFICIENT CONDITION ────────
def test_scenario_c_insufficient_safe_zone_capacity():
    people_at_risk = 3800
    safe_zones = [
        {
            "safeZoneId": "S01",
            "name": "Small School Shelter",
            "availableCapacity": 1200,
            "totalCapacity": 1500,
            "safetyScore": 85.0,
            "distanceKm": 2.0,
            "etaMin": 10.0,
            "reachable": True,
        },
        {
            "safeZoneId": "S02",
            "name": "Community Hall",
            "availableCapacity": 800,
            "totalCapacity": 1000,
            "safetyScore": 80.0,
            "distanceKm": 3.5,
            "etaMin": 15.0,
            "reachable": True,
        }
    ]
    # Total available = 2000 < 3800 -> Deficit = 1800
    alloc = allocate_evacuation_capacity(people_at_risk, safe_zones)
    
    assert alloc["isSufficient"] is False
    assert alloc["unallocatedDeficit"] == 1800
    assert alloc["totalAllocated"] == 2000
    assert alloc["condition"] == "INSUFFICIENT_SAFE_ZONE_CAPACITY"
    assert "Deficit of 1800 evacuees" in alloc["warning"]


# ── SCENARIO D: CRITICAL ZONE HIGHER PRIORITY THAN MODERATE ZONE ──────────────────
def test_scenario_d_critical_zone_higher_priority_than_moderate():
    critical_zone = {
        "id": "Z01",
        "name": "Rampur Tanda",
        "population": 4200,
        "affected_population": 3800,
        "damage_percentage": 75,
        "hospital_status": "unavailable",
        "water_availability": "none",
        "food_availability": "critical",
        "road_accessibility": "blocked",
        "hci_score": 92.5
    }
    
    moderate_zone = {
        "id": "Z06",
        "name": "Assi Ghat Colony",
        "population": 6500,
        "affected_population": 1200,
        "damage_percentage": 25,
        "hospital_status": "functional",
        "water_availability": "adequate",
        "food_availability": "adequate",
        "road_accessibility": "open",
        "hci_score": 42.0
    }
    
    p_crit = calculate_evacuation_priority(critical_zone)
    p_mod = calculate_evacuation_priority(moderate_zone)
    
    assert p_crit["evacuationPriority"] > p_mod["evacuationPriority"]
    assert p_crit["riskLevel"] == "CRITICAL"
    assert p_crit["urgency"] == "IMMEDIATE"
    assert p_mod["riskLevel"] in ("MODERATE", "LOWER")
    assert p_mod["urgency"] in ("ELEVATED", "STANDARD")


# ── SCENARIO E: SAFE ZONE IS CLOSER BUT DANGEROUS -> SAFER SUITABLE PREFERRED ───
def test_scenario_e_safer_suitable_zone_preferred_over_dangerous_closer():
    affected_zone = {
        "id": "Z01",
        "name": "Flood Enclave",
        "latitude": 25.312,
        "longitude": 83.012,
        "road_accessibility": "open"
    }
    
    safe_zones = [
        # Closer shelter (1.5 km), but critically degraded safety & blocked road access
        {
            "id": "S_DANGER",
            "name": "Flood Submerged Community Shed",
            "latitude": 25.320,
            "longitude": 83.015,
            "capacity": 1000,
            "current_occupancy": 950,
            "food_stock_days": 0,
            "water_supply": "none",
            "status": "partial",
            "road_accessibility": "blocked"
        },
        # Slightly further shelter (4.5 km), but high safety score, functional water, open road
        {
            "id": "S_SAFE",
            "name": "District High School Relief Center",
            "latitude": 25.345,
            "longitude": 83.040,
            "capacity": 3000,
            "current_occupancy": 800,
            "food_stock_days": 7,
            "water_supply": "functional",
            "status": "open",
            "road_accessibility": "open"
        }
    ]
    
    ranked = rank_safe_zones_for_zone(affected_zone, safe_zones)
    
    # S_SAFE must be ranked #1 despite being slightly further
    assert ranked[0]["safeZoneId"] == "S_SAFE"
    assert ranked[0]["rank"] == 1
    assert ranked[0]["suitabilityScore"] > ranked[1]["suitabilityScore"]
    assert ranked[0]["safetyScore"] > ranked[1]["safetyScore"]


# ── EVACUATION LIFECYCLE & PEOPLE TRACKING ────────────────────────────────────────
def test_evacuation_lifecycle_and_people_tracking():
    source_zone = {
        "id": "Z01",
        "name": "Rampur Tanda",
        "population": 4200,
        "affected_population": 3800,
        "damage_percentage": 65,
        "hospital_status": "unavailable",
        "water_availability": "none",
        "road_accessibility": "open",
        "hci_score": 88.0
    }
    safe_zones = [
        {
            "id": "S1",
            "name": "Safe Haven Center",
            "latitude": 25.340,
            "longitude": 83.050,
            "capacity": 4000,
            "current_occupancy": 200,
            "food_stock_days": 5,
            "water_supply": "functional",
            "status": "open",
            "road_accessibility": "open"
        }
    ]
    resources = [
        {"id": "BUS01", "type": "bus", "capacity": 40, "status": "AVAILABLE", "speed_kmh": 45, "fuel_pct": 95},
        {"id": "BUS02", "type": "bus", "capacity": 40, "status": "AVAILABLE", "speed_kmh": 45, "fuel_pct": 90},
        {"id": "VAN01", "type": "rescue_van", "capacity": 15, "status": "AVAILABLE", "speed_kmh": 50, "fuel_pct": 95},
    ]
    
    # 1. Create Plan
    plan = create_evacuation_plan(source_zone, safe_zones, available_resources=resources)
    assert plan["status"] == "RESOURCE_ASSIGNED"
    assert plan["peopleAtRisk"] == 3800
    assert plan["peopleTracking"]["peopleAtRisk"] == 3800
    assert plan["peopleTracking"]["peopleRemaining"] == 3800
    assert plan["peopleTracking"]["peopleEvacuated"] == 0
    assert len(plan["assignedResources"]) == 3
    
    # 2. Transition to MOVING_TO_ZONE
    plan = update_evacuation_progress(plan, "MOVING_TO_ZONE")
    assert plan["status"] == "MOVING_TO_ZONE"
    
    # 3. Transition to EVACUATING
    plan = update_evacuation_progress(plan, "EVACUATING")
    assert plan["status"] == "EVACUATING"
    assert plan["peopleTracking"]["peoplePickedUp"] > 0
    
    # 4. Transition to EN_ROUTE_TO_SAFE_ZONE
    plan = update_evacuation_progress(plan, "EN_ROUTE_TO_SAFE_ZONE")
    assert plan["status"] == "EN_ROUTE_TO_SAFE_ZONE"
    assert plan["peopleTracking"]["peopleInTransit"] > 0
    
    # 5. Transition to ARRIVED_SAFE_ZONE
    plan = update_evacuation_progress(plan, "ARRIVED_SAFE_ZONE")
    assert plan["status"] == "ARRIVED_SAFE_ZONE"
    assert plan["peopleTracking"]["peopleInTransit"] == 0
    assert plan["peopleTracking"]["peopleEvacuated"] > 0
    
    # 6. Complete Evacuation
    plan = update_evacuation_progress(plan, "COMPLETED")
    assert plan["status"] == "COMPLETED"
    assert plan["peopleTracking"]["peopleEvacuated"] == 3800
    assert plan["peopleTracking"]["peopleRemaining"] == 0


# ── REST API ENDPOINTS INTEGRATION TESTS ─────────────────────────────────────────
def test_api_evacuation_affected_zones(client):
    res = client.get("/api/evacuation/affected-zones")
    assert res.status_code == 200
    data = res.json()
    assert "zones" in data
    assert len(data["zones"]) > 0
    first = data["zones"][0]
    assert "peopleAtRisk" in first
    assert "evacuationPriority" in first
    assert "urgency" in first
    assert "remainingPopulationAtRisk" in first


def test_api_evacuation_safe_zones(client):
    res = client.get("/api/evacuation/safe-zones")
    assert res.status_code == 200
    data = res.json()
    assert "safe_zones" in data
    assert len(data["safe_zones"]) > 0
    first = data["safe_zones"][0]
    assert "safeZoneId" in first
    assert "availableCapacity" in first
    assert "safetyScore" in first


def test_api_evacuation_priority_calculation(client):
    res = client.post("/api/evacuation/priority", json={"zone_id": "Z01"})
    assert res.status_code == 200
    data = res.json()
    assert "evacuationPriority" in data
    assert "riskLevel" in data
    assert "urgency" in data
    assert data["evacuationPriority"] >= 80  # Z01 is critical


def test_api_evacuation_recommend_safe_zone(client):
    res = client.post("/api/evacuation/recommend-safe-zone", json={"zone_id": "Z01"})
    assert res.status_code == 200
    data = res.json()
    assert "ranked_safe_zones" in data
    ranked = data["ranked_safe_zones"]
    assert len(ranked) > 0
    assert ranked[0]["rank"] == 1
    assert ranked[0]["suitabilityScore"] >= ranked[-1]["suitabilityScore"]


def test_api_create_and_track_evacuation_plan(client):
    # 1. Create plan
    res = client.post("/api/evacuation/plan", json={"zone_id": "Z01", "people_at_risk": 3800})
    assert res.status_code == 200
    plan = res.json()
    plan_id = plan["planId"]
    assert plan["sourceZone"]["id"] == "Z01"
    assert plan["peopleAtRisk"] == 3800
    assert "destinations" in plan
    assert len(plan["destinations"]) > 0
    
    # 2. Get status
    res_status = client.get(f"/api/evacuation/status/{plan_id}")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["planId"] == plan_id
    assert "peopleTracking" in status_data
    
    # 3. Update progress to COMPLETED
    res_progress = client.post("/api/evacuation/progress", json={
        "plan_id": plan_id,
        "target_status": "COMPLETED",
        "note": "Full sector evacuation completed"
    })
    assert res_progress.status_code == 200
    updated = res_progress.json()
    assert updated["status"] == "COMPLETED"
    assert updated["peopleTracking"]["peopleEvacuated"] == 3800
    assert updated["peopleTracking"]["peopleRemaining"] == 0
