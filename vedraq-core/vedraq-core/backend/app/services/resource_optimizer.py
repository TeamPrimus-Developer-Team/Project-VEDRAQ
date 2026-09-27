"""
Resource-Impact Optimization Engine
=====================================
Strategy: Greedy impact-per-resource allocation.

For each available resource unit:
  1. Find all zones that need it AND are reachable.
  2. Simulate deploying the resource to that zone.
  3. Calculate expected HCI reduction (impact).
  4. Rank by impact descending.
  5. Allocate to highest-impact zone.
  6. Repeat until resource exhausted or no more need.

This is a greedy approximation. The code is structured so that
an OR-Tools ILP solver can replace the greedy loop later.

DISCLAIMER: Impact values are prototype estimates only.
"""

from typing import Dict, List, Any, Tuple
from copy import deepcopy
from .criticality import compute_hci

# ── Resource impact simulation ────────────────────────────────────────────────
# How much each resource improves each zone attribute (for HCI recalculation)

RESOURCE_EFFECTS: Dict[str, Dict[str, Any]] = {
    "water_tanker": {
        "water_availability": "partial",   # none → partial  or partial → adequate
        "water_upgrade_map": {"none": "partial", "partial": "adequate", "adequate": "adequate"},
    },
    "medical_team": {
        "hospital_status": "partial",
        "hospital_upgrade_map": {"unavailable": "partial", "partial": "functional", "functional": "functional"},
    },
    "ambulance": {
        # Ambulances reduce effective shelter distance (improves evacuation)
        "shelter_distance_reduction_km": 8,
    },
    "food_unit": {
        "food_availability": "partial",
        "food_upgrade_map": {"critical": "partial", "partial": "adequate", "adequate": "adequate"},
    },
    "rescue_boat": {
        # Boats help with road accessibility in flood zones
        "road_upgrade_map": {"blocked": "degraded", "degraded": "open", "open": "open"},
    },
    "helicopter": {
        "hospital_status": "partial",
        "hospital_upgrade_map": {"unavailable": "partial", "partial": "functional", "functional": "functional"},
    },
    "rescue_vehicle": {
        "road_upgrade_map": {"blocked": "degraded", "degraded": "open", "open": "open"},
    },
}


def simulate_resource_effect(zone: Dict, resource_type: str) -> Dict:
    """Apply a single resource to a zone copy and return modified zone."""
    z = deepcopy(zone)
    effects = RESOURCE_EFFECTS.get(resource_type, {})

    if resource_type == "water_tanker":
        current = z.get("water_availability", "none")
        z["water_availability"] = effects["water_upgrade_map"].get(current, current)

    elif resource_type == "medical_team":
        current = z.get("hospital_status", "unavailable")
        z["hospital_status"] = effects["hospital_upgrade_map"].get(current, current)

    elif resource_type == "ambulance":
        reduction = effects.get("shelter_distance_reduction_km", 0)
        z["shelter_distance_km"] = max(0.0, z.get("shelter_distance_km", 0) - reduction)

    elif resource_type == "food_unit":
        current = z.get("food_availability", "critical")
        z["food_availability"] = effects["food_upgrade_map"].get(current, current)

    elif resource_type == "rescue_boat":
        current = z.get("road_accessibility", "blocked")
        z["road_accessibility"] = effects["road_upgrade_map"].get(current, current)

    elif resource_type == "helicopter":
        current = z.get("hospital_status", "unavailable")
        z["hospital_status"] = effects.get("hospital_upgrade_map", {}).get(current, current)

    elif resource_type == "rescue_vehicle":
        current = z.get("road_accessibility", "blocked")
        z["road_accessibility"] = effects.get("road_upgrade_map", {}).get(current, current)

    return z


def compute_impact(zone: Dict, resource_type: str) -> float:
    """Return expected HCI reduction from deploying one resource unit."""
    before = compute_hci(zone)["hci_score"]
    modified_zone = simulate_resource_effect(zone, resource_type)
    after = compute_hci(modified_zone)["hci_score"]
    return round(before - after, 2)


def greedy_optimize(
    zones: List[Dict],
    inventory: Dict[str, Dict],
    routes: Dict[str, Dict], scored_zones: List[Dict], units: List[Dict] = None,
    routes_by_origin: Dict[str, Dict[str, Dict]] = None,
) -> List[Dict]:
    """
    Greedy allocation:
    Returns list of recommended dispatch actions sorted by priority.
    Each action: {zone_id, resource_type, impact, before_hci, after_hci, route}
    """
    # Working copies
    available_units = {}
    for unit in (units or []):
        if unit.get("status") == "AVAILABLE": available_units.setdefault(unit["type"], []).append(unit)
    zone_map = {z["id"]: deepcopy(z) for z in zones}
    hci_map = {z["id"]: z["hci_score"] for z in scored_zones}

    actions: List[Dict] = []
    max_iterations = 50  # safety limit

    for _ in range(max_iterations):
        best_action = None
        best_score = float("-inf")

        for resource_type, candidates in available_units.items():
            if not candidates: continue

            for zone_id, zone in zone_map.items():
                # Check if zone needs this resource
                req = zone.get("required_resources", {})
                if req.get(resource_type, 0) <= 0:
                    continue

                # Compute impact
                impact = compute_impact(zone, resource_type)
                if impact <= 0:
                    continue
                for selected in candidates:
                    origin = selected.get("base_id") or "DEPOT"
                    route_info = (routes_by_origin or {}).get(origin, routes).get(zone_id, {})
                    if not route_info.get("reachable", False): continue
                    score = impact * 100 - route_info["total_time_min"] - route_info["distance_km"] * .5
                    if score <= best_score: continue
                    best_score = score
                    best_action = {
                        "zone_id":       zone_id,
                        "zone_name":     zone["name"],
                        "resource_type": resource_type,
                        "resource_id": selected.get("id", resource_type.upper()),
                        "resource_mode": selected.get("mode", "GROUND"),
                        "origin": selected.get("base", "Resource Depot"), "origin_node": origin,
                        "impact":        impact,
                        "before_hci":    round(hci_map[zone_id], 1),
                        "after_hci":     round(hci_map[zone_id] - impact, 1),
                        "route":         route_info,
                    }

        if best_action is None:
            break

        # Commit action
        rid = best_action["resource_type"]
        zid = best_action["zone_id"]
        available_units[rid] = [u for u in available_units[rid] if u["id"] != best_action["resource_id"]]

        # Update zone state
        zone_map[zid] = simulate_resource_effect(zone_map[zid], rid)

        # Update HCI
        new_hci = compute_hci(zone_map[zid])["hci_score"]
        hci_map[zid] = new_hci
        best_action["after_hci"] = round(new_hci, 1)

        # Decrement requirement
        zone_map[zid]["required_resources"][rid] = max(
            0, zone_map[zid]["required_resources"].get(rid, 0) - 1
        )

        actions.append(best_action)

    # Sort by impact descending
    actions.sort(key=lambda a: -a["impact"])
    return actions


def build_recommendations(
    zones: List[Dict],
    scored_zones: List[Dict],
    inventory: Dict,
    routes: Dict, units: List[Dict] = None, routes_by_origin: Dict[str, Dict[str, Dict]] = None,
) -> Dict[str, Any]:
    """Entry point for optimization pipeline."""
    actions = greedy_optimize(zones, inventory, routes, scored_zones, units, routes_by_origin)

    total_impact = round(sum(a["impact"] for a in actions), 1)
    critical_addressed = len({a["zone_id"] for a in actions
                               if any(z["id"] == a["zone_id"] and z.get("classification") == "CRITICAL"
                                      for z in scored_zones)})
    return {
        "actions":           actions,
        "total_impact":      total_impact,
        "critical_addressed": critical_addressed,
        "resource_summary": {k: {"total": v["total"], "used": sum(1 for a in actions if a["resource_type"] == k), "remaining": max(0, v["available"] - sum(1 for a in actions if a["resource_type"] == k))} for k, v in inventory.items()},
    }
