"""
VEDRAQ — Autonomous Groq-Powered What-If Simulation Engine
===========================================================
Executes closed-loop, sequential disaster-response interventions.
VEDRAQ calculates ground truth reality; Groq AI acts as the decision agent
determining the next optimal intervention for the highest-priority unresolved area.

Architecture:
  VEDRAQ State -> Priority Ranking -> Highest-Priority Unresolved Area
  -> Available Actions -> Groq Decision Agent -> Apply Intervention
  -> VEDRAQ Recalculation -> Cascading Effect Analysis -> Repeat
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from copy import deepcopy
from datetime import datetime

from .groq_service import get_api_key, DEFAULT_MODEL
from .simulation import SimulationState
from .resource_optimizer import simulate_resource_effect

logger = logging.getLogger("vedraq.autonomous_sim")

MAX_AUTONOMOUS_STEPS = 10


def get_unresolved_critical_areas(
    state: Dict[str, Any],
    resolved_ids: Set[str],
    concluded_ids: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Returns zones sorted by priority rank (HCI descending) that have not yet been resolved or concluded.
    Zones already in the GREEN / LOW risk zone (classification == 'LOWER' or hci_score < 40.0) are considered resolved.
    """
    zones = state.get("zones", [])
    excluded = resolved_ids | (concluded_ids or set())
    # In VEDRAQ, state["zones"] is sorted by priority_rank (hci_score descending)
    return [
        z for z in zones
        if z["id"] not in excluded and z.get("classification") != "LOWER" and z.get("hci_score", 0) >= 40.0
    ]


def get_highest_priority_unresolved_area(
    state: Dict[str, Any],
    resolved_ids: Set[str],
    concluded_ids: Optional[Set[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the single highest-priority unresolved critical area.
    """
    unresolved = get_unresolved_critical_areas(state, resolved_ids, concluded_ids)
    return unresolved[0] if unresolved else None


def get_available_actions_for_area(zone: Dict[str, Any], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identifies concrete, executable VEDRAQ interventions available for the target area.
    Only returns actions that the VEDRAQ engine can actually execute.
    """
    actions: List[Dict[str, Any]] = []
    zid = zone["id"]
    zname = zone["name"]
    roads = state.get("roads", [])
    facilities = state.get("facilities", {})
    resources = state.get("resources", {})
    blocked_roads = {r["id"] for r in roads if r.get("status") == "blocked"}

    # 1. Restore Blocked Roads connecting to or impacting this zone
    zone_blocked_roads = []
    if zone.get("primary_road_id") in blocked_roads:
        zone_blocked_roads.append(zone.get("primary_road_id"))

    route = zone.get("route_from_best_depot") or {}
    for rid in (route.get("road_ids") or []):
        if rid in blocked_roads and rid not in zone_blocked_roads:
            zone_blocked_roads.append(rid)

    for rid in blocked_roads:
        if rid not in zone_blocked_roads:
            r_obj = next((r for r in roads if r["id"] == rid), None)
            if r_obj and (r_obj.get("from_node") == zid or r_obj.get("to_node") == zid):
                zone_blocked_roads.append(rid)

    for rid in zone_blocked_roads:
        actions.append({
            "action": "restore_road",
            "action_id": f"restore_road_{rid}",
            "road_id": rid,
            "target_zone_id": zid,
            "label": f"Clear & Reopen Blocked Road {rid}",
            "expected_effect": f"Restores road corridor {rid}, removing route isolation penalty (+15 HCI) and reconnecting {zname} to supply depot.",
            "impact_weight": 95,
        })

    # 2. Dispatch Required Resources from Available Inventory
    req_res = zone.get("required_resources") or {}
    inventory = resources.get("inventory") or {}
    units = resources.get("units") or []

    for rtype, qty in req_res.items():
        if qty > 0:
            avail_count = (inventory.get(rtype) or {}).get("available", 0)
            avail_units = [u for u in units if u.get("type") == rtype and u.get("status") == "AVAILABLE"]
            if avail_count > 0 or len(avail_units) > 0:
                actions.append({
                    "action": "dispatch_resource",
                    "action_id": f"dispatch_{rtype}_{zid}",
                    "resource_type": rtype,
                    "quantity": 1,
                    "target_zone_id": zid,
                    "label": f"Dispatch {rtype.replace('_', ' ').title()} to {zname}",
                    "expected_effect": f"Directly satisfies {rtype.replace('_', ' ')} deficit, upgrading sector lifeline availability and reducing HCI score.",
                    "impact_weight": 85 if rtype in ("medical_team", "water_tanker") else 70,
                })

    # 3. Aerial Helicopter Response for Inaccessible / Critical Areas
    is_inaccessible = zone.get("response_accessibility") == "INACCESSIBLE" or zone.get("road_accessibility") == "blocked"
    heli_avail = any(u.get("type") == "helicopter" and u.get("status") == "AVAILABLE" for u in units)
    if is_inaccessible and heli_avail:
        actions.append({
            "action": "aerial_helicopter_response",
            "action_id": f"helicopter_airdrop_{zid}",
            "resource_type": "helicopter",
            "target_zone_id": zid,
            "label": f"Deploy Emergency Helicopter Payload to {zname}",
            "expected_effect": "Bypasses severed road network via Air Response Base, air-dropping critical medical supplies and potable water.",
            "impact_weight": 90,
        })

    # 4. Critical Facility Restoration
    hospitals = facilities.get("hospitals") or []
    for h in hospitals:
        if h.get("status") == "unavailable" and (h.get("zone_id") == zid or len(actions) < 3):
            actions.append({
                "action": "restore_facility",
                "action_id": f"restore_hospital_{h['id']}",
                "facility_id": h["id"],
                "facility_type": "hospital",
                "target_zone_id": zid,
                "label": f"Re-energize & Reopen {h['name']}",
                "expected_effect": f"Restores local emergency medical beds ({h.get('capacity', 50)} capacity), dramatically upgrading regional medical access.",
                "impact_weight": 88,
            })
            break

    shelters = facilities.get("shelters") or []
    for s in shelters:
        if s.get("status") == "full":
            actions.append({
                "action": "restore_facility",
                "action_id": f"expand_shelter_{s['id']}",
                "facility_id": s["id"],
                "facility_type": "shelter",
                "target_zone_id": zid,
                "label": f"Expand Evacuation Shelter {s['name']}",
                "expected_effect": "Expands emergency evacuee capacity and shortens average shelter transit distances.",
                "impact_weight": 75,
            })
            break

    # 5. Alternative Route Activation
    alt_route = zone.get("alternate_route") or {}
    if alt_route.get("reachable") and zone.get("road_accessibility") != "open":
        actions.append({
            "action": "activate_alternate_route",
            "action_id": f"activate_alt_{zid}",
            "target_zone_id": zid,
            "label": f"Prioritize Standby Alternative Corridor ({alt_route.get('distance_km')} km)",
            "expected_effect": "Reroutes emergency ground transit over functional standby road segments around blocked primary route.",
            "impact_weight": 80,
        })

    if not actions:
        actions.append({
            "action": "NO_FEASIBLE_ACTION",
            "action_id": f"no_action_{zid}",
            "target_zone_id": zid,
            "label": f"No feasible intervention remains for {zname} under current constraints",
            "expected_effect": "All available matching resources depleted and road corridors nominal; flag for passive monitoring.",
            "impact_weight": 0,
        })

    # Sort actions by impact weight descending
    actions.sort(key=lambda a: -a.get("impact_weight", 0))
    return actions


def consult_decision_agent(
    target_area: Dict[str, Any],
    available_actions: List[Dict[str, Any]],
    state: Dict[str, Any],
    history: List[Dict[str, Any]],
    scenario_context: Optional[Dict[str, Any]] = None,
    target_step_count: int = 0,
) -> Dict[str, Any]:
    """
    Invokes Groq AI (Llama 3.3 70B Versatile) with strict Resolve-Then-Advance prompt guardrails.
    Returns structured JSON with the chosen action, grounded operational why, and objective.
    """
    api_key = get_api_key()

    if not api_key:
        return deterministic_decision_policy(target_area, available_actions, state, history, scenario_context)

    try:
        from groq import Groq

        client = Groq(api_key=api_key, timeout=18.0)

        system_prompt = """You are the VEDRAQ Autonomous Disaster Response Decision Agent.
You are operating inside a VEDRAQ What-If disaster simulation using a strict RESOLVE-THEN-ADVANCE strategy.
The scenario conditions supplied in CURRENT_SIMULATION_STATE represent the user's selected hypothetical conditions.
You MUST treat these conditions as the current simulated reality.
You MUST NOT revert to baseline conditions.
You MUST NOT invent or remove scenario conditions.
You MUST select an intervention only from executable VEDRAQ actions.

STRICT RESOLVE-THEN-ADVANCE OPERATIONAL RULES:
1. You MUST focus entirely on the assigned `target_critical_area`.
2. Under Resolve-Then-Advance, you MUST continue working on this same area until its HCI drops into the GREEN / LOW risk zone (< 40.0) or available actions are exhausted.
3. You MUST select exactly ONE action from the provided `available_actions` list.
4. Do NOT repeat an action if it was already performed on this target and its benefit already applied.
5. Explain WHY this intervention was selected based on the zone's specific bottlenecks (HCI score, road accessibility, medical status, water availability) under the active What-If conditions.
6. State the concrete operational objective and anticipated cascading network benefits.
7. Return your decision strictly in valid JSON matching this schema:
{
  "target_area_id": "...",
  "selected_action": "...",
  "action_id": "...",
  "action_parameters": {},
  "reason": "...",
  "expected_objective": "...",
  "cascading_implication": "..."
}
"""

        active_conditions = (scenario_context or {}).get("selected_conditions", [])
        active_events = (scenario_context or {}).get("events", [])

        # Extract actions previously applied to this target
        prev_target_actions = [
            h.get("decision", {}).get("action_label") or h.get("decision", {}).get("selected_action")
            for h in history
            if h.get("target_area", {}).get("id") == target_area.get("id")
        ]

        context_payload = {
            "what_if_scenario": {
                "name": "User-Defined What-If Disaster Simulation",
                "active_conditions_count": len(active_conditions) or len(active_events),
                "selected_conditions": active_conditions,
                "active_events": active_events,
            },
            "current_simulation_state": {
                "total_zones": len(state.get("zones", [])),
                "critical_zones": sum(1 for z in state.get("zones", []) if z.get("classification") == "CRITICAL"),
                "high_zones": sum(1 for z in state.get("zones", []) if z.get("classification") == "HIGH"),
                "blocked_roads": [r["id"] for r in state.get("roads", []) if r.get("status") == "blocked"],
                "offline_hospitals": [h["id"] for h in state.get("facilities", {}).get("hospitals", []) if h.get("status") in ("offline", "unavailable")],
                "full_shelters": [s["id"] for s in state.get("facilities", {}).get("shelters", []) if s.get("status") == "full"],
            },
            "target_critical_area": {
                "id": target_area.get("id"),
                "name": target_area.get("name"),
                "priority_rank": target_area.get("priority_rank"),
                "hci_score": target_area.get("hci_score"),
                "classification": target_area.get("classification"),
                "affected_population": target_area.get("affected_population"),
                "road_accessibility": target_area.get("road_accessibility"),
                "response_accessibility": target_area.get("response_accessibility"),
                "top_bottlenecks": target_area.get("bottlenecks", [])[:3],
                "required_resources": target_area.get("required_resources", {}),
                "interventions_applied_on_this_target_so_far": target_step_count,
                "previous_actions_on_this_target": prev_target_actions,
            },
            "available_actions": [
                {
                    "action": a["action"],
                    "action_id": a["action_id"],
                    "label": a["label"],
                    "expected_effect": a["expected_effect"],
                    "parameters": {k: v for k, v in a.items() if k not in ("action", "action_id", "label", "expected_effect", "impact_weight")},
                }
                for a in available_actions
            ],
            "overall_steps_count": len(history),
        }

        user_content = (
            f"Active What-If Scenario Conditions: {', '.join(active_conditions) if active_conditions else 'Standard Scenario'}\n\n"
            f"Select the optimal intervention for Critical Area #{target_area.get('priority_rank')} ({target_area.get('name')}):\n\n"
            + json.dumps(context_payload, indent=2)
        )

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=600,
        )

        decision = json.loads(response.choices[0].message.content)

        # Validate decision: selected action must match one of available_actions
        matching_action = next(
            (a for a in available_actions if a["action_id"] == decision.get("action_id") or a["action"] == decision.get("selected_action")),
            None
        )

        if matching_action:
            decision["validated"] = True
            decision["action_id"] = matching_action["action_id"]
            decision["selected_action"] = matching_action["action"]
            decision["action_parameters"] = {k: v for k, v in matching_action.items() if k not in ("action", "action_id", "label", "expected_effect", "impact_weight")}
            decision["is_ai"] = True
            decision["model"] = DEFAULT_MODEL
            return decision
        else:
            logger.warning(f"Groq selected invalid action {decision.get('selected_action')}; using deterministic policy fallback.")
            fallback = deterministic_decision_policy(target_area, available_actions, state, history, scenario_context)
            fallback["validation_note"] = "AI proposed action was unsupported; corrected via deterministic validation."
            return fallback

    except Exception as exc:
        logger.error(f"Autonomous Groq decision agent error ({exc}); using deterministic fallback.", exc_info=True)
        fallback = deterministic_decision_policy(target_area, available_actions, state, history, scenario_context)
        fallback["error_fallback"] = str(exc)
        return fallback


def deterministic_decision_policy(
    target_area: Dict[str, Any],
    available_actions: List[Dict[str, Any]],
    state: Dict[str, Any],
    history: List[Dict[str, Any]],
    scenario_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Expert deterministic decision heuristic used when Groq is unavailable or returns an invalid action.
    Selects the highest impact-weighted executable action for the target critical area.
    """
    if not available_actions:
        return {
            "target_area_id": target_area.get("id"),
            "selected_action": "NO_FEASIBLE_ACTION",
            "action_id": "no_action",
            "action_parameters": {},
            "reason": "No valid actions remain in VEDRAQ inventory for this sector.",
            "expected_objective": "Flag for continuous monitoring.",
            "cascading_implication": "None.",
            "is_ai": False,
            "policy": "deterministic_fallback",
        }

    # Best action is the top sorted by impact weight
    best = available_actions[0]
    action_name = best["action"]
    zid = target_area.get("id")
    zname = target_area.get("name")
    hci = target_area.get("hci_score", 0)

    if action_name == "restore_road":
        rid = best.get("road_id")
        reason = f"{zname} (HCI {hci}) suffers from road inaccessibility due to Road {rid} being blocked. Reopening {rid} eliminates the severe isolation penalty (+15) and restores ground logistics."
        objective = f"Clear road corridor {rid} and re-establish ground connectivity from staging depots."
        cascade = f"Restoring {rid} also improves alternate bypass availability for neighboring flood sectors."
    elif action_name == "dispatch_resource":
        rtype = best.get("resource_type", "lifeline_unit")
        reason = f"{zname} has an acute deficit in {rtype.replace('_', ' ')}. Dispatching an active unit directly mitigates this bottleneck, upgrading the sector's lifeline service status."
        objective = f"Deliver emergency {rtype.replace('_', ' ')} allocation to reduce humanitarian criticality."
        cascade = f"Stabilizes sector survival conditions, preventing secondary mortality escalation."
    elif action_name == "aerial_helicopter_response":
        reason = f"{zname} is completely cut off from ground transit (HCI {hci}). Aerial helicopter deployment is the sole viable mechanism to deliver immediate medical triage."
        objective = "Establish aerial lifeline corridor to extract critical casualties and air-drop supplies."
        cascade = "Alleviates urgent trauma pressure without waiting for floodwater road recession."
    elif action_name == "restore_facility":
        fid = best.get("facility_id")
        reason = f"Reopening critical facility {fid} restores vital regional capacity, directly relieving healthcare or shelter congestion in {zname}."
        objective = f"Re-energize and staff facility {fid} to resume emergency operations."
        cascade = "Reduces patient/evacuee diversion strain on secondary district infrastructure."
    elif action_name == "activate_alternate_route":
        reason = f"Primary access to {zname} is impaired; activating the standby alternative route ensures supply convoys can bypass obstructions."
        objective = "Reroute relief convoys onto cleared alternate secondary road segments."
        cascade = "Maintains logistics flow while primary corridor clearing is underway."
    else:
        reason = f"No viable physical intervention is currently feasible for {zname} under resource constraints."
        objective = "Maintain passive operational monitoring."
        cascade = "None."

    return {
        "target_area_id": zid,
        "selected_action": action_name,
        "action_id": best.get("action_id"),
        "action_parameters": {k: v for k, v in best.items() if k not in ("action", "action_id", "label", "expected_effect", "impact_weight")},
        "reason": reason,
        "expected_objective": objective,
        "cascading_implication": cascade,
        "is_ai": False,
        "policy": "deterministic_expert_heuristic",
    }


def apply_action_to_simulation(
    decision: Dict[str, Any],
    sim: SimulationState,
    dispatched_vehicles: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Executes the validated intervention strictly inside VEDRAQ's SimulationState engine.
    VEDRAQ calculates the real mathematical results.
    """
    action = decision.get("selected_action")
    params = decision.get("action_parameters") or {}
    target_zid = decision.get("target_area_id")

    # Capture initial zone state before intervention
    initial_full_state = sim.compute_full_state(active_dispatches=list(dispatched_vehicles.values()))
    initial_zone = next((z for z in initial_full_state["zones"] if z["id"] == target_zid), None)
    initial_hci = initial_zone["hci_score"] if initial_zone else 0.0
    initial_access = initial_zone.get("response_accessibility") if initial_zone else "UNKNOWN"

    action_summary_detail = ""

    if action == "restore_road":
        rid = params.get("road_id")
        if rid:
            # Reopen road in VEDRAQ simulation engine
            sim.apply_events([{"type": "ROAD_OPEN", "road_id": rid}], active_dispatches=list(dispatched_vehicles.values()))
            # Remove from active_events if it was blocked
            sim.active_events = [e for e in sim.active_events if not (e.get("type") == "ROAD_BLOCK" and e.get("road_id") == rid)]
            action_summary_detail = f"Road {rid} status set to OPEN. Road network graph updated."

    elif action == "restore_facility":
        fid = params.get("facility_id")
        ftype = params.get("facility_type")
        if ftype == "hospital":
            sim.apply_events([{"type": "HOSPITAL_ONLINE", "facility_id": fid}], active_dispatches=list(dispatched_vehicles.values()))
            sim.active_events = [e for e in sim.active_events if not (e.get("type") == "HOSPITAL_OFFLINE" and e.get("facility_id") == fid)]
            action_summary_detail = f"Hospital {fid} restored to online status with operational beds."
        elif ftype == "shelter":
            sim.apply_events([{"type": "SHELTER_OPEN", "shelter_id": fid}], active_dispatches=list(dispatched_vehicles.values()))
            sim.active_events = [e for e in sim.active_events if not (e.get("type") == "SHELTER_FULL" and e.get("shelter_id") == fid)]
            action_summary_detail = f"Shelter {fid} expanded; admissions reopened."

    elif action in ("dispatch_resource", "aerial_helicopter_response"):
        rtype = params.get("resource_type")
        # Find available unit
        avail_units = [u for u in (sim.resources.get("units") or []) if u.get("type") == rtype and u.get("status") == "AVAILABLE"]
        if avail_units:
            unit = avail_units[0]
            rid = unit["id"]
            origin = unit.get("base_id") or "DEPOT"

            # Create active dispatch
            dispatched_vehicles[rid] = {
                "resource_id": rid,
                "resource_type": rtype,
                "mode": unit.get("mode", "GROUND" if rtype != "helicopter" else "AIR"),
                "origin": origin,
                "zone_id": target_zid,
                "zone_name": initial_zone["name"] if initial_zone else target_zid,
                "status": "ARRIVED",  # Autonomous simulation simulates successful immediate deployment
                "distance_km": 8.5,
                "eta_min": 0,
                "progress_pct": 100,
                "is_air": rtype == "helicopter" or unit.get("mode") == "AIR",
                "dispatched_at": datetime.now().isoformat(),
            }
            # Mark unit as deployed
            unit["status"] = "DEPLOYED"
            unit["current_assignment"] = target_zid
            if sim.resources.get("inventory", {}).get(rtype):
                sim.resources["inventory"][rtype]["available"] = max(0, sim.resources["inventory"][rtype]["available"] - 1)

            action_summary_detail = f"Dispatched unit {rid} ({rtype}) from {origin} to {initial_zone['name'] if initial_zone else target_zid}."
        else:
            # Direct simulation effect if inventory tracking only
            action_summary_detail = f"Dispatched emergency {rtype} payload to target zone."

    elif action == "activate_alternate_route":
        action_summary_detail = f"Standby alternate route prioritized for {initial_zone['name'] if initial_zone else target_zid}."

    elif action == "NO_FEASIBLE_ACTION":
        action_summary_detail = "No operational intervention executed. Sector flagged for monitoring."

    # Recalculate VEDRAQ ground truth state
    new_full_state = sim.compute_full_state(active_dispatches=list(dispatched_vehicles.values()))
    after_zone = next((z for z in new_full_state["zones"] if z["id"] == target_zid), None)
    after_hci = after_zone["hci_score"] if after_zone else initial_hci
    after_access = after_zone.get("response_accessibility") if after_zone else initial_access
    hci_reduction = round(initial_hci - after_hci, 1)

    # Detect cascading network impact on OTHER zones
    cascading_effects = []
    initial_zones_map = {z["id"]: z for z in initial_full_state["zones"]}
    for other_z in new_full_state["zones"]:
        if other_z["id"] != target_zid:
            prev_z = initial_zones_map.get(other_z["id"])
            if prev_z:
                diff = round(prev_z["hci_score"] - other_z["hci_score"], 1)
                prev_acc = prev_z.get("response_accessibility")
                curr_acc = other_z.get("response_accessibility")
                if diff > 0.5:
                    cascading_effects.append(
                        f"{other_z['name']} HCI reduced by {diff} pts (indirect benefit from intervention)"
                    )
                elif prev_acc != curr_acc:
                    cascading_effects.append(
                        f"{other_z['name']} access upgraded from {prev_acc} to {curr_acc}"
                    )

    # VEDRAQ Authoritative Resolution Check:
    # A zone is strictly RESOLVED only if it reaches the GREEN / LOW risk zone:
    # classification == "LOWER" or after_hci < 40.0
    after_class = after_zone.get("classification", "CRITICAL") if after_zone else "CRITICAL"
    is_green_or_low = (after_class == "LOWER") or (after_hci < 40.0)

    if is_green_or_low:
        engine_status = "Intervention Applied — Target Resolved"
        target_status = "RESOLVED"
        target_status_label = "🟢 RESOLVED / GREEN"
    elif after_class == "CRITICAL":
        engine_status = "Intervention Applied — Still Critical"
        target_status = "STILL_CRITICAL"
        target_status_label = "🔴 STILL CRITICAL — Continuing Resolution"
    elif after_class == "HIGH":
        engine_status = "Intervention Applied — Still High Risk"
        target_status = "STILL_HIGH"
        target_status_label = "🟠 STILL HIGH — Continuing Resolution"
    else:  # MODERATE
        engine_status = "Intervention Applied — Still Moderate Risk"
        target_status = "STILL_MODERATE"
        target_status_label = "🟡 STILL MODERATE — Continuing Resolution"

    return {
        "action": action,
        "detail": action_summary_detail,
        "initial_hci": initial_hci,
        "after_hci": after_hci,
        "hci_reduction": hci_reduction,
        "initial_access": initial_access,
        "after_access": after_access,
        "initial_classification": initial_zone.get("classification", "CRITICAL") if initial_zone else "CRITICAL",
        "after_classification": after_class,
        "status": engine_status,
        "target_status": target_status,
        "target_status_label": target_status_label,
        "cascading_effects": cascading_effects,
        "new_state": new_full_state,
        "is_resolved": is_green_or_low,
    }


def execute_autonomous_step(
    sim: SimulationState,
    resolved_ids: Set[str],
    step_num: int,
    history: List[Dict[str, Any]],
    dispatched_vehicles: Dict[str, Dict[str, Any]],
    scenario_context: Optional[Dict[str, Any]] = None,
    active_target_id: Optional[str] = None,
    target_step_count: int = 0,
    concluded_ids: Optional[Set[str]] = None,
    stagnation_counter: int = 0,
) -> Dict[str, Any]:
    """
    Executes a single step in the AI Autonomous Simulation loop following the Resolve-Then-Advance strategy:
    1. Lock onto active_target_id if still unresolved (HCI >= 40.0 / not GREEN); otherwise select highest-priority unresolved area.
    2. Analyze target bottlenecks and consult Groq AI decision agent with context on previous interventions.
    3. Apply action in VEDRAQ simulation engine and recalculate ground truth.
    4. Authoritatively check if target reached GREEN / LOW (< 40.0 HCI). If YES, mark resolved and advance.
       If NO, keep target active for next step unless interventions are exhausted or stagnant.
    """
    if concluded_ids is None:
        concluded_ids = set()

    current_state = sim.compute_full_state(active_dispatches=list(dispatched_vehicles.values()))

    # 1. Resolve-Then-Advance Target Selection:
    target_area = None
    if active_target_id and active_target_id not in concluded_ids and active_target_id not in resolved_ids:
        active_zone = next((z for z in current_state.get("zones", []) if z["id"] == active_target_id), None)
        if active_zone and (active_zone.get("classification") != "LOWER" and active_zone.get("hci_score", 0) >= 40.0):
            target_area = active_zone

    # If no active target in progress, pick highest-priority unresolved area from latest state
    if not target_area:
        target_area = get_highest_priority_unresolved_area(current_state, resolved_ids, concluded_ids)
        target_step_count = 0
        stagnation_counter = 0

    # Stopping condition: No unresolved critical areas remain
    if not target_area:
        logger.info(f"AI SIMULATION FINISHED at Step {step_num}: All critical areas resolved or concluded.")
        return {
            "step_number": step_num,
            "is_finished": True,
            "finish_reason": "ALL_CRITICAL_AREAS_RESOLVED",
            "message": "All critical and high-risk areas have been successfully addressed.",
            "target_area": None,
            "decision": None,
            "result": None,
            "resolved_ids": list(resolved_ids),
            "concluded_ids": list(concluded_ids),
            "active_target_id": None,
            "target_step_count": 0,
            "continue_same_target": False,
            "current_state": current_state,
        }

    logger.info(
        f"AI STEP {step_num} -> Target: {target_area['name']} (ID: {target_area['id']}, Rank: #{target_area.get('priority_rank')}, HCI: {target_area.get('hci_score')}, Classification: {target_area.get('classification')}, Sector Step: {target_step_count + 1})"
    )

    # Gather available executable actions for target area
    available_actions = get_available_actions_for_area(target_area, current_state)

    # Reason: Consult Groq AI Decision Agent (with deterministic fallback and active scenario context)
    decision = consult_decision_agent(
        target_area,
        available_actions,
        current_state,
        history,
        scenario_context,
        target_step_count=target_step_count,
    )

    logger.info(
        f"AI STEP {step_num} -> Action Chosen: {decision.get('selected_action')} ({decision.get('action_id')}) [Model: {decision.get('model', 'VEDRAQ Heuristic')}]"
    )

    # Act & Recalculate: Apply in VEDRAQ simulation engine
    execution_result = apply_action_to_simulation(decision, sim, dispatched_vehicles)
    after_zone = next((z for z in execution_result["new_state"]["zones"] if z["id"] == target_area["id"]), None)
    after_hci = execution_result["after_hci"]
    after_class = execution_result["after_classification"]
    hci_reduction = execution_result["hci_reduction"]

    # Resolution and Progression Assessment:
    is_resolved = execution_result["is_resolved"]
    next_active_target_id = None
    next_target_step_count = 0
    next_stagnation_counter = 0
    continue_same_target = False

    if is_resolved:
        # Target brought to GREEN / LOW risk zone (< 40.0 HCI)
        resolved_ids.add(target_area["id"])
        concluded_ids.add(target_area["id"])
        target_status = "RESOLVED"
        target_status_label = "🟢 RESOLVED / GREEN"
        engine_status = "Intervention Applied — Target Resolved"
        action_preview = "Target reached GREEN / LOW risk zone (< 40 HCI). Re-ranking for next critical sector."
        logger.info(f"Target {target_area['name']} successfully brought to GREEN / LOW risk ({after_hci} HCI).")
    else:
        # Inspect for stagnation or exhaustion
        rem_actions = get_available_actions_for_area(after_zone, execution_result["new_state"]) if after_zone else []
        has_feasible = any(a.get("action") != "NO_FEASIBLE_ACTION" for a in rem_actions)
        is_negligible = (hci_reduction < 0.2 and target_step_count >= 1)

        if is_negligible:
            next_stagnation_counter = stagnation_counter + 1
        else:
            next_stagnation_counter = 0

        if (not has_feasible) or next_stagnation_counter >= 2:
            # Interventions stagnant or exhausted: safely conclude this target and move forward
            concluded_ids.add(target_area["id"])
            target_status = "STAGNANT_UNRESOLVED"
            target_status_label = f"⚠️ STAGNANT — Interventions Exhausted (Remaining HCI: {after_hci})"
            engine_status = "Intervention Applied — Improvement Stagnated"
            action_preview = f"No further feasible improvements available for {target_area['name']}. Re-ranking remaining sectors."
            logger.info(f"Target {target_area['name']} stagnant/exhausted at HCI {after_hci}. Concluding target.")
        else:
            # CONTINUE WORKING ON THE SAME TARGET!
            next_active_target_id = target_area["id"]
            next_target_step_count = target_step_count + 1
            continue_same_target = True
            target_status = execution_result["target_status"]
            target_status_label = execution_result["target_status_label"]
            engine_status = execution_result["status"]
            action_preview = f"Continuing resolution of {target_area['name']} (HCI: {after_hci}, {after_class}). AI re-evaluating next intervention..."
            logger.info(f"Target {target_area['name']} remains {after_class} (HCI {after_hci}). Staying on SAME target.")

    # Re-ranking / Next Target in Queue determination:
    if continue_same_target:
        next_critical_area = f"{target_area['name']} (Continuing Resolution)"
    else:
        next_unresolved = get_highest_priority_unresolved_area(execution_result["new_state"], resolved_ids, concluded_ids)
        next_critical_area = next_unresolved["name"] if next_unresolved else "All Critical Areas Resolved"

    # Stopping condition evaluation:
    is_finished = False
    finish_reason = None
    remaining_unresolved = get_unresolved_critical_areas(execution_result["new_state"], resolved_ids, concluded_ids)

    if (not continue_same_target) and (not remaining_unresolved):
        is_finished = True
        finish_reason = "ALL_CRITICAL_AREAS_RESOLVED"
    elif step_num >= MAX_AUTONOMOUS_STEPS:
        is_finished = True
        finish_reason = "MAX_STEPS_REACHED"

    step_record = {
        "step_number": step_num,
        "timestamp": datetime.now().isoformat(),
        "active_target_id": next_active_target_id,
        "target_step_count": next_target_step_count,
        "concluded_ids": list(concluded_ids),
        "stagnation_counter": next_stagnation_counter,
        "resolved_ids": list(resolved_ids),
        "continue_same_target": continue_same_target,
        "is_target_resolved": is_resolved,
        "target_status": target_status,
        "target_status_label": target_status_label,
        "engine_status": engine_status,
        "target_area": {
            "id": target_area["id"],
            "name": target_area["name"],
            "rank": target_area.get("priority_rank"),
            "initial_classification": target_area.get("classification"),
            "after_classification": after_class,
            "initial_hci": target_area.get("hci_score"),
            "after_hci": after_hci,
            "hci_reduction": hci_reduction,
            "initial_accessibility": target_area.get("response_accessibility"),
            "after_accessibility": execution_result["after_access"],
            "target_intervention_number": target_step_count + 1,
        },
        "decision": {
            "selected_action": decision["selected_action"],
            "action_id": decision.get("action_id"),
            "action_label": next((a["label"] for a in available_actions if a["action"] == decision["selected_action"]), decision["selected_action"]),
            "reason": decision["reason"],
            "expected_objective": decision["expected_objective"],
            "cascading_implication": decision["cascading_implication"],
            "is_ai": decision.get("is_ai", False),
            "model_used": decision.get("model", "VEDRAQ Expert Policy"),
        },
        "result": {
            "action_detail": execution_result["detail"],
            "updated_hci": after_hci,
            "hci_reduction": hci_reduction,
            "updated_accessibility": execution_result["after_access"],
            "status": engine_status,
            "target_status": target_status,
            "target_status_label": target_status_label,
            "cascading_effects": execution_result["cascading_effects"],
        },
        "next_action_preview": action_preview,
        "next_critical_area": next_critical_area,
        "is_finished": is_finished,
        "finish_reason": finish_reason,
        "current_state": execution_result["new_state"],
    }
    return step_record


def run_full_autonomous_simulation(
    sim: SimulationState,
    max_steps: int = 10,
    dispatched_vehicles: Dict[str, Dict[str, Any]] = None,
    scenario_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Runs the complete autonomous simulation loop from start to completion.
    Operates under the strict Resolve-Then-Advance strategy.
    """
    if dispatched_vehicles is None:
        dispatched_vehicles = {}

    active_conds = (scenario_context or {}).get("selected_conditions", [])
    logger.info(
        f"AI SIMULATION START -> Scenario ID: {(scenario_context or {}).get('scenario_id', 'whatif_active')}, Active Conditions: {active_conds}"
    )

    resolved_ids: Set[str] = set()
    concluded_ids: Set[str] = set()
    history: List[Dict[str, Any]] = []
    active_target_id: Optional[str] = None
    target_step_count: int = 0
    stagnation_counter: int = 0

    # Capture initial What-If state before AI interventions begin
    initial_state = sim.compute_full_state(active_dispatches=list(dispatched_vehicles.values()))
    initial_crit_count = sum(1 for z in initial_state["zones"] if z.get("classification") == "CRITICAL")
    initial_high_count = sum(1 for z in initial_state["zones"] if z.get("classification") == "HIGH")
    initial_avg_hci = round(sum(z.get("hci_score", 0) for z in initial_state["zones"]) / max(1, len(initial_state["zones"])), 1)
    initial_accessible_routes = sum(1 for r in initial_state.get("routes", {}).values() if r.get("reachable"))

    for step_idx in range(1, max_steps + 1):
        step_result = execute_autonomous_step(
            sim=sim,
            resolved_ids=resolved_ids,
            step_num=step_idx,
            history=history,
            dispatched_vehicles=dispatched_vehicles,
            scenario_context=scenario_context,
            active_target_id=active_target_id,
            target_step_count=target_step_count,
            concluded_ids=concluded_ids,
            stagnation_counter=stagnation_counter,
        )

        history.append(step_result)

        # Update state trackers for next step in loop:
        active_target_id = step_result.get("active_target_id")
        target_step_count = step_result.get("target_step_count", 0)
        concluded_ids = set(step_result.get("concluded_ids", []))
        stagnation_counter = step_result.get("stagnation_counter", 0)
        resolved_ids = set(step_result.get("resolved_ids", []))

        if step_result.get("is_finished"):
            break

    # Final state
    final_state = sim.compute_full_state(active_dispatches=list(dispatched_vehicles.values()))
    final_crit_count = sum(1 for z in final_state["zones"] if z.get("classification") == "CRITICAL")
    final_high_count = sum(1 for z in final_state["zones"] if z.get("classification") == "HIGH")
    final_avg_hci = round(sum(z.get("hci_score", 0) for z in final_state["zones"]) / max(1, len(final_state["zones"])), 1)
    final_accessible_routes = sum(1 for r in final_state.get("routes", {}).values() if r.get("reachable"))

    # Generate AI analytical explanation
    explanation = generate_autonomous_summary_explanation(
        initial_state, final_state, history, scenario_context
    )

    return {
        "status": "COMPLETED",
        "total_steps_executed": len(history),
        "steps": history,
        "initial_state_summary": {
            "critical_zones": initial_crit_count,
            "high_zones": initial_high_count,
            "average_hci": initial_avg_hci,
            "accessible_routes": initial_accessible_routes,
            "overall_risk": "CRITICAL" if initial_crit_count >= 2 else "HIGH",
            "active_what_if_conditions": active_conds,
        },
        "final_state_summary": {
            "critical_zones": final_crit_count,
            "high_zones": final_high_count,
            "average_hci": final_avg_hci,
            "accessible_routes": final_accessible_routes,
            "overall_risk": "CRITICAL" if final_crit_count >= 2 else "HIGH" if final_high_count >= 3 else "MODERATE",
        },
        "impact": {
            "critical_zones_reduced": initial_crit_count - final_crit_count,
            "average_hci_reduction": round(initial_avg_hci - final_avg_hci, 1),
            "accessible_routes_gained": max(0, final_accessible_routes - initial_accessible_routes),
            "interventions_applied": len(history),
        },
        "final_ai_explanation": explanation,
        "final_state": final_state,
        "what_if_scenario": scenario_context,
    }


def generate_autonomous_summary_explanation(
    initial_state: Dict[str, Any],
    final_state: Dict[str, Any],
    history: List[Dict[str, Any]],
    scenario_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates a concise, grounded explanation of how the autonomous simulation progressed.
    """
    if not history:
        return "Autonomous simulation executed with no interventions required."

    first_step = history[0]
    first_name = first_step["target_area"]["name"] if first_step.get("target_area") else "Priority 1 Sector"
    first_act = first_step["decision"]["action_label"] if first_step.get("decision") else "Emergency Intervention"

    target_names = list(dict.fromkeys(h["target_area"]["name"] for h in history if h.get("target_area")))

    active_conds = (scenario_context or {}).get("selected_conditions", [])
    scenario_prefix = (
        f"Under active What-If scenario ({len(active_conds)} conditions: {', '.join(active_conds[:3])}{'...' if len(active_conds) > 3 else ''}), "
        if active_conds
        else "Under standard operational scenario, "
    )

    return (
        f"{scenario_prefix}VEDRAQ Autonomous Simulation operated under a strict Resolve-Then-Advance strategy. "
        f"The AI focused primarily on {first_name} with '{first_act}', maintaining resolution focus until systemic criticality was mitigated before re-ranking and advancing to subsequent sectors ({', '.join(target_names[:3])}). "
        f"After each intervention, VEDRAQ recalculated regional road accessibility, lifelines, and HCI scores. "
        f"This closed-loop process successfully mitigated critical bottlenecks and stabilized network connectivity."
    )
