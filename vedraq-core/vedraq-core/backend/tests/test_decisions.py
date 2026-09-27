import unittest
from app.services.criticality import compute_hci
from app.services.routing import RoutingService

def roads():
    return [{"id":"R1","from_node":"DEPOT","to_node":"A","distance_km":2,"travel_time_min":4,"status":"open"},{"id":"R2","from_node":"A","to_node":"Z","distance_km":3,"travel_time_min":6,"status":"open"},{"id":"R3","from_node":"DEPOT","to_node":"Z","distance_km":9,"travel_time_min":20,"status":"open"}]

class DecisionTests(unittest.TestCase):
 def test_criticality_increases_with_unmet_medical_need(self):
    self.assertGreater(compute_hci({"hospital_status":"unavailable"})["hci_score"], compute_hci({"hospital_status":"functional"})["hci_score"])

 def test_route_uses_shortest_road_segments_and_reports_distance(self):
    route = RoutingService(roads()).get_route("DEPOT", "Z")
    self.assertEqual(route["road_ids"], ["R1", "R2"]); self.assertEqual(route["distance_km"], 5)

 def test_blocked_primary_road_uses_alternative(self):
    data = roads(); data[1]["status"] = "blocked"
    route = RoutingService(data).get_route("DEPOT", "Z")
    self.assertTrue(route["reachable"]); self.assertEqual(route["road_ids"], ["R3"])

 def test_inaccessible_route_is_explicit(self):
    data = roads(); data[1]["status"] = data[2]["status"] = "blocked"
    self.assertFalse(RoutingService(data).get_route("DEPOT", "Z")["reachable"])

 def test_every_zone_has_a_safe_structured_route_result(self):
    from app.main import sim
    state = sim.compute_full_state()
    for route in state["routes"].values():
      self.assertIn(route["reachable"], (True, False))
      self.assertIsInstance(route["geometry"], list)
      if route["reachable"]: self.assertGreater(route["distance_km"], 0)
