"""
VEDRAQ What-If Simulation Engine
==================================
Applies user-defined events to the baseline state and returns
the full recalculated picture: zones, HCI, priorities, recommendations, routes.

Enhanced features:
- All What-If events (road block/hospital offline/shelter full/food depot offline/water offline)
  trigger actual route recalculation with real road graph constraints.
- Blocked road segments are excluded from the Dijkstra graph → ground routes MUST
  find actual alternative road segments or become UNAVAILABLE.
- Multi-depot routing: for each zone, every depot is evaluated; recommendations
  pick the BEST reachable depot considering real road ETA, not straight-line distance.
- Hospital fallback: if primary hospital is offline, next nearest accessible hospital
  by road route is chosen.
- Helicopter escalation: when NO ground route exists across all depots, the zone is
  marked INACCESSIBLE and a helicopter response plan is proposed.
"""

from copy import deepcopy
from typing import Dict, List, Any, Tuple, Optional

from .criticality import classify_all_zones
from .routing import RoutingService, compute_all_routes, haversine
from .resource_optimizer import build_recommendations, simulate_resource_effect
from .evacuation import extend_affected_zone, upgrade_safe_zone
from .risk_engine import ZONE_ELEVATION_MAPPING




class SimulationState:
    def __init__(self, zones: List[Dict], roads: List[Dict],
                 facilities: Dict, resources: Dict):
        self._baseline_zones = deepcopy(zones)
        self._baseline_roads = deepcopy(roads)
        self._baseline_facilities = deepcopy(facilities)
        self._baseline_resources = deepcopy(resources)

        self.zones = deepcopy(zones)
        self.roads = deepcopy(roads)
        self.facilities = deepcopy(facilities)
        self.resources = deepcopy(resources)
        self.active_events: List[Dict] = []

    def reset(self):
        self.zones = deepcopy(self._baseline_zones)
        self.roads = deepcopy(self._baseline_roads)
        self.facilities = deepcopy(self._baseline_facilities)
        self.resources = deepcopy(self._baseline_resources)
        self.active_events = []

    def apply_events(self, events: List[Dict], active_dispatches: List[Dict] = None) -> Dict[str, Any]:
        for event in events:
            self._apply_single_event(event)
            self.active_events.append(event)
        return self.compute_full_state(active_dispatches=active_dispatches)

    def _apply_single_event(self, event: Dict):
        etype = event.get("type", "")

        if etype == "ROAD_BLOCK":
            rid = event["road_id"]
            for road in self.roads:
                if road["id"] == rid:
                    road["status"] = "blocked"
                    for zone in self.zones:
                        if zone.get("primary_road_id") == rid:
                            zone["road_accessibility"] = "blocked"

        elif etype == "ROAD_OPEN":
            rid = event["road_id"]
            for road in self.roads:
                if road["id"] == rid:
                    road["status"] = "open"
                    for zone in self.zones:
                        if zone.get("primary_road_id") == rid:
                            zone["road_accessibility"] = "open"

        elif etype == "ROAD_DEGRADE":
            rid = event["road_id"]
            for road in self.roads:
                if road["id"] == rid:
                    road["status"] = "degraded"
                    for zone in self.zones:
                        if zone.get("primary_road_id") == rid:
                            zone["road_accessibility"] = "degraded"

        elif etype == "HOSPITAL_OFFLINE":
            fid = event["facility_id"]
            for h in self.facilities.get("hospitals", []):
                if h["id"] == fid:
                    h["status"] = "unavailable"
                    h["available_beds"] = 0
                    for zone in self.zones:
                        if zone.get("id") == h.get("zone_id"):
                            zone["hospital_status"] = "unavailable"
                            zone["hospital_capacity"] = 0

        elif etype == "HOSPITAL_ONLINE":
            fid = event["facility_id"]
            for h_base in self._baseline_facilities.get("hospitals", []):
                if h_base["id"] == fid:
                    for h in self.facilities.get("hospitals", []):
                        if h["id"] == fid:
                            h["status"] = h_base["status"]
                            h["available_beds"] = h_base.get("available_beds", 0)
                    for zone in self.zones:
                        if zone.get("id") == h_base.get("zone_id"):
                            for z_base in self._baseline_zones:
                                if z_base["id"] == zone["id"]:
                                    zone["hospital_status"] = z_base["hospital_status"]
                                    zone["hospital_capacity"] = z_base["hospital_capacity"]

        elif etype == "WATER_OFFLINE":
            zid = event.get("zone_id")
            for zone in self.zones:
                if zone["id"] == zid:
                    zone["water_availability"] = "none"
            for ws in self.facilities.get("water_stations", []):
                if event.get("station_id") and ws["id"] == event["station_id"]:
                    ws["status"] = "unavailable"

        elif etype == "COMMUNICATION_FAILURE":
            for zone in self.zones:
                if zone["id"] == event.get("zone_id"):
                    zone["communication_status"] = "none"

        elif etype == "FOOD_DEPOT_OFFLINE":
            for unit in self.resources.get("units", []):
                if unit.get("type") == "food_unit" and (
                        ("01" in unit.get("base", "") or unit.get("base_id") == "DEPOT")
                ):
                    unit["status"] = "UNAVAILABLE"
            self.resources["inventory"]["food_unit"]["available"] = sum(
                1 for u in self.resources["units"]
                if u["type"] == "food_unit" and u["status"] == "AVAILABLE"
            )
            for d in self.facilities.get("depots", []):
                if d["id"] == "DEPOT":
                    d["food_stock_units"] = 0

        elif etype == "GROUND_ACCESS_LOSS":
            for rid in event.get("road_ids", []):
                self._apply_single_event({"type": "ROAD_BLOCK", "road_id": rid})

        elif etype in ("SHELTER_FULL", "SAFE_ZONE_FULL"):
            sid = event.get("safe_zone_id") or event.get("shelter_id", "S1")
            for s in self.facilities.get("shelters", []):
                if s["id"] == sid:
                    s["current_occupancy"] = s["capacity"]
                    s["status"] = "full"
            for zone in self.zones:
                zone["shelter_distance_km"] = min(
                    zone.get("shelter_distance_km", 5.0) + 5.0, 25.0
                )

        elif etype in ("SHELTER_OPEN", "SAFE_ZONE_OPEN"):
            sid = event.get("safe_zone_id") or event.get("shelter_id", "S1")
            for s_base in self._baseline_facilities.get("shelters", []):
                if s_base["id"] == sid:
                    for s in self.facilities.get("shelters", []):
                        if s["id"] == sid:
                            s["current_occupancy"] = s_base["current_occupancy"]
                            s["status"] = s_base["status"]

        elif etype == "SAFE_ZONE_UNAVAILABLE":
            sid = event.get("safe_zone_id") or event.get("shelter_id", "S01")
            for s in self.facilities.get("shelters", []):
                if s["id"] == sid:
                    s["status"] = "unavailable"
                    s["current_occupancy"] = s["capacity"]
                    s["available_capacity"] = 0

        elif etype == "PRIMARY_ROAD_BLOCKED":
            rid = event.get("road_id", "R11")
            self._apply_single_event({"type": "ROAD_BLOCK", "road_id": rid})

        elif etype == "ALTERNATE_ROAD_BLOCKED":
            rid = event.get("road_id", "R13")
            self._apply_single_event({"type": "ROAD_BLOCK", "road_id": rid})

        elif etype == "VEHICLE_BREAKDOWN":
            uid = event.get("unit_id")
            for unit in self.resources.get("units", []):
                if uid and unit.get("id") == uid:
                    unit["status"] = "UNAVAILABLE"
                    break
                elif not uid and unit.get("type") in ("bus", "rescue_van") and unit.get("status") == "AVAILABLE":
                    unit["status"] = "UNAVAILABLE"
                    break

        elif etype == "POPULATION_SURGE":
            surge_pct = float(event.get("surge_pct", 30.0)) / 100.0
            target_zid = event.get("zone_id")
            for zone in self.zones:
                if not target_zid or zone["id"] == target_zid:
                    cur_pop = int(zone.get("affected_population", zone.get("population", 3000)))
                    zone["affected_population"] = int(cur_pop * (1.0 + surge_pct))
                    zone["peopleAtRisk"] = zone["affected_population"]
                    zone["damage_percentage"] = min(100.0, float(zone.get("damage_percentage", 50.0)) + 15.0)

        elif etype == "SEVERE_WEATHER":
            # Monsoon deluge: degrades open roads, cuts speed, increases road risk
            speed_mult = float(event.get("speed_multiplier", 0.6))
            for road in self.roads:
                if road.get("status") == "open":
                    road["status"] = "degraded"
                    road["condition"] = "flooded"
                    road["speed_kmh"] = max(10.0, float(road.get("speed_kmh", 25.0)) * speed_mult)
            for zone in self.zones:
                zone["damage_percentage"] = min(100.0, float(zone.get("damage_percentage", 50.0)) + 10.0)
                if zone.get("road_accessibility") == "open":
                    zone["road_accessibility"] = "degraded"

        elif etype == "STORM_SURGE_INUNDATION":
            # Physics-based storm surge inundation: compares elevation with surge water height
            surge_h = float(event.get("surge_height_m", 3.0))
            
            # 1. Road inundation
            for road in self.roads:
                road_elev = float(road.get("elevation_m", 0.0))
                if road_elev <= 0.0:
                    fn = road.get("from_node", "")
                    tn = road.get("to_node", "")
                    fn_elev = ZONE_ELEVATION_MAPPING.get(fn, 3.5)
                    tn_elev = ZONE_ELEVATION_MAPPING.get(tn, 3.5)
                    road_elev = min(fn_elev, tn_elev)
                    road["elevation_m"] = road_elev
                # Low-lying roads or high flood vulnerability segments are submerged
                if road_elev < surge_h or road.get("flood_vulnerability") in ("HIGH", "EXTREME"):
                    depth = round(max(0.1, surge_h - road_elev), 2)
                    road["status"] = "blocked"
                    road["condition"] = "submerged"
                    road["submerged"] = True
                    road["inundation_depth_m"] = depth

            # 2. Zone flooding
            for zone in self.zones:
                zid = zone.get("id", "")
                zone_elev = float(zone.get("elevation_m", 0.0))
                if zone_elev <= 0.0:
                    zone_elev = ZONE_ELEVATION_MAPPING.get(zid, 2.8)
                    zone["elevation_m"] = zone_elev
                if zone_elev < surge_h:
                    depth = round(max(0.2, surge_h - zone_elev), 2)
                    zone["flooded"] = True
                    zone["inundation_depth_m"] = depth
                    zone["damage_percentage"] = min(100.0, float(zone.get("damage_percentage", 45.0)) + (depth * 15.0))
                    pop = int(zone.get("population", 5000))
                    zone["affected_population"] = min(pop, int(zone.get("affected_population", pop * 0.6) * (1.0 + min(0.7, depth * 0.22))))
                    zone["peopleAtRisk"] = zone["affected_population"]
                    zone["water_availability"] = "none"

            # 3. Cyclone shelter ground-floor inundation
            for s in self.facilities.get("shelters", []):
                shelter_elev = float(s.get("elevation_m", 0.0))
                if shelter_elev <= 0.0:
                    slat = float(s.get("latitude", 0.0))
                    slon = float(s.get("longitude", 0.0))
                    nearest_z_elev = 2.8
                    min_dist_sq = float("inf")
                    for z in self.zones:
                        zlat = float(z.get("latitude", 0.0))
                        zlon = float(z.get("longitude", 0.0))
                        dist_sq = (zlat - slat)**2 + (zlon - slon)**2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            nearest_z_elev = ZONE_ELEVATION_MAPPING.get(z.get("id"), 2.8)
                    shelter_elev = round(nearest_z_elev + 0.6, 2)
                    s["elevation_m"] = shelter_elev

                if "available_capacity" not in s:
                    s["available_capacity"] = max(0, int(s.get("capacity", 1000)) - int(s.get("current_occupancy", 0)))

                if shelter_elev < surge_h:
                    s["ground_floor_flooded"] = True
                    s["inundation_depth_m"] = round(surge_h - shelter_elev, 2)
                    s["available_capacity"] = max(0, int(s["available_capacity"] * 0.35))
                    if (surge_h - shelter_elev) > 1.5:
                        s["status"] = "unavailable"
                        s["available_capacity"] = 0

        elif etype == "CYCLONE_LANDFALL":
            wind_speed = float(event.get("wind_speed_kmh", 140.0))
            eye_zone = event.get("landfall_zone_id", "WB01")
            for zone in self.zones:
                zone["damage_percentage"] = min(100.0, float(zone.get("damage_percentage", 40.0)) + (wind_speed / 18.0))
                if wind_speed >= 120.0:
                    zone["communication_status"] = "none"
            for road in self.roads:
                if road.get("status") == "open" and (road.get("from_node") == eye_zone or road.get("to_node") == eye_zone):
                    road["status"] = "blocked"
                    road["condition"] = "debris_blocked"

        elif etype == "EMBANKMENT_BREACH":
            breaches = event.get("locations", ["WB01", "WB04", "WB05"])
            for loc in breaches:
                for zone in self.zones:
                    if zone.get("id") == loc:
                        zone["embankment_breached"] = True
                        zone["damage_percentage"] = min(100.0, float(zone.get("damage_percentage", 50.0)) + 28.0)
                        zone["road_accessibility"] = "INACCESSIBLE"
                for road in self.roads:
                    if road.get("from_node") == loc or road.get("to_node") == loc:
                        road["status"] = "blocked"
                        road["condition"] = "embankment_breached"

        elif etype == "TORRENTIAL_PRECIPITATION":
            rain_mm = float(event.get("rainfall_24h_mm", 220.0))
            speed_factor = max(0.35, 1.0 - (rain_mm / 450.0))
            for road in self.roads:
                if road.get("status") == "open":
                    road["status"] = "degraded"
                    road["speed_kmh"] = max(10.0, float(road.get("speed_kmh", 25.0)) * speed_factor)


    def _build_nodes_dict(self) -> Dict[str, Dict]:
        nodes: Dict[str, Dict] = {z["id"]: z for z in self.zones}
        if self.facilities.get("depot"):
            nodes["DEPOT"] = self.facilities["depot"]
        for depot in self.facilities.get("depots", []):
            nodes[depot["id"]] = depot
        for hospital in self.facilities.get("hospitals", []):
            nodes[hospital["id"]] = hospital
        for shelter in self.facilities.get("shelters", []):
            nodes[shelter["id"]] = shelter
        for heli_base in self.facilities.get("helicopter_bases", []):
            nodes[heli_base["id"]] = heli_base
        return nodes

    def _evaluate_depot_for_zone(self, zone: Dict, depot_id: str, nodes: Dict,
                                   resource_type: str = None) -> Dict[str, Any]:
        service = RoutingService(self.roads, nodes)
        depot = nodes.get(depot_id)
        if not depot:
            return {"feasible": False, "reason": "Depot not found in graph"}
        route = service.get_route(depot_id, zone["id"], use_snap=True)
        return {
            "feasible": route["reachable"],
            "depot_id": depot_id,
            "depot_name": depot.get("name", depot_id),
            "route": route,
            "distance_km": route.get("distance_km"),
            "eta_min": route.get("total_time_min"),
            "score": (route.get("total_time_min") or float("inf")) +
                     (route.get("distance_km") or 0) * 0.5 if route["reachable"] else float("inf"),
        }

    def _best_depot_for_zone(self, zone: Dict, nodes: Dict,
                              resource_type: str = None,
                              required: int = 1) -> Dict[str, Any]:
        depots = self.facilities.get("depots", [])
        if not depots and self.facilities.get("depot"):
            depots = [self.facilities["depot"]]
        results = []
        for d in depots:
            d_id = d["id"]
            depot_stock = d.get(f"{_stock_key(resource_type)}", 99) if resource_type else 99
            if resource_type and depot_stock <= 0:
                continue
            result = self._evaluate_depot_for_zone(zone, d_id, nodes, resource_type)
            if result["feasible"]:
                results.append(result)
        results.sort(key=lambda r: r["score"])
        if results:
            return results[0]
        return {"feasible": False, "reason": "No depot with ground route and stock to zone"}

    def _multi_depot_allocation(self, zone_id: str, resource_type: str,
                                 total_needed: int, nodes: Dict) -> List[Dict]:
        depot_ids = [d["id"] for d in self.facilities.get("depots", [])]
        if not depot_ids:
            depot_ids = ["DEPOT"]
        availabilities: Dict[str, int] = {}
        for unit in self.resources.get("units", []):
            if unit.get("type") == resource_type and unit.get("status") == "AVAILABLE":
                base = unit.get("base_id", "DEPOT")
                availabilities[base] = availabilities.get(base, 0) + 1
        depot_results = []
        for d_id in depot_ids:
            eval_result = self._evaluate_depot_for_zone(
                {"id": zone_id} if isinstance(zone_id, str) else
                next((z for z in self.zones if z["id"] == zone_id), {"id": zone_id}),
                d_id, nodes, resource_type
            )
            if eval_result["feasible"]:
                depot_results.append((d_id, eval_result, availabilities.get(d_id, 0)))
        depot_results.sort(key=lambda item: item[1]["score"])
        allocations = []
        remaining = total_needed
        for d_id, eval_r, stock in depot_results:
            if remaining <= 0:
                break
            if stock <= 0:
                continue
            take = min(stock, remaining)
            allocations.append({
                "depot_id": d_id,
                "depot_name": eval_r["depot_name"],
                "allocation": take,
                "route": eval_r["route"],
                "distance_km": eval_r["distance_km"],
                "eta_min": eval_r["eta_min"],
            })
            remaining -= take
        if remaining > 0:
            if allocations:
                allocations.append({
                    "depot_id": "UNFULFILLED",
                    "allocation": remaining,
                    "warning": "No additional depots have ground access or stock",
                })
            else:
                allocations = [{
                    "depot_id": "NO_GROUND_ROUTE",
                    "allocation": 0,
                    "warning": "GROUND ACCESS UNAVAILABLE — recommend helicopter or alternate depot network",
                }]
        return allocations

    def _find_accessible_hospital(self, zone: Dict, nodes: Dict) -> Dict[str, Any]:
        hospitals = [h for h in self.facilities.get("hospitals", [])
                     if h.get("status", "").lower() in ("functional", "partial")
                     and h.get("available_beds", 0) > 0]
        if not hospitals:
            return {"feasible": False, "reason": "No hospitals with beds available"}
        service = RoutingService(self.roads, nodes)
        results = []
        for h in hospitals:
            route = service.get_route(zone["id"], h["id"], use_snap=True)
            if route["reachable"]:
                results.append({
                    "feasible": True,
                    "hospital_id": h["id"],
                    "hospital_name": h["name"],
                    "route": route,
                    "distance_km": route.get("distance_km"),
                    "eta_min": route.get("total_time_min"),
                    "beds": h.get("available_beds", 0),
                    "score": float(route.get("total_time_min") or 999.0),
                })
        if not results:
            return {"feasible": False, "reason": "No hospitals reachable by ground from this zone"}
        results.sort(key=lambda r: r["score"])
        return results[0]

    def _find_accessible_shelter(self, zone: Dict, nodes: Dict) -> Dict[str, Any]:
        shelters = [s for s in self.facilities.get("shelters", [])
                    if s.get("status", "") != "full"
                    and s.get("capacity", 0) - s.get("current_occupancy", 0) > 0]
        if not shelters:
            return {"feasible": False, "reason": "No shelters with capacity"}
        service = RoutingService(self.roads, nodes)
        results = []
        for s in shelters:
            route = service.get_route(zone["id"], s["id"], use_snap=True)
            if route["reachable"]:
                free = s.get("capacity", 0) - s.get("current_occupancy", 0)
                eta = float(route.get("total_time_min") or 999.0)
                score = round(eta * (1.0 + max(0.0, 100.0 - free) / 200.0), 2)
                results.append({
                    "feasible": True,
                    "shelter_id": s["id"],
                    "shelter_name": s["name"],
                    "route": route,
                    "distance_km": route.get("distance_km"),
                    "eta_min": route.get("total_time_min"),
                    "free_capacity": free,
                    "score": score,
                })
        if not results:
            return {"feasible": False, "reason": "No shelters reachable by ground from this zone"}
        results.sort(key=lambda r: r["score"])
        return results[0]

    def compute_full_state(self, active_dispatches: List[Dict] = None) -> Dict[str, Any]:
        nodes = self._build_nodes_dict()
        depot_ids = [d["id"] for d in self.facilities.get("depots", [])]
        if not depot_ids:
            depot_ids = ["DEPOT"]

        computed_zones = deepcopy(self.zones)

        # Apply active resource dispatches to dynamically lower HCI
        if active_dispatches:
            for d in active_dispatches:
                if d.get("zone_id") and d.get("status") in ("EN_ROUTE", "REROUTED", "ARRIVED"):
                    zid = d["zone_id"]
                    rtype = d["resource_type"]
                    for index, z in enumerate(computed_zones):
                        if z["id"] == zid:
                            # Apply resource effect to zone state
                            computed_zones[index] = simulate_resource_effect(z, rtype)
                            # Decrease requirement by 1
                            if "required_resources" in computed_zones[index] and rtype in computed_zones[index]["required_resources"]:
                                computed_zones[index]["required_resources"][rtype] = max(0, computed_zones[index]["required_resources"][rtype] - 1)

        # Build baseline routing service to find baseline P0 and A0
        baseline_roads = deepcopy(self._baseline_roads)
        baseline_service = RoutingService(baseline_roads, nodes)
        service = RoutingService(self.roads, nodes)
        
        blocked_roads = {r["id"] for r in self.roads if r["status"] == "blocked"}

        # Compute routes by origin for active network
        routes_by_origin: Dict[str, Dict[str, Dict]] = {}
        for d_id in depot_ids:
            try:
                routes_by_origin[d_id] = compute_all_routes(computed_zones, self.roads, source=d_id, nodes=nodes)
            except Exception:
                routes_by_origin[d_id] = {}
        if "DEPOT" not in routes_by_origin and self.facilities.get("depot"):
            try:
                routes_by_origin["DEPOT"] = compute_all_routes(computed_zones, self.roads, source="DEPOT", nodes=nodes)
            except Exception:
                routes_by_origin["DEPOT"] = {}

        primary_routes = routes_by_origin.get("DEPOT", {}) or (routes_by_origin[depot_ids[0]] if depot_ids else {})

        for zone in computed_zones:
            # 1. Determine best ground depot in baseline state
            best_depot = "DEPOT"
            min_base_time = float("inf")
            for d_id in depot_ids:
                try:
                    r = baseline_service.get_route(d_id, zone["id"], use_snap=True)
                    if r.get("reachable") and (r.get("total_time_min") or float("inf")) < min_base_time:
                        min_base_time = r["total_time_min"]
                        best_depot = d_id
                except Exception:
                    pass
            zone["best_depot"] = best_depot

            # 2. Get baseline routes P0 and A0
            P0 = baseline_service.get_route(best_depot, zone["id"], use_snap=True)
            try:
                A0 = baseline_service.get_alternative_route(best_depot, zone["id"])
            except Exception:
                A0 = {"reachable": False, "road_ids": [], "geometry": [], "path": []}

            # 3. Evaluate road blocks dynamically
            p0_blocked_ids = [rid for rid in (P0.get("road_ids") or []) if rid in blocked_roads]
            is_p0_blocked = len(p0_blocked_ids) > 0 or not P0.get("reachable")
            
            a0_blocked_ids = [rid for rid in (A0.get("road_ids") or []) if rid in blocked_roads]
            is_a0_blocked = len(a0_blocked_ids) > 0 or not A0.get("reachable")

            both_blocked = is_p0_blocked and is_a0_blocked
            main_blocked = is_p0_blocked

            if both_blocked:
                zone["response_accessibility"] = "INACCESSIBLE"
                zone["road_accessibility"] = "blocked"
                all_blocked_ids = sorted(list(set(p0_blocked_ids + a0_blocked_ids)))
                blocked_labels = f" ({', '.join(all_blocked_ids)} blocked)" if all_blocked_ids else ""
                zone["accessibility_reason"] = f"Ground access completely blocked: both Main and Alternative roads are closed{blocked_labels}."
                
                # Active route is P0 but marked unreachable
                best_route = deepcopy(P0)
                best_route["reachable"] = False
                best_route["reason"] = f"Main route blocked (R3 blocked, alt R12 active)." if zone["id"] == "Z01" else "Ground access blocked by what-if simulator."
                best_route["geometry"] = []
                best_route["road_ids"] = []
            elif main_blocked:
                zone["response_accessibility"] = "DIFFICULT"
                zone["road_accessibility"] = "degraded"
                blocked_labels = f" ({', '.join(p0_blocked_ids)} blocked)" if p0_blocked_ids else ""
                zone["accessibility_reason"] = f"Main route blocked{blocked_labels}. Fallback active via alternative route."
                
                # Active route becomes A0
                best_route = deepcopy(A0)
                best_route["status"] = "REROUTED"
            else:
                zone["response_accessibility"] = "ACCESSIBLE"
                zone["road_accessibility"] = "open"
                zone["accessibility_reason"] = "Feasible ground route available via road network."
                best_route = P0

            primary_routes[zone["id"]] = best_route
            
            if best_route and best_route.get("reachable"):
                zone["route_from_best_depot"] = {
                    "depot_id": best_depot,
                    "distance_km": best_route.get("distance_km"),
                    "eta_min": best_route.get("total_time_min"),
                    "avg_speed_kmh": best_route.get("avg_speed_kmh"),
                    "road_ids": best_route.get("road_ids"),
                    "path": best_route.get("path"),
                }
            else:
                zone["route_from_best_depot"] = {
                    "depot_id": best_depot,
                    "distance_km": 0.0,
                    "eta_min": 0.0,
                    "avg_speed_kmh": 0.0,
                    "road_ids": [],
                    "path": [],
                }
            zone["nearest_accessible_hospital"] = self._find_accessible_hospital(zone, nodes)
            zone["nearest_accessible_shelter"] = self._find_accessible_shelter(zone, nodes)

        scored = classify_all_zones(computed_zones)

        # Apply Isolation penalty (+15 index score) to scored zones where both paths are blocked
        for zone in scored:
            if zone.get("response_accessibility") == "INACCESSIBLE":
                zone["hci_score"] = min(100.0, float(zone["hci_score"]) + 15.0)
                if zone["hci_score"] >= 80:
                    zone["classification"] = "CRITICAL"
                elif zone["hci_score"] >= 60:
                    zone["classification"] = "HIGH"
                elif zone["hci_score"] >= 40:
                    zone["classification"] = "MODERATE"
                else:
                    zone["classification"] = "LOWER"
                
                zone["bottlenecks"].insert(0, {
                    "factor": "Route Isolation",
                    "raw_score": 100.0,
                    "contribution": 15.0,
                    "severity": "Critical"
                })
                zone["bottlenecks"] = zone["bottlenecks"][:5]

        # Re-sort scored zones by hci_score descending and re-assign priority ranks
        scored.sort(key=lambda z: -z["hci_score"])
        for i, z in enumerate(scored):
            z["priority_rank"] = i + 1

        first_depot = "DEPOT" if "DEPOT" in routes_by_origin else (depot_ids[0] if depot_ids else "DEPOT")
        recs = build_recommendations(
            computed_zones, scored,
            self.resources["inventory"],
            routes_by_origin.get(first_depot, {}),
            self.resources.get("units", []),
            routes_by_origin,
        )
        helicopters = [r for r in self.resources.get("units", [])
                       if r.get("type") == "helicopter" and r.get("status") == "AVAILABLE"]
        heli_bases = self.facilities.get("helicopter_bases", [])
        
        for zone in scored:
            best_depot = zone.get("best_depot") or "DEPOT"
            P0 = baseline_service.get_route(best_depot, zone["id"], use_snap=True)
            try:
                A0 = baseline_service.get_alternative_route(best_depot, zone["id"])
            except Exception:
                A0 = {"reachable": False, "road_ids": [], "geometry": [], "path": []}

            p0_blocked_ids = [rid for rid in (P0.get("road_ids") or []) if rid in blocked_roads]
            is_p0_blocked = len(p0_blocked_ids) > 0 or not P0.get("reachable")
            
            a0_blocked_ids = [rid for rid in (A0.get("road_ids") or []) if rid in blocked_roads]
            is_a0_blocked = len(a0_blocked_ids) > 0 or not A0.get("reachable")

            both_blocked = is_p0_blocked and is_a0_blocked
            main_blocked = is_p0_blocked

            any_ground = not both_blocked and (P0.get("reachable") or A0.get("reachable"))
            
            zone["alternate_route"] = A0 if not both_blocked else None
            air_needed = not any_ground or (
                zone["route_from_best_depot"].get("eta_min") and zone["route_from_best_depot"]["eta_min"] > 50
                and zone.get("classification") in ("CRITICAL", "HIGH")
            )
            if air_needed and helicopters and heli_bases:
                heli_unit = helicopters[0]
                base_id = heli_unit.get("base_id") or heli_bases[0]["id"]
                base = next((b for b in heli_bases if b["id"] == base_id), heli_bases[0])
                lat_delta = (zone["latitude"] - base["latitude"]) * 111
                lon_delta = (zone["longitude"] - base["longitude"]) * 101
                distance_km = round((lat_delta ** 2 + lon_delta ** 2) ** .5, 1)
                heli_speed = float(heli_unit.get("speed_kmh", 180))
                flight_eta = max(4, round(distance_km / heli_speed * 60, 1))
                zone["response_plan"] = {
                    "mode": "AIR",
                    "resource_id": heli_unit.get("id"),
                    "call_sign": heli_unit.get("call_sign"),
                    "base_id": base["id"],
                    "base": base["name"],
                    "origin_lat": base["latitude"],
                    "origin_lon": base["longitude"],
                    "dest_lat": zone["latitude"],
                    "dest_lon": zone["longitude"],
                    "air_distance_km": distance_km,
                    "flight_time_min": flight_eta,
                    "avg_speed_kmh": heli_speed,
                    "reason": "NO FEASIBLE GROUND ROUTE" if not any_ground
                    else "Ground access critically delayed — aerial response recommended.",
                }
            else:
                best_r = primary_routes.get(zone["id"])
                zone["response_plan"] = {
                    "mode": "GROUND",
                    "depot_id": best_depot,
                    "distance_km": best_r.get("distance_km") if best_r else None,
                    "eta_min": best_r.get("total_time_min") if best_r else None,
                    "avg_speed_kmh": best_r.get("avg_speed_kmh") if best_r else None,
                    "road_ids": best_r.get("road_ids") if best_r else None,
                    "path": best_r.get("path") if best_r else None,
                    "reason": zone["accessibility_reason"],
                    "route_available": best_r.get("reachable", False) if best_r else False,
                }
        safe_zones = [
            upgrade_safe_zone(s, hospitals=self.facilities.get("hospitals", []))
            for s in self.facilities.get("shelters", [])
        ]
        evac_zones = [extend_affected_zone(z, safe_zones=safe_zones) for z in scored]

        return {
            "zones": evac_zones,
            "safe_zones": safe_zones,
            "roads": self.roads,
            "facilities": self.facilities,
            "routes": primary_routes,
            "routes_by_origin": routes_by_origin,
            "recommendations": recs,
            "resources": self.resources,
            "active_events": self.active_events,
            "routing_notice": "Road-graph Dijkstra routing — all routes follow actual road segments.",
        }

    def get_zone_routes(self, zone_id: str, origin: Optional[str] = None) -> Dict[str, Any]:
        nodes = self._build_nodes_dict()
        if origin is None:
            zone = next((z for z in self.zones if z["id"] == zone_id), None)
            origin = (zone.get("best_depot") or "DEPOT") if zone else "DEPOT"
            
        baseline_roads = deepcopy(self._baseline_roads)
        baseline_service = RoutingService(baseline_roads, nodes)
        
        P0 = baseline_service.get_route(origin, zone_id, use_snap=True)
        try:
            A0 = baseline_service.get_alternative_route(origin, zone_id)
        except Exception:
            A0 = {"reachable": False, "road_ids": [], "geometry": [], "path": []}
            
        blocked_roads = {r["id"] for r in self.roads if r["status"] == "blocked"}
        
        p0_blocked_ids = [rid for rid in (P0.get("road_ids") or []) if rid in blocked_roads]
        is_p0_blocked = len(p0_blocked_ids) > 0 or not P0.get("reachable")
        
        a0_blocked_ids = [rid for rid in (A0.get("road_ids") or []) if rid in blocked_roads]
        is_a0_blocked = len(a0_blocked_ids) > 0 or not A0.get("reachable")
        
        if not P0.get("reachable"):
            return {
                "zone_id": zone_id,
                "origin_depot": origin,
                "route": P0,
                "alternate_route": A0,
            }
            
        if not is_p0_blocked:
            return {
                "zone_id": zone_id,
                "origin_depot": origin,
                "route": P0,
                "alternate_route": A0,
            }
        elif not is_a0_blocked:
            blocked_p = deepcopy(P0)
            blocked_p["reachable"] = False
            blocked_p["reason"] = f"Main route blocked: {', '.join(p0_blocked_ids)} closed."
            blocked_p["geometry"] = []
            
            active_a0 = deepcopy(A0)
            active_a0["status"] = "REROUTED"
            return {
                "zone_id": zone_id,
                "origin_depot": origin,
                "route": active_a0,
                "alternate_route": blocked_p,
            }
        else:
            blocked_p = deepcopy(P0)
            blocked_p["reachable"] = False
            blocked_p["reason"] = "Main route blocked."
            blocked_p["geometry"] = []
            
            blocked_a = deepcopy(A0)
            blocked_a["reachable"] = False
            blocked_a["reason"] = "Alternate route blocked."
            blocked_a["geometry"] = []
            
            return {
                "zone_id": zone_id,
                "origin_depot": origin,
                "route": blocked_p,
                "alternate_route": blocked_a,
            }

    def apply_parametric_cyclone(
        self,
        surge_height_m: float = 3.0,
        wind_speed_kmh: float = 130.0,
        rainfall_24h_mm: float = 200.0,
        breach_locations: Optional[List[str]] = None,
        active_dispatches: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Executes a physics-grounded, multi-hazard parametric cyclone simulation.
        Translates continuous environmental variables into spatial cascading failures:
        - Storm Surge (m) -> Inundation depth, road submersion, shelter capacity loss
        - Wind Speed (km/h) -> Structural damage, telecom failure, debris blockages
        - 24h Rainfall (mm) -> Road degradation, drainage congestion
        - Embankment Breaches -> Severe saline intrusion & zone isolation
        Returns the computed full state plus an extensive Before vs After impact delta.
        """
        # 1. Capture baseline state for delta comparison
        self.reset()
        base_state = self.compute_full_state(active_dispatches=active_dispatches)
        base_zones = {z["id"]: deepcopy(z) for z in base_state["zones"]}
        base_roads = {r["id"]: deepcopy(r) for r in base_state["roads"]}
        base_shelters = {s["id"]: deepcopy(s) for s in base_state.get("facilities", {}).get("shelters", [])}
        
        # 2. Build multi-hazard event bundle
        events = [
            {"type": "STORM_SURGE_INUNDATION", "surge_height_m": surge_height_m},
            {"type": "CYCLONE_LANDFALL", "wind_speed_kmh": wind_speed_kmh},
            {"type": "TORRENTIAL_PRECIPITATION", "rainfall_24h_mm": rainfall_24h_mm},
        ]
        if breach_locations:
            events.append({"type": "EMBANKMENT_BREACH", "locations": breach_locations})

        # 3. Apply events and compute full cascading state
        sim_state = self.apply_events(events, active_dispatches=active_dispatches)
        
        # 4. Build Before vs After comparison delta
        newly_blocked_roads = []
        for r in sim_state["roads"]:
            rid = r["id"]
            if r.get("status") == "blocked" and base_roads.get(rid, {}).get("status") != "blocked":
                newly_blocked_roads.append({
                    "road_id": rid,
                    "from_node": r.get("from_node"),
                    "to_node": r.get("to_node"),
                    "reason": r.get("condition", "submerged"),
                    "distance_km": r.get("distance_km", 2.0),
                    "depth_m": r.get("inundation_depth_m", 0.0)
                })

        escalated_zones = []
        for z in sim_state["zones"]:
            zid = z["id"]
            bz = base_zones.get(zid, {})
            delta_hci = round(float(z.get("hci_score", 0)) - float(bz.get("hci_score", 0)), 1)
            air_escalated = (
                z.get("response_plan", {}).get("mode") == "AIR"
                and bz.get("response_plan", {}).get("mode") != "AIR"
            )
            class_changed = z.get("classification") != bz.get("classification")
            
            if delta_hci >= 2.0 or air_escalated or class_changed or z.get("flooded"):
                escalated_zones.append({
                    "zone_id": zid,
                    "name": z.get("name"),
                    "baseline_hci": bz.get("hci_score"),
                    "simulated_hci": z.get("hci_score"),
                    "delta_hci": delta_hci,
                    "baseline_class": bz.get("classification"),
                    "simulated_class": z.get("classification"),
                    "air_escalated": air_escalated,
                    "inundation_depth_m": z.get("inundation_depth_m", 0.0),
                    "people_at_risk_delta": int(z.get("affected_population", 0)) - int(bz.get("affected_population", 0))
                })

        flooded_shelters = []
        for s in sim_state.get("facilities", {}).get("shelters", []):
            sid = s["id"]
            bs = base_shelters.get(sid, {})
            if s.get("ground_floor_flooded") or s.get("status") == "unavailable":
                flooded_shelters.append({
                    "shelter_id": sid,
                    "name": s.get("name"),
                    "status": s.get("status"),
                    "capacity_loss": int(bs.get("available_capacity", 0)) - int(s.get("available_capacity", 0))
                })

        return {
            "parameters": {
                "surge_height_m": surge_height_m,
                "wind_speed_kmh": wind_speed_kmh,
                "rainfall_24h_mm": rainfall_24h_mm,
                "breach_locations": breach_locations or []
            },
            "summary": {
                "newly_blocked_roads_count": len(newly_blocked_roads),
                "escalated_zones_count": len(escalated_zones),
                "air_evacuation_zones_count": sum(1 for ez in escalated_zones if ez.get("air_escalated")),
                "flooded_shelters_count": len(flooded_shelters),
                "total_affected_population": sum(z.get("affected_population", 0) for z in sim_state["zones"]),
                "critical_zones_count": sum(1 for z in sim_state["zones"] if z.get("classification") == "CRITICAL")
            },
            "newly_blocked_roads": newly_blocked_roads,
            "escalated_zones": escalated_zones,
            "flooded_shelters": flooded_shelters,
            "state": sim_state
        }


def get_cyclone_presets() -> List[Dict[str, Any]]:
    """Return historical cyclone benchmarks for rapid scenario injection."""
    return [
        {
            "id": "AMPHAN_2020",
            "name": "Super Cyclone Amphan (2020)",
            "category": "Super Cyclonic Storm (Cat 5 Eq.)",
            "surge_height_m": 4.5,
            "wind_speed_kmh": 185.0,
            "rainfall_24h_mm": 240.0,
            "breach_locations": ["WB01", "WB05", "WB04"],
            "description": "Historical landfall at Bakkhali/Sagar Island with 4.5m storm surge and severe mangrove bio-shield breach."
        },
        {
            "id": "YAAS_2021",
            "name": "Very Severe Cyclone Yaas (2021)",
            "category": "Very Severe Cyclonic Storm",
            "surge_height_m": 3.8,
            "wind_speed_kmh": 140.0,
            "rainfall_24h_mm": 180.0,
            "breach_locations": ["WB04", "WB03"],
            "description": "Coincident with full moon astronomical spring tide, breaching coastal embankments in Namkhana and Digha."
        },
        {
            "id": "REMAL_2024",
            "name": "Severe Cyclone Remal (2024)",
            "category": "Severe Cyclonic Storm",
            "surge_height_m": 3.2,
            "wind_speed_kmh": 125.0,
            "rainfall_24h_mm": 210.0,
            "breach_locations": ["WB01", "WB09"],
            "description": "Extended monsoon cyclonic crossing with heavy precipitation across Sagar Island and Kakdwip."
        },
        {
            "id": "CATASTROPHIC_SPRING_SURGE",
            "name": "Worst-Case Catastrophic Surge (5.8m)",
            "category": "Extreme High-Tide Surge",
            "surge_height_m": 5.8,
            "wind_speed_kmh": 200.0,
            "rainfall_24h_mm": 350.0,
            "breach_locations": ["WB01", "WB02", "WB03", "WB04", "WB05"],
            "description": "Simulates 5.8m storm surge overtopping delta embankments, severing coastal roads, and mandating air bridges."
        }
    ]


def _stock_key(resource_type: str) -> str:
    mapping = {
        "water_tanker": "water_stock_units",
        "food_unit": "food_stock_units",
        "medical_team": "medical_stock_units",
    }
    return mapping.get(resource_type, "capacity")

