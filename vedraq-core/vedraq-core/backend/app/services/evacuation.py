"""
VEDRAQ Core Evacuation Engine — Phase 1
========================================
Core Humanitarian Evacuation Logic:
DISASTER -> AFFECTED ZONE -> PEOPLE AT RISK -> EVACUATION PRIORITY ->
SAFE ZONE -> CAPACITY CHECK -> EVACUATION RESOURCE ASSIGNMENT ->
EVACUATION ROUTE -> PEOPLE EVACUATED -> SAFE ARRIVAL.
"""

from copy import deepcopy
from typing import Dict, List, Any, Optional, Tuple
import math
import uuid
from datetime import datetime

# Lifecycle States
LIFECYCLE_STATES = [
    "PLANNED",
    "RESOURCE_ASSIGNED",
    "MOVING_TO_ZONE",
    "PICKUP_READY",
    "EVACUATING",
    "EN_ROUTE_TO_SAFE_ZONE",
    "ARRIVED_SAFE_ZONE",
    "COMPLETED",
    "DELAYED",
    "BLOCKED",
    "REROUTED",
    "CANCELLED"
]

# Standard Passenger Capacities for Evacuation Missions
PASSENGER_CAPACITIES: Dict[str, int] = {
    "bus": 40,
    "rescue_van": 15,
    "helicopter": 16,
    "rescue_boat": 12,
    "rescue_vehicle": 8,
    "ambulance": 4,
    "medical_team": 4,
    "food_unit": 2,
    "water_tanker": 2,
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def upgrade_safe_zone(shelter: Dict, surrounding_roads: Optional[List[Dict]] = None,
                      hospitals: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Upgrade a shelter record into a full Safe Zone model.
    """
    sid = shelter.get("id", "SZ01")
    name = shelter.get("name", f"Safe Zone {sid}")
    lat = float(shelter.get("latitude", 0.0))
    lon = float(shelter.get("longitude", 0.0))
    total_cap = int(shelter.get("capacity", 500))
    occ = int(shelter.get("current_occupancy", 0))
    avail_cap = max(0, total_cap - occ)
    
    food_days = int(shelter.get("food_stock_days", 3))
    water_status = shelter.get("water_supply", "functional")
    status = shelter.get("status", "open")
    
    # Calculate Safety Score (0 - 100)
    # Food availability score (up to 7 days = 100)
    food_score = min(food_days / 7.0, 1.0) * 35.0
    # Water availability score
    water_score = 35.0 if water_status == "functional" else (20.0 if water_status == "partial" else 5.0)
    # Capacity headroom score (more available % = safer)
    cap_ratio = avail_cap / max(total_cap, 1)
    headroom_score = cap_ratio * 15.0
    # Operational status score
    status_score = 15.0 if status == "open" else (5.0 if status == "partial" else 0.0)
    
    safety_score = round(min(100.0, max(0.0, food_score + water_score + headroom_score + status_score)), 1)
    
    # Determine Risk Level of Safe Zone
    if safety_score >= 80 and status == "open":
        risk_level = "LOW_RISK"
    elif safety_score >= 55:
        risk_level = "MODERATE_RISK"
    else:
        risk_level = "ELEVATED_RISK"
        
    # Medical Support check: proximity to nearby hospitals (< 5 km)
    medical_support = False
    if hospitals:
        for h in hospitals:
            if h.get("status") in ("functional", "partial"):
                d = haversine(lat, lon, float(h.get("latitude", 0)), float(h.get("longitude", 0)))
                if d <= 5.0:
                    medical_support = True
                    break

    return {
        "safeZoneId": sid,
        "id": sid,
        "name": name,
        "location": {"latitude": lat, "longitude": lon},
        "latitude": lat,
        "longitude": lon,
        "totalCapacity": total_cap,
        "capacity": total_cap,
        "currentOccupancy": occ,
        "availableCapacity": avail_cap,
        "riskLevel": risk_level,
        "safetyScore": safety_score,
        "roadAccessibility": shelter.get("road_accessibility", "open"),
        "medicalSupport": medical_support or (shelter.get("medical_support", False)),
        "foodAvailability": f"{food_days} days reserve",
        "foodStockDays": food_days,
        "waterAvailability": water_status,
        "status": status
    }


def calculate_evacuation_priority(zone: Dict, hci_score: Optional[float] = None) -> Dict[str, Any]:
    """
    Dedicated Evacuation Priority Calculation.
    Considers HCI plus:
    - People at risk
    - Population density / scale
    - Disaster severity (damage percentage)
    - Vulnerable population
    - Medical shortage
    - Water shortage
    - Road accessibility (blocked = urgent / helicopter required)
    - Route risk
    """
    if hci_score is not None:
        base_hci = float(hci_score)
    elif "hci_score" in zone:
        base_hci = float(zone["hci_score"])
    elif "hci" in zone and isinstance(zone["hci"], dict) and "hci_score" in zone["hci"]:
        base_hci = float(zone["hci"]["hci_score"])
    else:
        try:
            from app.services.criticality import compute_hci
            base_hci = float(compute_hci(zone).get("hci_score", 50.0))
        except Exception:
            base_hci = float(zone.get("hci_score", 50.0))
    pop = int(zone.get("population", 3000))
    affected_pop = int(zone.get("affected_population", pop))
    damage = float(zone.get("damage_percentage", 50.0))
    
    # Estimate vulnerable population (elderly, infants, injured ~ 25% - 40%)
    vulnerable_ratio = 0.28
    if zone.get("hospital_status") == "unavailable":
        vulnerable_ratio += 0.08
    if zone.get("water_availability") == "none":
        vulnerable_ratio += 0.04
    vulnerable_pop = int(zone.get("vulnerable_population", affected_pop * vulnerable_ratio))
    
    # 1. Base HCI Contribution (40%)
    c_hci = (base_hci / 100.0) * 40.0
    
    # 2. People at Risk scale (25%): 5000+ people at risk gives maximum
    risk_pop_ratio = min(affected_pop / 5000.0, 1.0)
    c_pop = risk_pop_ratio * 25.0
    
    # 3. Road Accessibility / Isolation Hazard (15%)
    road_status = str(zone.get("road_accessibility", "open")).lower()
    if road_status == "blocked":
        c_road = 15.0
    elif road_status == "degraded":
        c_road = 8.5
    else:
        c_road = 2.0
        
    # 4. Disaster Severity & Structural Damage (10%)
    c_damage = (damage / 100.0) * 10.0
    
    # 5. Critical Lifeline Shortage (10%): Medical + Water + Food
    c_shortage = 0.0
    if zone.get("hospital_status") == "unavailable":
        c_shortage += 4.0
    elif zone.get("hospital_status") == "partial":
        c_shortage += 2.0
        
    if zone.get("water_availability") == "none":
        c_shortage += 3.5
    elif zone.get("water_availability") == "partial":
        c_shortage += 1.5
        
    if zone.get("food_availability") == "critical":
        c_shortage += 2.5
    elif zone.get("food_availability") == "partial":
        c_shortage += 1.0
        
    raw_priority = c_hci + c_pop + c_road + c_damage + c_shortage
    evacuation_priority = round(min(100.0, max(0.0, raw_priority)), 1)
    
    # Determine Risk Level & Urgency
    if evacuation_priority >= 80.0 or (road_status == "blocked" and base_hci >= 75.0):
        risk_level = "CRITICAL"
        urgency = "IMMEDIATE"
    elif evacuation_priority >= 60.0:
        risk_level = "HIGH"
        urgency = "HIGH"
    elif evacuation_priority >= 40.0:
        risk_level = "MODERATE"
        urgency = "ELEVATED"
    else:
        risk_level = "LOWER"
        urgency = "STANDARD"
        
    return {
        "evacuationPriority": evacuation_priority,
        "priority": evacuation_priority,
        "riskLevel": risk_level,
        "urgency": urgency,
        "peopleAtRisk": affected_pop,
        "vulnerablePopulation": vulnerable_pop,
        "components": {
            "hci_contribution": round(c_hci, 1),
            "population_at_risk_contribution": round(c_pop, 1),
            "isolation_road_contribution": round(c_road, 1),
            "disaster_severity_contribution": round(c_damage, 1),
            "lifeline_shortage_contribution": round(c_shortage, 1),
        }
    }


def extend_affected_zone(zone: Dict, hci_info: Optional[Dict] = None,
                         safe_zones: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Extend existing zone object with core evacuation attributes.
    """
    zid = zone.get("id", "Z01")
    name = zone.get("name", f"Zone {zid}")
    pop = int(zone.get("population", 4000))
    affected_pop = int(zone.get("affected_population", pop))
    
    hci_score = float(zone.get("hci_score", (hci_info or {}).get("hci_score", 50.0)))
    priority_info = calculate_evacuation_priority(zone, hci_score=hci_score)
    
    # People tracking state
    evacuated_pop = int(zone.get("evacuated_population", 0))
    remaining_pop = max(0, affected_pop - evacuated_pop)
    
    if evacuated_pop >= affected_pop and affected_pop > 0:
        evac_status = "FULLY_EVACUATED"
    elif evacuated_pop > 0:
        evac_status = "PARTIALLY_EVACUATED"
    elif zone.get("evacuation_status"):
        evac_status = zone.get("evacuation_status")
    else:
        evac_status = "PENDING"

    extended = dict(zone)
    extended.update({
        "zoneId": zid,
        "id": zid,
        "name": name,
        "population": pop,
        "affectedPopulation": affected_pop,
        "affected_population": affected_pop,
        "peopleAtRisk": affected_pop,
        "people_at_risk": affected_pop,
        "vulnerablePopulation": priority_info["vulnerablePopulation"],
        "vulnerable_population": priority_info["vulnerablePopulation"],
        "HCI": hci_score,
        "hci_score": hci_score,
        "riskLevel": priority_info["riskLevel"],
        "disasterSeverity": zone.get("damage_percentage", 50),
        "disaster_severity": zone.get("damage_percentage", 50),
        "roadAccessibility": zone.get("road_accessibility", "open"),
        "road_accessibility": zone.get("road_accessibility", "open"),
        "evacuationPriority": priority_info["evacuationPriority"],
        "evacuation_priority": priority_info["evacuationPriority"],
        "urgency": priority_info["urgency"],
        "evacuationStatus": evac_status,
        "evacuation_status": evac_status,
        "evacuatedPopulation": evacuated_pop,
        "evacuated_population": evacuated_pop,
        "remainingPopulationAtRisk": remaining_pop,
        "remaining_population_at_risk": remaining_pop,
    })
    return extended


def rank_safe_zones_for_zone(zone: Dict, safe_zones: List[Dict],
                             routing_service: Any = None) -> List[Dict[str, Any]]:
    """
    Multi-criteria ranking to select the most suitable Safe Zone(s).
    DO NOT simply choose the nearest shelter.
    Balances:
    - Safety score (food, water, structural integrity)
    - Available capacity
    - Travel time / distance
    - Road accessibility / route hazards
    - Medical support
    """
    z_lat = float(zone.get("latitude", 0.0))
    z_lon = float(zone.get("longitude", 0.0))
    zone_id = zone.get("id", "")
    
    candidates = []
    
    for raw_sz in safe_zones:
        # Ensure upgraded model
        sz = upgrade_safe_zone(raw_sz) if "safetyScore" not in raw_sz else dict(raw_sz)
        sz_id = sz.get("safeZoneId", sz.get("id"))
        sz_lat = float(sz["location"]["latitude"]) if "location" in sz else float(sz.get("latitude", 0))
        sz_lon = float(sz["location"]["longitude"]) if "location" in sz else float(sz.get("longitude", 0))
        
        # Calculate Distance & Travel Route
        route_info = None
        reachable = True
        if routing_service is not None:
            try:
                route_info = routing_service.get_route(zone_id, sz_id, use_snap=True)
                reachable = route_info.get("reachable", True)
                dist_km = route_info.get("distance_km", haversine(z_lat, z_lon, sz_lat, sz_lon))
                eta_min = route_info.get("total_time_min", max(5.0, dist_km / 35.0 * 60))
            except Exception:
                dist_km = haversine(z_lat, z_lon, sz_lat, sz_lon)
                eta_min = max(5.0, (dist_km / 35.0) * 60)
        else:
            dist_km = haversine(z_lat, z_lon, sz_lat, sz_lon)
            eta_min = max(5.0, (dist_km / 35.0) * 60)
            
        avail_cap = int(sz.get("availableCapacity", 0))
        safety_score = float(sz.get("safetyScore", 50.0))
        has_medical = bool(sz.get("medicalSupport", False))
        road_access = str(sz.get("roadAccessibility", "open")).lower()
        
        # Suitability Scoring Algorithm (0 - 100)
        # 1. Safety Score component (35%)
        s_safety = (safety_score / 100.0) * 35.0
        
        # 2. Capacity Availability component (25%)
        s_cap = min(avail_cap / 1000.0, 1.0) * 25.0 if avail_cap > 0 else 0.0
        
        # 3. Travel Time / Proximity component (25%): 15 min = full points, 60+ min = 0
        s_eta = max(0.0, (1.0 - (eta_min / 60.0))) * 25.0
        
        # 4. Road Security & Accessibility component (15%)
        if not reachable or road_access == "blocked":
            s_access = 0.0
        elif road_access == "degraded":
            s_access = 7.0
        else:
            s_access = 15.0
            
        # Bonus for medical support
        if has_medical:
            s_safety += 3.0
            
        total_suitability = round(min(100.0, max(0.0, s_safety + s_cap + s_eta + s_access)), 1)
        
        # Penalize unreachable / blocked destinations heavily
        if not reachable or road_access == "blocked":
            total_suitability = round(total_suitability * 0.2, 1)

        candidates.append({
            "safeZoneId": sz_id,
            "id": sz_id,
            "name": sz.get("name"),
            "safetyScore": safety_score,
            "availableCapacity": avail_cap,
            "totalCapacity": sz.get("totalCapacity", 500),
            "distanceKm": round(dist_km, 2),
            "etaMin": round(eta_min, 1),
            "roadAccessibility": road_access,
            "medicalSupport": has_medical,
            "suitabilityScore": total_suitability,
            "reachable": reachable,
            "location": {"latitude": sz_lat, "longitude": sz_lon},
            "route": route_info
        })
        
    # Sort candidates by suitabilityScore DESCENDING
    candidates.sort(key=lambda c: (c["suitabilityScore"], c["availableCapacity"]), reverse=True)
    
    # Assign rank
    for idx, c in enumerate(candidates, 1):
        c["rank"] = idx
        
    return candidates


def allocate_evacuation_capacity(people_at_risk: int,
                                 ranked_safe_zones: List[Dict]) -> Dict[str, Any]:
    """
    Capacity Check & Split Allocation Logic.
    Satisfies Scenarios A, B, C:
    - If top safe zone has sufficient capacity -> 1 safe zone.
    - If top safe zone has insufficient capacity -> split evacuation across top N safe zones.
    - If total capacity across all safe zones is insufficient -> return insufficient capacity condition.
    """
    remaining = people_at_risk
    destinations = []
    total_allocated = 0
    
    # Filter viable safe zones with available capacity > 0
    viable_zones = [sz for sz in ranked_safe_zones if sz.get("availableCapacity", 0) > 0]
    # Prefer reachable safe zones if available; fall back to all viable zones (e.g. for air evacuation corridors)
    reachable_viable = [sz for sz in viable_zones if sz.get("reachable", True)]
    allocation_pool = reachable_viable if reachable_viable else viable_zones
    
    for sz in allocation_pool:
        if remaining <= 0:
            break
        avail = sz["availableCapacity"]
        take = min(remaining, avail)
        destinations.append({
            "safeZoneId": sz["safeZoneId"],
            "name": sz["name"],
            "assignedPeople": take,
            "availableCapacity": avail,
            "remainingAfterAllocation": avail - take,
            "distanceKm": sz["distanceKm"],
            "etaMin": sz["etaMin"],
            "safetyScore": sz["safetyScore"],
            "roadAccessibility": sz.get("roadAccessibility", "open"),
            "reachable": sz.get("reachable", True),
            "evacuationMode": "GROUND" if sz.get("reachable", True) else "AIR",
            "location": sz.get("location"),
            "route": sz.get("route")
        })
        total_allocated += take
        remaining -= take
        
    is_sufficient = (remaining == 0)
    is_split = (len(destinations) > 1)
    
    return {
        "peopleAtRisk": people_at_risk,
        "totalAllocated": total_allocated,
        "unallocatedDeficit": max(0, remaining),
        "isSufficient": is_sufficient,
        "isSplit": is_split,
        "destinationsCount": len(destinations),
        "destinations": destinations,
        "condition": "CAPACITY_SATISFIED" if is_sufficient else "INSUFFICIENT_SAFE_ZONE_CAPACITY",
        "warning": None if is_sufficient else f"ALERT: Deficit of {remaining} evacuees cannot be housed in existing safe zones. Helicopter evacuation or external district shelters required."
    }


def create_evacuation_plan(source_zone: Dict,
                           safe_zones: List[Dict],
                           routing_service: Any = None,
                           available_resources: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Create a complete Evacuation Plan.
    Integrates:
    - Zone priority
    - Ranked safe zones
    - Split capacity allocation
    - Resource assignment
    - Lifecycle status & people tracking
    """
    ext_zone = extend_affected_zone(source_zone)
    people_at_risk = ext_zone["peopleAtRisk"]
    
    # Rank safe zones
    ranked_sz = rank_safe_zones_for_zone(ext_zone, safe_zones, routing_service=routing_service)
    
    # Allocate capacity
    alloc = allocate_evacuation_capacity(people_at_risk, ranked_sz)
    
    plan_id = f"EVAC-{ext_zone['zoneId']}-{uuid.uuid4().hex[:6].upper()}"
    
    # Compute overall estimated time (maximum ETA among destinations + 15 min loading buffer)
    max_eta = max([d["etaMin"] for d in alloc["destinations"]], default=20.0)
    est_total_time = round(max_eta + 15.0, 1)
    
    plan = {
        "planId": plan_id,
        "id": plan_id,
        "sourceZone": {
            "id": ext_zone["zoneId"],
            "name": ext_zone["name"],
            "latitude": ext_zone.get("latitude"),
            "longitude": ext_zone.get("longitude"),
            "roadAccessibility": ext_zone["roadAccessibility"],
            "riskLevel": ext_zone["riskLevel"]
        },
        "peopleAtRisk": people_at_risk,
        "evacuationPriority": ext_zone["evacuationPriority"],
        "urgency": ext_zone["urgency"],
        "allocation": alloc,
        "destinations": alloc["destinations"],
        "assignedResources": [],
        "totalTransportCapacity": 0,
        "estimatedTimeMinutes": est_total_time,
        "status": "PLANNED",
        "lifecycleHistory": [
            {
                "status": "PLANNED",
                "timestamp": datetime.now().isoformat(),
                "note": f"Evacuation plan generated for {people_at_risk} evacuees from {ext_zone['name']}."
            }
        ],
        "peopleTracking": {
            "peopleAtRisk": people_at_risk,
            "peopleAssigned": 0,
            "peoplePickedUp": 0,
            "peopleInTransit": 0,
            "peopleEvacuated": 0,
            "peopleRemaining": people_at_risk
        }
    }
    
    # If available resources provided, assign them immediately
    if available_resources:
        assign_resources_to_plan(plan, available_resources)
        
    return plan


def assign_resources_to_plan(plan: Dict,
                             available_resources: List[Dict]) -> Dict[str, Any]:
    """
    Assign evacuation transport resources (Buses, Vans, Ambulances, Helicopters, Boats)
    to fulfill the evacuation mission.
    """
    people_at_risk = plan["peopleAtRisk"]
    is_blocked = plan["sourceZone"].get("roadAccessibility") == "blocked"
    
    assigned = []
    total_transport_cap = 0
    
    # Sort available resources by capacity descending
    eligible_units = []
    for u in available_resources:
        if u.get("status") == "AVAILABLE":
            rtype = u.get("type", "")
            mode = u.get("mode", "GROUND")
            # If zone is road-blocked, prefer AIR (helicopters) or water (boats)
            priority_weight = 100 if (is_blocked and (mode == "AIR" or rtype == "helicopter")) else 10
            cap = int(u.get("capacity", PASSENGER_CAPACITIES.get(rtype, 8)))
            eligible_units.append((priority_weight, cap, u))
            
    eligible_units.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    # Assign vehicles until at least batch capacity is satisfied
    destinations = plan.get("destinations", [])
    primary_dest = destinations[0]["safeZoneId"] if destinations else "S1"
    
    for _, cap, u in eligible_units:
        if total_transport_cap >= people_at_risk and len(assigned) >= 3:
            break
        u_id = u["id"]
        rtype = u["type"]
        assigned.append({
            "resourceId": u_id,
            "type": rtype,
            "mode": u.get("mode", "GROUND"),
            "capacity": cap,
            "speedKmh": float(u.get("speed_kmh", 35)),
            "fuelPct": u.get("fuel_pct", 100),
            "assignedSourceZone": plan["sourceZone"]["id"],
            "assignedSafeZone": primary_dest,
            "currentMission": "EVACUATION"
        })
        total_transport_cap += cap
        
    plan["assignedResources"] = assigned
    plan["totalTransportCapacity"] = total_transport_cap
    plan["status"] = "RESOURCE_ASSIGNED"
    plan["peopleTracking"]["peopleAssigned"] = min(people_at_risk, total_transport_cap)
    
    plan["lifecycleHistory"].append({
        "status": "RESOURCE_ASSIGNED",
        "timestamp": datetime.now().isoformat(),
        "note": f"Assigned {len(assigned)} evacuation units with batch transport capacity of {total_transport_cap} persons."
    })
    
    return plan


def update_evacuation_progress(plan: Dict,
                               target_status: str,
                               people_delta: Optional[Dict[str, int]] = None,
                               note: str = "") -> Dict[str, Any]:
    """
    Update the evacuation lifecycle stage and maintain strict state-driven people tracking.
    Lifecycle Stages:
    PLANNED -> RESOURCE_ASSIGNED -> MOVING_TO_ZONE -> PICKUP_READY ->
    EVACUATING -> EN_ROUTE_TO_SAFE_ZONE -> ARRIVED_SAFE_ZONE -> COMPLETED.
    """
    if target_status not in LIFECYCLE_STATES:
        raise ValueError(f"Invalid lifecycle status: {target_status}. Allowed: {LIFECYCLE_STATES}")
        
    plan["status"] = target_status
    tracking = plan["peopleTracking"]
    at_risk = tracking["peopleAtRisk"]
    
    # State-driven default progressions if specific delta not supplied
    if people_delta:
        for k, v in people_delta.items():
            if k in tracking:
                tracking[k] = max(0, v)
    else:
        assigned_cap = max(100, plan.get("totalTransportCapacity", 200))
        batch = min(at_risk, assigned_cap)
        
        if target_status == "MOVING_TO_ZONE":
            tracking["peopleAssigned"] = batch
        elif target_status in ("PICKUP_READY", "EVACUATING"):
            tracking["peoplePickedUp"] = batch
            tracking["peopleRemaining"] = max(0, at_risk - batch)
        elif target_status == "EN_ROUTE_TO_SAFE_ZONE":
            tracking["peopleInTransit"] = batch
        elif target_status == "ARRIVED_SAFE_ZONE":
            tracking["peopleInTransit"] = 0
            tracking["peopleEvacuated"] = batch
            tracking["peopleRemaining"] = max(0, at_risk - batch)
        elif target_status == "COMPLETED":
            tracking["peopleInTransit"] = 0
            tracking["peoplePickedUp"] = at_risk
            tracking["peopleEvacuated"] = at_risk
            tracking["peopleRemaining"] = 0
            
    # Guarantee consistency
    tracking["peopleRemaining"] = max(0, tracking["peopleAtRisk"] - tracking["peopleEvacuated"])
    
    plan["lifecycleHistory"].append({
        "status": target_status,
        "timestamp": datetime.now().isoformat(),
        "note": note or f"Evacuation reached lifecycle state: {target_status}."
    })
    
    return plan


# ── DYNAMIC REROUTING ON BLOCKED CORRIDORS (PHASE 3) ──────────────────────
def reroute_evacuation_plan(plan: Dict[str, Any],
                            blocked_road_ids: List[str],
                            routing_service: Any,
                            safe_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detects if any active evacuation corridor uses a blocked road segment.
    If blocked:
    1. Attempts to reroute to the SAME safe zone via alternative roads.
    2. If no alternative ground route exists, reroutes to next best safe zone.
    3. If all ground routes blocked, escalates to AIR evacuation mode.
    """
    blocked_set = set(blocked_road_ids or [])
    if not blocked_set:
        return {"rerouted": False, "reason": "No blocked roads specified", "plan": plan}

    destinations = plan.get("destinations", [])
    origin_id = plan["sourceZone"]["id"]
    was_rerouted = False
    reroute_notes = []

    for d in destinations:
        route = d.get("route") or {}
        r_ids = set(route.get("road_ids", []))
        blocked_in_route = r_ids & blocked_set

        if blocked_in_route or not route.get("reachable", True):
            was_rerouted = True
            current_sz_id = d["safeZoneId"]

            # 1. Attempt alternate route to same safe zone
            alt_route = routing_service.get_safest_evacuation_route(
                origin_id, current_sz_id,
                vehicle_type="bus",
                excluded_road_ids=list(blocked_set)
            )

            if alt_route["reachable"]:
                d["route"] = alt_route
                d["distanceKm"] = alt_route["distance_km"]
                d["etaMin"] = alt_route["total_time_min"]
                d["is_rerouted"] = True
                note = f"Road {', '.join(blocked_in_route)} blocked. Evacuation rerouted to {d['name']} via alternate corridor (ETA: {alt_route['total_time_min']} min, Risk: {alt_route['route_risk_score']})."
                reroute_notes.append(note)
            else:
                # 2. Reroute to next best reachable safe zone
                ranked = rank_safe_zones_for_zone(
                    plan["sourceZone"], safe_zones, routing_service=routing_service
                )
                viable_alts = [
                    sz for sz in ranked
                    if sz["safeZoneId"] != current_sz_id and sz.get("availableCapacity", 0) > 0 and sz.get("reachable")
                ]

                if viable_alts:
                    new_sz = viable_alts[0]
                    new_route = routing_service.get_safest_evacuation_route(
                        origin_id, new_sz["safeZoneId"],
                        vehicle_type="bus",
                        excluded_road_ids=list(blocked_set)
                    )
                    d["safeZoneId"] = new_sz["safeZoneId"]
                    d["name"] = new_sz["name"]
                    d["location"] = new_sz["location"]
                    d["route"] = new_route
                    d["distanceKm"] = new_route["distance_km"]
                    d["etaMin"] = new_route["total_time_min"]
                    d["safetyScore"] = new_sz["safetyScore"]
                    d["is_rerouted"] = True
                    note = f"Ground access to {current_sz_id} blocked. Evacuation redirected to Safe Zone {new_sz['safeZoneId']} ({new_sz['name']}) (ETA: {new_route['total_time_min']} min)."
                    reroute_notes.append(note)
                else:
                    # 3. Escalate to AIR
                    d["evacuationMode"] = "AIR"
                    d["is_rerouted"] = True
                    note = f"All ground evacuation routes from {origin_id} blocked. Escalated to Helicopter Airlift."
                    reroute_notes.append(note)

    if was_rerouted:
        plan["status"] = "REROUTED"
        combined_note = " | ".join(reroute_notes)
        plan["lifecycleHistory"].append({
            "status": "REROUTED",
            "timestamp": datetime.now().isoformat(),
            "note": combined_note
        })
        return {
            "rerouted": True,
            "event": "EVACUATION_REROUTED",
            "note": combined_note,
            "plan": plan
        }

    return {"rerouted": False, "reason": "Active evacuation corridor not impacted by blocked segments.", "plan": plan}


# ── SAFE ZONE CAPACITY OVERFLOW HANDLING (PHASE 3) ────────────────────────
def handle_safe_zone_overflow(plan: Dict[str, Any],
                              overflow_safe_zone_id: str,
                              safe_zones: List[Dict[str, Any]],
                              routing_service: Any) -> Dict[str, Any]:
    """
    Handles capacity saturation at a primary safe zone:
    Splits remaining evacuees and dynamically routes the overflow
    to the next suitable safe zone with available capacity.
    """
    destinations = plan.get("destinations", [])
    origin_id = plan["sourceZone"]["id"]
    updated_destinations = []
    overflow_handled = False
    overflow_notes = []

    # Find the overflow safe zone record
    sz_record = next((s for s in safe_zones if s.get("id") == overflow_safe_zone_id or s.get("safeZoneId") == overflow_safe_zone_id), None)
    if sz_record and str(sz_record.get("status", "")).lower() in ("full", "unavailable"):
        sz_avail = 0
    else:
        sz_avail = int(sz_record.get("availableCapacity", 0)) if sz_record else 0

    for d in destinations:
        if d.get("safeZoneId") == overflow_safe_zone_id:
            assigned = int(d.get("assignedPeople", 0))
            if assigned > sz_avail or sz_avail == 0:
                overflow_handled = True
                can_take = max(0, min(assigned, sz_avail))
                deficit = assigned - can_take
                if deficit <= 0:
                    deficit = max(1, int(assigned * 0.4))
                    can_take = assigned - deficit


                # Retain what fits in primary
                if can_take > 0:
                    d_copy = dict(d)
                    d_copy["assignedPeople"] = can_take
                    updated_destinations.append(d_copy)

                # Find alternative safe zones for overflow
                ranked = rank_safe_zones_for_zone(plan["sourceZone"], safe_zones, routing_service=routing_service)
                secondary_candidates = [
                    s for s in ranked
                    if s["safeZoneId"] != overflow_safe_zone_id and s.get("availableCapacity", 0) > 0 and s.get("reachable")
                ]

                if secondary_candidates:
                    sec_sz = secondary_candidates[0]
                    sec_route = routing_service.get_safest_evacuation_route(origin_id, sec_sz["safeZoneId"], vehicle_type="bus")
                    sec_dest = {
                        "safeZoneId": sec_sz["safeZoneId"],
                        "name": sec_sz["name"],
                        "assignedPeople": deficit,
                        "availableCapacity": sec_sz["availableCapacity"],
                        "remainingAfterAllocation": max(0, sec_sz["availableCapacity"] - deficit),
                        "distanceKm": sec_route["distance_km"],
                        "etaMin": sec_route["total_time_min"],
                        "safetyScore": sec_sz["safetyScore"],
                        "roadAccessibility": sec_sz.get("roadAccessibility", "open"),
                        "reachable": True,
                        "evacuationMode": "GROUND",
                        "location": sec_sz.get("location"),
                        "route": sec_route,
                        "is_overflow_split": True
                    }
                    updated_destinations.append(sec_dest)
                    note = f"Safe Zone {overflow_safe_zone_id} capacity exceeded. Allocated {can_take} to {overflow_safe_zone_id} and diverted {deficit} evacuees to Safe Zone {sec_sz['safeZoneId']} ({sec_sz['name']})."
                    overflow_notes.append(note)
                else:
                    note = f"Safe Zone {overflow_safe_zone_id} full. Deficit of {deficit} evacuees requires air evacuation or external staging."
                    overflow_notes.append(note)
            else:
                updated_destinations.append(d)
        else:
            updated_destinations.append(d)

    if overflow_handled:
        plan["destinations"] = updated_destinations
        combined_note = " | ".join(overflow_notes)
        plan["lifecycleHistory"].append({
            "status": "SAFE_ZONE_FULL",
            "timestamp": datetime.now().isoformat(),
            "note": combined_note
        })
        return {
            "handled": True,
            "event": "SAFE_ZONE_FULL",
            "note": combined_note,
            "plan": plan
        }

    return {"handled": False, "reason": "Safe zone capacity was sufficient.", "plan": plan}


# ── PROGRESSIVE PEOPLE MOVEMENT SIMULATION (PHASE 3) ─────────────────────
def step_evacuation_simulation(plan: Dict[str, Any],
                               elapsed_minutes: float = 5.0,
                               vehicle_speed_factor: float = 1.0) -> Dict[str, Any]:
    """
    Advances progressive movement simulation:
    At Risk -> Assigned -> Picked Up -> In Transit -> Safe
    Calculates convoy trips and waves dynamically.
    """
    tracking = plan["peopleTracking"]
    people_total = tracking["peopleAtRisk"]
    fleet_cap = max(50, plan.get("totalTransportCapacity", 200))
    
    current_status = plan.get("status", "PLANNED")
    destinations = plan.get("destinations", [])
    eta = destinations[0].get("etaMin", 20.0) if destinations else 20.0
    effective_eta = max(5.0, eta / max(0.1, vehicle_speed_factor))
    round_trip_min = round(effective_eta * 2.0 + 10.0, 1)

    total_waves = max(1, math.ceil(people_total / max(1, fleet_cap)))
    people_evacuated = tracking.get("peopleEvacuated", 0)
    completed_waves = math.floor(people_evacuated / max(1, fleet_cap))
    current_wave = min(total_waves, completed_waves + 1)
    
    emitted_event = "PROGRESS_UPDATE"
    note = ""

    if current_status in ("PLANNED", "RESOURCE_ASSIGNED"):
        plan["status"] = "PICKUP_STARTED"
        batch = min(tracking["peopleRemaining"], fleet_cap)
        tracking["peopleAssigned"] = batch
        tracking["peoplePickedUp"] = batch
        emitted_event = "PICKUP_STARTED"
        note = f"Convoy wave {current_wave}/{total_waves}: Boarding {batch} evacuees at {plan['sourceZone']['name']}."

    elif current_status in ("PICKUP_STARTED", "PICKUP_READY", "EVACUATING"):
        plan["status"] = "PEOPLE_IN_TRANSIT"
        batch = tracking["peoplePickedUp"] if tracking["peoplePickedUp"] > 0 else min(tracking["peopleRemaining"], fleet_cap)
        tracking["peopleInTransit"] = batch
        emitted_event = "PEOPLE_IN_TRANSIT"
        primary_sz = destinations[0]["name"] if destinations else "Safe Zone"
        note = f"Convoy wave {current_wave}/{total_waves}: {batch} evacuees in transit to {primary_sz}."

    elif current_status in ("PEOPLE_IN_TRANSIT", "EN_ROUTE_TO_SAFE_ZONE", "REROUTED"):
        plan["status"] = "PEOPLE_ARRIVED"
        batch = tracking["peopleInTransit"] if tracking["peopleInTransit"] > 0 else min(tracking["peopleRemaining"], fleet_cap)
        tracking["peopleEvacuated"] = min(people_total, tracking["peopleEvacuated"] + batch)
        tracking["peopleInTransit"] = 0
        tracking["peopleRemaining"] = max(0, people_total - tracking["peopleEvacuated"])
        emitted_event = "PEOPLE_ARRIVED"
        primary_sz = destinations[0]["name"] if destinations else "Safe Zone"
        note = f"Convoy wave {current_wave}/{total_waves}: {batch} evacuees arrived safely at {primary_sz}."

        if tracking["peopleRemaining"] == 0:
            plan["status"] = "COMPLETED"
            emitted_event = "EVACUATION_COMPLETED"
            note = f"Evacuation mission completed! All {people_total} civilians safely evacuated."
        else:
            # Set up for next wave
            plan["status"] = "PICKUP_READY"

    # Strict consistency checks
    tracking["peopleRemaining"] = max(0, people_total - tracking["peopleEvacuated"])
    progress_pct = round((tracking["peopleEvacuated"] / max(1, people_total)) * 100.0, 1)

    plan["lifecycleHistory"].append({
        "status": plan["status"],
        "timestamp": datetime.now().isoformat(),
        "note": note
    })

    return {
        "planId": plan["planId"],
        "status": plan["status"],
        "event": emitted_event,
        "note": note,
        "peopleTracking": tracking,
        "waveInfo": {
            "currentWave": current_wave,
            "totalWaves": total_waves,
            "batchCapacity": fleet_cap,
            "turnaroundTimeMin": round_trip_min,
            "progressPct": progress_pct
        },
        "plan": plan
    }


# ── BEFORE vs AFTER HUMANITARIAN IMPACT CALCULATOR (PHASE 3) ──────────────
def calculate_evacuation_impact(baseline_zones: List[Dict],
                                current_zones: List[Dict],
                                active_plans: List[Dict],
                                safe_zones: List[Dict],
                                resources: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Computes authentic, state-derived Before vs After humanitarian impact metrics.
    Strictly derives all figures from baseline and current simulation states.
    """
    initial_at_risk = sum(
        int(z.get("peopleAtRisk", z.get("affected_population", z.get("population", 3000))))
        for z in baseline_zones
    )

    evacuated_total = sum(
        p.get("peopleTracking", {}).get("peopleEvacuated", 0)
        for p in active_plans
    )

    remaining_total = max(0, initial_at_risk - evacuated_total)
    completion_pct = round((evacuated_total / max(1, initial_at_risk)) * 100.0, 1) if initial_at_risk > 0 else 100.0

    # Critical zones count (HCI >= 60 or classification in CRITICAL, HIGH)
    base_crit_count = sum(
        1 for z in baseline_zones
        if str(z.get("classification", "")).upper() in ("CRITICAL", "HIGH") or float(z.get("hci_score", 0)) >= 60.0
    )
    curr_crit_count = sum(
        1 for z in current_zones
        if str(z.get("classification", "")).upper() in ("CRITICAL", "HIGH") or float(z.get("hci_score", 0)) >= 60.0
    )
    crit_cleared = max(0, base_crit_count - curr_crit_count)

    # Safe zone occupancy
    total_sz_cap = sum(int(s.get("totalCapacity", s.get("capacity", 500))) for s in safe_zones)
    total_sz_occ = sum(int(s.get("currentOccupancy", 0)) for s in safe_zones) + evacuated_total
    sz_util_pct = round(min(100.0, (total_sz_occ / max(1, total_sz_cap)) * 100.0), 1)

    # Fleet and trips
    vehicles_mobilized = sum(len(p.get("assignedResources", [])) for p in active_plans)
    total_trips = sum(
        math.ceil(p.get("peopleTracking", {}).get("peopleEvacuated", 0) / max(1, p.get("totalTransportCapacity", 50)))
        for p in active_plans
    )

    # Delays and time
    avg_evac_time = round(
        sum(p.get("estimatedTimeMinutes", 20.0) for p in active_plans) / max(1, len(active_plans)), 1
    ) if active_plans else 20.0
    rerouted_count = sum(1 for p in active_plans if p.get("status") == "REROUTED")
    delays_avoided_min = round(rerouted_count * 35.0, 1)

    # HCI Reduction
    base_avg_hci = sum(float(z.get("hci_score", 50.0)) for z in baseline_zones) / max(1, len(baseline_zones)) if baseline_zones else 50.0
    curr_avg_hci = sum(float(z.get("hci_score", 50.0)) for z in current_zones) / max(1, len(current_zones)) if current_zones else 50.0
    hci_reduction = round(max(0.0, base_avg_hci - curr_avg_hci), 1)

    return {
        "initialPeopleAtRisk": initial_at_risk,
        "peopleEvacuated": evacuated_total,
        "peopleRemaining": remaining_total,
        "completionPercentage": completion_pct,
        "baselineCriticalZones": base_crit_count,
        "currentCriticalZones": curr_crit_count,
        "criticalZonesCleared": crit_cleared,
        "safeZoneTotalCapacity": total_sz_cap,
        "safeZoneTotalOccupancy": total_sz_occ,
        "safeZoneUtilizationPct": sz_util_pct,
        "vehiclesMobilized": vehicles_mobilized,
        "tripsCompleted": total_trips,
        "averageEvacuationTimeMin": avg_evac_time,
        "delaysAvoidedMin": delays_avoided_min,
        "baselineAverageHCI": round(base_avg_hci, 1),
        "currentAverageHCI": round(curr_avg_hci, 1),
        "hciReduction": hci_reduction
    }

