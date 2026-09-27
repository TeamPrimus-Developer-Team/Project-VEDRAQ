"""
VEDRAQ Road Routing Service — Road Graph Dijkstra with Geometry-Aware Routing
===============================================================================
Key features:
- Builds a bidirectional weighted graph from the road segment network.
- Uses REAL geometry waypoints from roads.json for route visualization (not fake curves).
- Dijkstra shortest-path by travel-time cost (degraded roads add penalty).
- Location snapping: any lat/lon snaps to the nearest road segment before routing.
- Primary + Alternate route: removes each edge of primary path one-by-one and re-runs Dijkstra, keeping the shortest available alternative.
- ETA calculation: distance_km / effective_speed_kmh, with degradation penalties.
- Helicopter routing: straight haversine aerial distance, no roads needed.
- Never falls back to a straight ground line — if no ground route, returns unreachable.
"""
import heapq
import math
from typing import Any, Dict, List, Optional, Tuple


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def point_to_segment_distance(px: float, py: float,
                              ax: float, ay: float, bx: float, by: float) -> Tuple[float, float, float]:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        d = math.hypot(px - ax, py - ay)
        return d, 0.0, 0.0
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    d = math.hypot(px - cx, py - cy)
    return d, t, math.hypot(cx - ax, cy - ay) / max(math.hypot(dx, dy), 1e-9)


def route_geometry_distance_km(geometry: List[List[float]]) -> float:
    total = 0.0
    for i in range(1, len(geometry)):
        a, b = geometry[i - 1], geometry[i]
        total += haversine(a[0], a[1], b[0], b[1])
    return total


class RoutingService:
    def __init__(self, roads: List[Dict], nodes: Optional[Dict[str, Dict]] = None):
        self.roads = roads
        self.nodes = nodes or {}
        self._road_by_id = {r["id"]: r for r in roads}

    # ── GRAPH CONSTRUCTION ────────────────────────────────────────────────
    def _build_graph(self, excluded_road_ids=None, excluded_nodes=None) -> Dict[str, List[Tuple[str, float, Dict]]]:
        graph: Dict[str, List[Tuple[str, float, Dict]]] = {}
        excluded = set(excluded_road_ids or [])
        ex_nodes = set(excluded_nodes or [])
        for road in self.roads:
            if road["id"] in excluded:
                continue
            if road["status"].lower() == "blocked":
                continue
            base_time = float(road.get("travel_time_min", 0))
            degraded = road["status"].lower() == "degraded"
            edge_cost = base_time * (1.8 if degraded else 1.0) * max(float(road.get("distance_km", 0.01)) / max(0.01, float(road.get("distance_km", 1))), 1.0)
            if edge_cost <= 0:
                dist = float(road.get("distance_km", 0))
                speed = float(road.get("speed_kmh", 20))
                edge_cost = dist / speed * 60 if speed > 0 and dist > 0 else float(road.get("travel_time_min", 10))
                edge_cost = edge_cost * (1.8 if degraded else 1.0)
            a, b = road["from_node"], road["to_node"]
            if a in ex_nodes or b in ex_nodes:
                continue
            graph.setdefault(a, []).append((b, edge_cost, road))
            graph.setdefault(b, []).append((a, edge_cost, road))
        return graph

    # ── DIJKSTRA ───────────────────────────────────────────────────────────
    def _dijkstra(self, graph, origin: str, destination: str
                  ) -> Tuple[Optional[float], Dict[str, Tuple[str, Dict]]]:
        if origin == destination:
            return 0.0, {}
        dist: Dict[str, float] = {origin: 0.0}
        prev: Dict[str, Tuple[str, Dict]] = {}
        heap = [(0.0, origin)]
        while heap:
            cost, node = heapq.heappop(heap)
            if node == destination:
                break
            if cost != dist.get(node, float("inf")):
                continue
            for nxt, edge_cost, road in graph.get(node, []):
                total = cost + edge_cost
                if total < dist.get(nxt, float("inf")):
                    dist[nxt] = total
                    prev[nxt] = (node, road)
                    heapq.heappush(heap, (total, nxt))
        if destination not in dist:
            return None, prev
        return dist[destination], prev

    def _reconstruct_path(self, prev: Dict, origin: str, destination: str
                          ) -> Tuple[List[str], List[Dict], List[str]]:
        if origin == destination:
            return [origin], [], []
        nodes: List[str] = [destination]
        segments: List[Dict] = []
        ids: List[str] = []
        cursor = destination
        safety = 0
        while cursor != origin and cursor in prev and safety < 1000:
            parent, road = prev[cursor]
            nodes.append(parent)
            segments.append(road)
            ids.append(road["id"])
            cursor = parent
            safety += 1
        nodes.reverse()
        segments.reverse()
        ids.reverse()
        return nodes, segments, ids

    # ── SNAP LAT/LON TO NEAREST ROAD → return graph node + snapped geometry point
    def snap_location(self, lat: float, lon: float, allow_blocked: bool = False) -> Dict[str, Any]:
        best = {"distance_km": float("inf")}
        for road in self.roads:
            if road["status"].lower() == "blocked" and not allow_blocked:
                continue
            geom = road.get("geometry", [])
            if len(geom) < 2:
                continue
            for i in range(1, len(geom)):
                a, b = geom[i - 1], geom[i]
                d_lat, d_lon, frac = point_to_segment_distance(lat, lon, a[0], a[1], b[0], b[1])
                d_km = d_lat * 111.0
                if d_km < best["distance_km"]:
                    snap_lat = a[0] + frac * (b[0] - a[0])
                    snap_lon = a[1] + frac * (b[1] - a[1])
                    from_node = road["from_node"]
                    to_node = road["to_node"]
                    d_from = haversine(snap_lat, snap_lon,
                                       self.nodes.get(from_node, {}).get("latitude", a[0]),
                                       self.nodes.get(from_node, {}).get("longitude", a[1]))
                    d_to = haversine(snap_lat, snap_lon,
                                     self.nodes.get(to_node, {}).get("latitude", b[0]),
                                     self.nodes.get(to_node, {}).get("longitude", b[1]))
                    nearer_node = from_node if d_from <= d_to else to_node
                    best = {
                        "distance_km": d_km,
                        "snap_lat": snap_lat,
                        "snap_lon": snap_lon,
                        "road_id": road["id"],
                        "nearest_node": nearer_node,
                        "from_node": from_node,
                        "to_node": to_node,
                        "segment_a": a,
                        "segment_b": b,
                        "fraction": frac,
                    }
        if best.get("nearest_node") is None:
            fallback_node = None
            fallback_dist = float("inf")
            for nid, ndata in self.nodes.items():
                d = haversine(lat, lon,
                              ndata.get("latitude", 0),
                              ndata.get("longitude", 0))
                if d < fallback_dist:
                    fallback_dist = d
                    fallback_node = nid
            best = {
                "distance_km": fallback_dist,
                "snap_lat": lat,
                "snap_lon": lon,
                "road_id": None,
                "nearest_node": fallback_node,
                "from_node": None,
                "to_node": None,
                "segment_a": [lat, lon],
                "segment_b": [lat, lon],
                "fraction": 0.0,
            }
        return best    # ── BUILD VISUAL GEOMETRY from real road waypoints ────────────────────
    def _assemble_geometry(self, segments: List[Dict],
                           path_nodes: List[str],
                           snap_from: Optional[Dict] = None,
                           snap_to: Optional[Dict] = None) -> List[List[float]]:
        if not segments:
            if snap_from and snap_to:
                return [[snap_from["snap_lat"], snap_from["snap_lon"]],
                        [snap_to["snap_lat"], snap_to["snap_lon"]]]
            return []

        geometry: List[List[float]] = []

        for i, road in enumerate(segments):
            # 1. Fetch original road geometry
            road_geom = list(road.get("geometry", []))
            if not road_geom and road["from_node"] in self.nodes and road["to_node"] in self.nodes:
                n1, n2 = self.nodes[road["from_node"]], self.nodes[road["to_node"]]
                road_geom = [[n1["latitude"], n1["longitude"]], [n2["latitude"], n2["longitude"]]]
            
            if not road_geom:
                continue

            # 2. Determine traversal direction based on path_nodes order
            is_reverse = False
            for idx in range(len(path_nodes) - 1):
                u, v = path_nodes[idx], path_nodes[idx+1]
                if u == road["from_node"] and v == road["to_node"]:
                    is_reverse = False
                    break
                elif u == road["to_node"] and v == road["from_node"]:
                    is_reverse = True
                    break

            # Orient geometry in the direction of traversal
            if is_reverse:
                road_geom.reverse()

            # 3. Handle snaps
            if len(segments) == 1 and snap_from and snap_to and snap_from.get("road_id") == road["id"] and snap_to.get("road_id") == road["id"]:
                start_pt = [snap_from["snap_lat"], snap_from["snap_lon"]]
                end_pt = [snap_to["snap_lat"], snap_to["snap_lon"]]
                
                min_start = float("inf")
                k_start = 0
                for k in range(len(road_geom) - 1):
                    d, _, _ = point_to_segment_distance(start_pt[0], start_pt[1], road_geom[k][0], road_geom[k][1], road_geom[k+1][0], road_geom[k+1][1])
                    if d < min_start:
                        min_start = d
                        k_start = k
                
                min_end = float("inf")
                k_end = 0
                for k in range(len(road_geom) - 1):
                    d, _, _ = point_to_segment_distance(end_pt[0], end_pt[1], road_geom[k][0], road_geom[k][1], road_geom[k+1][0], road_geom[k+1][1])
                    if d < min_end:
                        min_end = d
                        k_end = k
                
                if k_start < k_end:
                    geom_copy = [start_pt] + road_geom[k_start+1:k_end+1] + [end_pt]
                elif k_start > k_end:
                    geom_copy = [start_pt] + road_geom[k_start:k_end:-1] + [end_pt]
                else:
                    geom_copy = [start_pt, end_pt]
                
                geometry.extend(geom_copy)

            elif i == 0 and snap_from and snap_from.get("road_id") == road["id"]:
                start_pt = [snap_from["snap_lat"], snap_from["snap_lon"]]
                min_start = float("inf")
                k_start = 0
                for k in range(len(road_geom) - 1):
                    d, _, _ = point_to_segment_distance(start_pt[0], start_pt[1], road_geom[k][0], road_geom[k][1], road_geom[k+1][0], road_geom[k+1][1])
                    if d < min_start:
                        min_start = d
                        k_start = k
                geom_copy = [start_pt] + road_geom[k_start+1:]
                geometry.extend(geom_copy)

            elif i == len(segments) - 1 and snap_to and snap_to.get("road_id") == road["id"]:
                end_pt = [snap_to["snap_lat"], snap_to["snap_lon"]]
                min_end = float("inf")
                k_end = 0
                for k in range(len(road_geom) - 1):
                    d, _, _ = point_to_segment_distance(end_pt[0], end_pt[1], road_geom[k][0], road_geom[k][1], road_geom[k+1][0], road_geom[k+1][1])
                    if d < min_end:
                        min_end = d
                        k_end = k
                geom_copy = road_geom[:k_end+1] + [end_pt]
                if geometry:
                    geometry.extend(geom_copy[1:])
                else:
                    geometry.extend(geom_copy)

            else:
                if geometry:
                    geometry.extend(road_geom[1:])
                else:
                    geometry.extend(road_geom)

        return geometry

    # ── CALCULATE REAL DISTANCE from geometry, not just node labels ───────
    def _real_route_metrics(self, segments: List[Dict], geometry: List[List[float]],
                            resource_speed_kmh: Optional[float] = None
                            ) -> Tuple[float, float, float]:
        geo_dist = route_geometry_distance_km(geometry)
        road_sum = sum(float(r.get("distance_km", 0)) for r in segments)
        distance_km = geo_dist if geo_dist > 0 else road_sum
        if resource_speed_kmh and resource_speed_kmh > 0:
            eta_min = distance_km / resource_speed_kmh * 60
            degraded_count = sum(1 for r in segments if r.get("status", "").lower() == "degraded")
            if degraded_count > 0:
                eta_min = eta_min * (1.0 + 0.25 * degraded_count / max(1, len(segments)))
        else:
            eta_min = sum(float(r.get("travel_time_min", 0)) for r in segments)
            if eta_min <= 0:
                eta_min = distance_km / 25 * 60
        avg_speed = distance_km / (eta_min / 60) if eta_min > 0 else 25.0
        return round(distance_km, 1), round(eta_min, 1), round(avg_speed, 1)

    # ── ROUTE GEOMETRY VALIDATION ──────────────────────────────────────────
    def validate_route_geometry(self, route: Dict[str, Any]) -> Dict[str, Any]:
        if not route.get("reachable"):
            return {"valid": True, "reason": "Unreachable route needs no validation."}
        geom = route.get("geometry", [])
        if not geom:
            return {"valid": False, "reason": "Reachable route has empty geometry."}
        if len(geom) < 2:
            return {"valid": False, "reason": "Geometry has less than 2 points."}
        
        # 1. Proximity checks for origin and destination
        o_node = route.get("origin_node")
        d_node = route.get("destination_node")
        
        if o_node in self.nodes:
            origin_coords = [self.nodes[o_node]["latitude"], self.nodes[o_node]["longitude"]]
            if route.get("origin_snap"):
                origin_coords = [route["origin_snap"]["snap_lat"], route["origin_snap"]["snap_lon"]]
            start_dist = haversine(geom[0][0], geom[0][1], origin_coords[0], origin_coords[1])
            if start_dist > 1.5:
                return {"valid": False, "reason": f"Start point of geometry is too far from origin node/snap: {start_dist:.2f} km"}
        
        if d_node in self.nodes:
            dest_coords = [self.nodes[d_node]["latitude"], self.nodes[d_node]["longitude"]]
            if route.get("destination_snap"):
                dest_coords = [route["destination_snap"]["snap_lat"], route["destination_snap"]["snap_lon"]]
            end_dist = haversine(geom[-1][0], geom[-1][1], dest_coords[0], dest_coords[1])
            if end_dist > 1.5:
                return {"valid": False, "reason": f"End point of geometry is too far from destination node/snap: {end_dist:.2f} km"}

        # 2. Maximum segment jump validation (e.g. max 5.0 km jump between adjacent path coordinates)
        max_jump_km = 5.0
        for i in range(1, len(geom)):
            step_d = haversine(geom[i-1][0], geom[i-1][1], geom[i][0], geom[i][1])
            if step_d > max_jump_km:
                return {"valid": False, "reason": f"Impossible jump of {step_d:.2f} km detected at index {i}."}

        return {"valid": True, "reason": "Route geometry meets all validation rules."}

    # ── PRIMARY ROUTE ─────────────────────────────────────────────────────
    def get_route(self, origin: str, destination: str,
                  resource_speed_kmh: Optional[float] = None,
                  excluded_road_ids: Optional[List[str]] = None,
                  use_snap: bool = True) -> Dict[str, Any]:
        orig_snap, dest_snap = None, None
        o_node, d_node = origin, destination
        graph = self._build_graph(excluded_road_ids=excluded_road_ids)

        if use_snap:
            if o_node not in graph:
                if origin in self.nodes and "latitude" in self.nodes[origin] and "longitude" in self.nodes[origin]:
                    orig_snap = self.snap_location(float(self.nodes[origin]["latitude"]), float(self.nodes[origin]["longitude"]))
                    o_node = orig_snap["nearest_node"]
                elif "," in str(origin):
                    try:
                        lat, lon = map(float, str(origin).split(","))
                        orig_snap = self.snap_location(lat, lon)
                        o_node = orig_snap["nearest_node"]
                    except Exception:
                        pass
            if d_node not in graph:
                if destination in self.nodes and "latitude" in self.nodes[destination] and "longitude" in self.nodes[destination]:
                    dest_snap = self.snap_location(float(self.nodes[destination]["latitude"]), float(self.nodes[destination]["longitude"]))
                    d_node = dest_snap["nearest_node"]
                elif "," in str(destination):
                    try:
                        lat, lon = map(float, str(destination).split(","))
                        dest_snap = self.snap_location(lat, lon)
                        d_node = dest_snap["nearest_node"]
                    except Exception:
                        pass
        if o_node is None or d_node is None:
            return {"reachable": False, "path": [], "road_ids": [],
                    "distance_km": None, "total_time_min": None,
                    "avg_speed_kmh": None, "geometry": [],
                    "engine": "road-graph",
                    "reason": "No road graph nodes available near origin or destination."}
        cost, prev = self._dijkstra(graph, o_node, d_node)
        if cost is None:
            return {"reachable": False, "path": [], "road_ids": [],
                    "distance_km": None, "total_time_min": None,
                    "avg_speed_kmh": None, "geometry": [],
                    "engine": "road-graph",
                    "reason": f"No feasible ground route: all connecting road segments from {o_node} to {d_node} are blocked or no alternate roads exist."}
        nodes, segments, ids = self._reconstruct_path(prev, o_node, d_node)
        if origin not in nodes and orig_snap:
            if nodes[0] != orig_snap["nearest_node"]:
                nodes = [orig_snap["nearest_node"]] + nodes
        if destination not in nodes and dest_snap:
            if nodes[-1] != dest_snap["nearest_node"]:
                nodes = nodes + [dest_snap["nearest_node"]]
        geometry = self._assemble_geometry(segments, nodes, orig_snap, dest_snap)
        dist_km, eta_min, avg_speed = self._real_route_metrics(segments, geometry, resource_speed_kmh)
        route_out = {
            "reachable": True,
            "path": nodes,
            "road_ids": ids,
            "road_segments": [{
                "id": r["id"], "from_node": r["from_node"], "to_node": r["to_node"],
                "status": r["status"], "distance_km": r["distance_km"],
                "travel_time_min": r.get("travel_time_min", 0),
            } for r in segments],
            "distance_km": dist_km,
            "total_time_min": eta_min,
            "avg_speed_kmh": avg_speed,
            "geometry": geometry,
            "engine": "road-graph",
            "status": "OPEN",
            "degraded_segments": [r["id"] for r in segments if r.get("status", "").lower() == "degraded"],
            "blocked_check": "PASS",
            "notice": "Road graph routing — follows actual road segments from VEDRAQ network.",
            "origin_snap": orig_snap,
            "destination_snap": dest_snap,
            "origin_node": o_node,
            "destination_node": d_node,
        }
        route_out["geometry_validation"] = self.validate_route_geometry(route_out)
        return route_out

    # ── ALTERNATE ROUTE ───────────────────────────────────────────────────
    def get_alternative_route(self, origin: str, destination: str,
                              resource_speed_kmh: Optional[float] = None,
                              excluded_road_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        primary = self.get_route(origin, destination, resource_speed_kmh, excluded_road_ids)
        if not primary["reachable"]:
            return {"reachable": False, "is_alternative": True, "primary_blocked": True,
                    "reason": "Primary route unreachable — no alternate ground route exists either.",
                    "path": [], "road_ids": [], "geometry": [],
                    "distance_km": None, "total_time_min": None, "avg_speed_kmh": None,
                    "engine": "road-graph", "status": "NO_ALTERNATE"}
        primary_ids = set(primary["road_ids"])
        candidates: List[Dict[str, Any]] = []
        base_exclude = set(excluded_road_ids or [])
        for rid in primary_ids:
            trial_exclude = list(base_exclude | {rid})
            alt = self.get_route(origin, destination, resource_speed_kmh, trial_exclude, use_snap=True)
            if alt["reachable"] and set(alt["road_ids"]) != primary_ids:
                candidates.append(alt)
        if not candidates and len(primary_ids) >= 2:
            for combo_size in range(2, min(4, len(primary_ids) + 1)):
                import itertools
                for combo in itertools.combinations(list(primary_ids), combo_size):
                    trial_exclude = list(base_exclude | set(combo))
                    alt = self.get_route(origin, destination, resource_speed_kmh, trial_exclude, use_snap=True)
                    if alt["reachable"] and set(alt["road_ids"]) != primary_ids:
                        candidates.append(alt)
                        if len(candidates) >= 2:
                            break
                if candidates:
                    break
        if not candidates:
            all_ids = {r["id"] for r in self.roads if r["status"].lower() != "blocked"}
            alt_excl = list(base_exclude | primary_ids)
            fallback = self.get_route(origin, destination, resource_speed_kmh, alt_excl, use_snap=True)
            if fallback["reachable"]:
                candidates.append(fallback)
        if not candidates:
            return {"reachable": False, "is_alternative": True,
                    "primary_route": {"road_ids": list(primary_ids)},
                    "reason": "No alternate ground route available — all viable connecting road segments are in use or blocked.",
                    "path": [], "road_ids": [], "geometry": [],
                    "distance_km": None, "total_time_min": None, "avg_speed_kmh": None,
                    "engine": "road-graph", "status": "NO_ALTERNATE"}
        best = min(candidates, key=lambda c: c["total_time_min"] if c.get("total_time_min") else float("inf"))
        best["is_alternative"] = True
        best["primary_distance_km"] = primary["distance_km"]
        best["primary_time_min"] = primary["total_time_min"]
        best["delta_distance_km"] = round((best["distance_km"] or 0) - (primary["distance_km"] or 0), 1)
        best["delta_time_min"] = round((best["total_time_min"] or 0) - (primary["total_time_min"] or 0), 1)
        best["status"] = "ALTERNATE_ACTIVE"
        return best

    # ── 3-PATH FALLBACK ROUTING (PATH 1 -> PATH 2 -> PATH 3) ───────────────
    def get_three_routes(self, origin: str, destination: str,
                         resource_speed_kmh: Optional[float] = None,
                         excluded_road_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculates up to three distinct valid ground paths through Dijkstra:
        - Path 1 (PRIMARY): Shortest valid available route.
        - Path 2 (ALTERNATE): Alternative route excluding Path 1 road segments.
        - Path 3 (FALLBACK): Third fallback route excluding Path 1 & Path 2 road segments.
        If all paths are blocked/unreachable, returns reachable: False.
        """
        base_excl = set(excluded_road_ids or [])
        
        # Path 1: Primary (shortest valid route)
        path1 = self.get_route(origin, destination, resource_speed_kmh, list(base_excl), use_snap=True)
        if not path1.get("reachable"):
            return {
                "reachable": False,
                "active_path_type": None,
                "active_route": None,
                "primary": None, "alternate": None, "fallback": None,
                "reason": "ALL GROUND ROUTES BLOCKED — AERIAL RESPONSE REQUIRED"
            }
        
        path1["path_type"] = "PRIMARY"
        
        # Path 2: Alternate (exclude path1 road_ids)
        p1_roads = set(path1.get("road_ids", []))
        excl_p2 = list(base_excl | p1_roads)
        path2 = self.get_route(origin, destination, resource_speed_kmh, excl_p2, use_snap=True)
        
        if path2.get("reachable"):
            path2["path_type"] = "ALTERNATE"
            # Path 3: Fallback (exclude path1 + path2 road_ids)
            p2_roads = set(path2.get("road_ids", []))
            excl_p3 = list(base_excl | p1_roads | p2_roads)
            path3 = self.get_route(origin, destination, resource_speed_kmh, excl_p3, use_snap=True)
            if path3.get("reachable"):
                path3["path_type"] = "FALLBACK"
            else:
                path3 = None
        else:
            path2 = None
            path3 = None

        return {
            "reachable": True,
            "active_path_type": "PRIMARY",
            "active_route": path1,
            "primary": path1,
            "alternate": path2,
            "fallback": path3,
        }

    # ── HELICOPTER (AERIAL) ROUTE ─────────────────────────────────────────
    def get_helicopter_route(self, origin_lat: float, origin_lon: float,
                             dest_lat: float, dest_lon: float,
                             helicopter_speed_kmh: float = 180.0) -> Dict[str, Any]:
        dist_km = round(haversine(origin_lat, origin_lon, dest_lat, dest_lon), 1)
        eta_min = round(dist_km / max(helicopter_speed_kmh, 1) * 60, 1)
        mid_lat = (origin_lat + dest_lat) / 2 + 0.01
        mid_lon = (origin_lon + dest_lon) / 2 + 0.012
        mid_lat2 = (origin_lat + dest_lat) / 2 - 0.008
        mid_lon2 = (origin_lon + dest_lon) / 2 - 0.006
        geometry = [[origin_lat, origin_lon],
                    [mid_lat2, mid_lon2],
                    [(origin_lat + dest_lat) / 2, (origin_lon + dest_lon) / 2],
                    [mid_lat, mid_lon],
                    [dest_lat, dest_lon]]
        return {
            "reachable": True,
            "mode": "AIR",
            "air_distance_km": dist_km,
            "flight_time_min": eta_min,
            "avg_speed_kmh": round(helicopter_speed_kmh, 1),
            "geometry": geometry,
            "engine": "aerial-haversine",
            "status": "AERIAL_AVAILABLE",
            "reason": "Direct aerial path — helicopter does not require road network.",
        }

    def is_route_available(self, origin: str, destination: str) -> bool:
        return self.get_route(origin, destination, use_snap=True)["reachable"]

    def get_distance(self, origin: str, destination: str):
        return self.get_route(origin, destination, use_snap=True).get("distance_km")

    def get_eta(self, origin: str, destination: str):
        return self.get_route(origin, destination, use_snap=True).get("total_time_min")

    # ── SAFETY-FIRST EVACUATION ROUTING (PHASE 3) ─────────────────────────
    def _build_safety_graph(self, vehicle_type: str = "bus",
                            excluded_road_ids: Optional[List[str]] = None,
                            excluded_nodes: Optional[List[str]] = None) -> Dict[str, List[Tuple[str, float, Dict]]]:
        """
        Build a safety-weighted graph where edge cost prioritizes safety:
        - Base travel time
        - Degradation penalty tailored to vehicle suitability
        - Hazard/flood condition penalty
        - Blocked roads completely excluded
        """
        graph: Dict[str, List[Tuple[str, float, Dict]]] = {}
        excluded = set(excluded_road_ids or [])
        ex_nodes = set(excluded_nodes or [])

        # Heavy transport (buses) suffer higher penalties on degraded/damaged corridors
        v_degrade_mult = 2.5 if vehicle_type == "bus" else (2.0 if vehicle_type == "rescue_van" else 1.8)

        for road in self.roads:
            if road["id"] in excluded:
                continue
            status = str(road.get("status", "open")).lower()
            if status == "blocked":
                continue

            base_time = float(road.get("travel_time_min", 0))
            dist_km = float(road.get("distance_km", 0.01))
            speed = float(road.get("speed_kmh", 25.0))
            if base_time <= 0 and speed > 0:
                base_time = (dist_km / speed) * 60.0

            # Safety weighting calculation
            is_degraded = (status == "degraded")
            safety_mult = v_degrade_mult if is_degraded else 1.0

            # Check road condition or hazard level if present
            condition = str(road.get("condition", "normal")).lower()
            if condition in ("flooded", "waterlogged"):
                safety_mult *= 2.2
            elif condition in ("debris", "cracked", "damaged"):
                safety_mult *= 1.5

            edge_cost = base_time * safety_mult

            a, b = road["from_node"], road["to_node"]
            if a in ex_nodes or b in ex_nodes:
                continue
            graph.setdefault(a, []).append((b, edge_cost, road))
            graph.setdefault(b, []).append((a, edge_cost, road))
        return graph

    def get_safest_evacuation_route(self, origin: str, destination: str,
                                    vehicle_type: str = "bus",
                                    resource_speed_kmh: Optional[float] = None,
                                    excluded_road_ids: Optional[List[str]] = None,
                                    use_snap: bool = True) -> Dict[str, Any]:
        """
        Calculates the safest practical evacuation route between an affected zone
        and a safe zone, prioritizing lowest risk and vehicle suitability.
        """
        orig_snap, dest_snap = None, None
        o_node, d_node = origin, destination
        safety_graph = self._build_safety_graph(vehicle_type=vehicle_type, excluded_road_ids=excluded_road_ids)

        if use_snap:
            if o_node not in safety_graph:
                if origin in self.nodes and "latitude" in self.nodes[origin] and "longitude" in self.nodes[origin]:
                    orig_snap = self.snap_location(float(self.nodes[origin]["latitude"]), float(self.nodes[origin]["longitude"]))
                    o_node = orig_snap["nearest_node"]
                elif "," in str(origin):
                    try:
                        lat, lon = map(float, str(origin).split(","))
                        orig_snap = self.snap_location(lat, lon)
                        o_node = orig_snap["nearest_node"]
                    except Exception:
                        pass
            if d_node not in safety_graph:
                if destination in self.nodes and "latitude" in self.nodes[destination] and "longitude" in self.nodes[destination]:
                    dest_snap = self.snap_location(float(self.nodes[destination]["latitude"]), float(self.nodes[destination]["longitude"]))
                    d_node = dest_snap["nearest_node"]
                elif "," in str(destination):
                    try:
                        lat, lon = map(float, str(destination).split(","))
                        dest_snap = self.snap_location(lat, lon)
                        d_node = dest_snap["nearest_node"]
                    except Exception:
                        pass

        if o_node is None or d_node is None:
            return {
                "reachable": False, "path": [], "road_ids": [],
                "distance_km": None, "total_time_min": None,
                "avg_speed_kmh": None, "geometry": [],
                "engine": "safety-dijkstra",
                "route_risk_score": 100.0,
                "safety_grade": "UNREACHABLE",
                "reason": "No accessible road graph nodes near origin or safe zone destination."
            }

        cost, prev = self._dijkstra(safety_graph, o_node, d_node)
        if cost is None:
            return {
                "reachable": False, "path": [], "road_ids": [],
                "distance_km": None, "total_time_min": None,
                "avg_speed_kmh": None, "geometry": [],
                "engine": "safety-dijkstra",
                "route_risk_score": 100.0,
                "safety_grade": "BLOCKED",
                "reason": f"Ground evacuation corridor between {o_node} and {d_node} is completely blocked."
            }

        nodes, segments, ids = self._reconstruct_path(prev, o_node, d_node)
        if origin not in nodes and orig_snap:
            if nodes and nodes[0] != orig_snap["nearest_node"]:
                nodes = [orig_snap["nearest_node"]] + nodes
        if destination not in nodes and dest_snap:
            if nodes and nodes[-1] != dest_snap["nearest_node"]:
                nodes = nodes + [dest_snap["nearest_node"]]

        geometry = self._assemble_geometry(segments, nodes, orig_snap, dest_snap)
        dist_km, eta_min, avg_speed = self._real_route_metrics(segments, geometry, resource_speed_kmh)

        # Composite route safety scoring (0 - 100)
        degraded_segs = [r["id"] for r in segments if str(r.get("status", "")).lower() == "degraded"]
        degraded_count = len(degraded_segs)

        # Base risk from distance and transit time
        raw_risk = 12.0 + (degraded_count * 28.0) + (dist_km * 1.2) + max(0.0, (eta_min - 25.0) * 0.5)
        route_risk_score = round(min(100.0, max(5.0, raw_risk)), 1)

        if route_risk_score <= 35.0:
            safety_grade = "SAFE"
        elif route_risk_score <= 65.0:
            safety_grade = "MODERATE_RISK"
        else:
            safety_grade = "HAZARDOUS"

        # Vehicle suitability assessment
        if degraded_count == 0:
            vehicle_suitability = "OPTIMAL"
        elif degraded_count == 1 and vehicle_type in ("rescue_van", "rescue_vehicle", "ambulance"):
            vehicle_suitability = "ACCEPTABLE"
        elif vehicle_type == "bus" and degraded_count >= 1:
            vehicle_suitability = "SUB-OPTIMAL"
        else:
            vehicle_suitability = "ACCEPTABLE"

        route_out = {
            "reachable": True,
            "corridor_type": "EVACUATION",
            "origin": origin,
            "destination": destination,
            "vehicle_type": vehicle_type,
            "path": nodes,
            "road_ids": ids,
            "road_segments": [{
                "id": r["id"], "from_node": r["from_node"], "to_node": r["to_node"],
                "status": r["status"], "distance_km": r["distance_km"],
                "travel_time_min": r.get("travel_time_min", 0),
            } for r in segments],
            "distance_km": dist_km,
            "total_time_min": eta_min,
            "avg_speed_kmh": avg_speed,
            "route_risk_score": route_risk_score,
            "safety_grade": safety_grade,
            "vehicle_suitability": vehicle_suitability,
            "degraded_segments": degraded_segs,
            "geometry": geometry,
            "engine": "safety-dijkstra",
            "status": "OPEN",
            "notice": "Safety-first evacuation corridor — prioritized for lowest humanitarian risk.",
            "origin_snap": orig_snap,
            "destination_snap": dest_snap,
            "origin_node": o_node,
            "destination_node": d_node,
        }
        route_out["geometry_validation"] = self.validate_route_geometry(route_out)
        return route_out

    def get_evacuation_corridor(self, origin: str, destination: str,
                                vehicle_type: str = "bus",
                                resource_speed_kmh: Optional[float] = None,
                                excluded_road_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Returns full evacuation corridor package containing the primary safest route,
        the alternate safe route, safety comparison, and corridor status.
        """
        primary = self.get_safest_evacuation_route(
            origin, destination, vehicle_type=vehicle_type,
            resource_speed_kmh=resource_speed_kmh, excluded_road_ids=excluded_road_ids
        )
        if not primary["reachable"]:
            return {
                "reachable": False,
                "is_rerouted": False,
                "origin": origin,
                "destination": destination,
                "primary": primary,
                "alternate": None,
                "status": "CORRIDOR_BLOCKED",
                "reason": f"No ground route available from {origin} to safe zone {destination}."
            }

        # Calculate alternate corridor by excluding primary road segments
        primary_ids = set(primary["road_ids"])
        base_exclude = set(excluded_road_ids or [])
        alt_exclude = list(base_exclude | primary_ids)
        alternate = self.get_safest_evacuation_route(
            origin, destination, vehicle_type=vehicle_type,
            resource_speed_kmh=resource_speed_kmh, excluded_road_ids=alt_exclude
        )

        # If primary has no degraded segments or alternate is unreachable, try individual segment exclusions
        if not alternate["reachable"] and len(primary_ids) > 1:
            candidates = []
            for rid in primary_ids:
                trial = list(base_exclude | {rid})
                cand = self.get_safest_evacuation_route(
                    origin, destination, vehicle_type=vehicle_type,
                    resource_speed_kmh=resource_speed_kmh, excluded_road_ids=trial
                )
                if cand["reachable"] and set(cand["road_ids"]) != primary_ids:
                    candidates.append(cand)
            if candidates:
                alternate = min(candidates, key=lambda c: (c["route_risk_score"], c["total_time_min"]))

        delta_km = round((alternate["distance_km"] or 0) - (primary["distance_km"] or 0), 1) if alternate["reachable"] else None
        delta_min = round((alternate["total_time_min"] or 0) - (primary["total_time_min"] or 0), 1) if alternate["reachable"] else None

        return {
            "reachable": True,
            "origin": origin,
            "destination": destination,
            "primary": primary,
            "alternate": alternate,
            "delta_distance_km": delta_km,
            "delta_time_min": delta_min,
            "is_rerouted": False,
            "status": "CORRIDOR_ACTIVE"
        }



def find_route(roads, from_node, to_node, nodes=None, resource_speed_kmh=None):
    result = RoutingService(roads, nodes).get_route(from_node, to_node, resource_speed_kmh=resource_speed_kmh)
    result["status"] = "success" if result["reachable"] else "unreachable"
    result["route_type"] = "ground"
    result["eta_minutes"] = result.get("total_time_min")
    return result


def get_road_geometry(road, nodes=None):
    visual_road = dict(road, status="open")
    result = RoutingService([visual_road], nodes).get_route(
        visual_road["from_node"], visual_road["to_node"], use_snap=False
    )
    geom = result.get("geometry") or visual_road.get("geometry") or []
    if len(geom) < 2 and visual_road.get("geometry"):
        geom = visual_road["geometry"]
    return {"id": road["id"], "geometry": geom, "engine": result.get("engine", "road-graph"),
            "status": road["status"], "distance_km": road.get("distance_km"),
            "travel_time_min": road.get("travel_time_min")}


def compute_all_routes(zones, roads, source="DEPOT", nodes=None):
    service = RoutingService(roads, nodes)
    results = {}
    for z in zones:
        results[z["id"]] = service.get_route(source, z["id"], use_snap=True)
    return results
