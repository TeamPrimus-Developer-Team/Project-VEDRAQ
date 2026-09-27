import unittest
from fastapi.testclient import TestClient
from app.main import app, sim, DISPATCHED_VEHICLES
from app.services.autonomous_sim import (
    get_highest_priority_unresolved_area,
    get_available_actions_for_area,
    execute_autonomous_step,
    run_full_autonomous_simulation,
    consult_decision_agent,
)


class AutonomousSimulationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Reset simulation to clean state before each test
        sim.reset()
        global DISPATCHED_VEHICLES
        DISPATCHED_VEHICLES.clear()
        self.client.post("/api/simulation/autonomous/reset")

    def tearDown(self):
        sim.reset()
        global DISPATCHED_VEHICLES
        DISPATCHED_VEHICLES.clear()
        self.client.post("/api/simulation/autonomous/reset")

    def test_highest_priority_unresolved_area_selection(self):
        state = sim.compute_full_state()
        resolved_ids = set()

        # First area must be the top priority (#1)
        area1 = get_highest_priority_unresolved_area(state, resolved_ids)
        self.assertIsNotNone(area1)
        self.assertEqual(area1["priority_rank"], 1)

        # Mark #1 as resolved
        resolved_ids.add(area1["id"])

        # Second area must be #2
        area2 = get_highest_priority_unresolved_area(state, resolved_ids)
        self.assertIsNotNone(area2)
        self.assertNotEqual(area1["id"], area2["id"])
        self.assertEqual(area2["priority_rank"], 2)

    def test_available_actions_are_valid_and_non_empty(self):
        state = sim.compute_full_state()
        top_area = state["zones"][0]
        actions = get_available_actions_for_area(top_area, state)

        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)
        for act in actions:
            self.assertIn("action", act)
            self.assertIn("label", act)
            self.assertIn("expected_effect", act)
            self.assertIn(act["action"], (
                "restore_road",
                "dispatch_resource",
                "aerial_helicopter_response",
                "restore_facility",
                "activate_alternate_route",
                "NO_FEASIBLE_ACTION",
            ))

    def test_single_autonomous_step_execution_and_recalculation(self):
        resolved_ids = set()
        history = []
        dispatches = {}

        # Step 1
        step1 = execute_autonomous_step(sim, resolved_ids, 1, history, dispatches)

        self.assertIn("step_number", step1)
        self.assertEqual(step1["step_number"], 1)
        self.assertIn("target_area", step1)
        self.assertIn("decision", step1)
        self.assertIn("result", step1)
        self.assertIn("current_state", step1)

        # Target must be #1 priority area
        self.assertEqual(step1["target_area"]["rank"], 1)

        # Ground truth recalculation occurred:
        self.assertIn("updated_hci", step1["result"])
        self.assertIn("hci_reduction", step1["result"])

        # If target is still critical/high/moderate, it must NOT be marked resolved
        if not step1["is_target_resolved"]:
            self.assertTrue(step1["continue_same_target"])
            self.assertNotIn(step1["target_area"]["id"], resolved_ids)
            self.assertEqual(step1["active_target_id"], step1["target_area"]["id"])
        else:
            self.assertIn(step1["target_area"]["id"], resolved_ids)

    def test_resolve_then_advance_same_area_continuation(self):
        resolved_ids = set()
        history = []
        dispatches = {}

        # Block R3 so Rampur Tanda becomes CRITICAL (100 HCI)
        sim.apply_events([{"type": "ROAD_BLOCK", "road_id": "R3"}])

        # Step 1
        step1 = execute_autonomous_step(sim, resolved_ids, 1, history, dispatches)
        history.append(step1)
        area1_id = step1["target_area"]["id"]

        # If area 1 is still unresolved (>= 40.0 HCI), Step 2 MUST target the SAME area
        if not step1["is_target_resolved"]:
            step2 = execute_autonomous_step(
                sim,
                resolved_ids,
                2,
                history,
                dispatches,
                active_target_id=step1.get("active_target_id"),
                target_step_count=step1.get("target_step_count", 0),
                concluded_ids=set(step1.get("concluded_ids", [])),
                stagnation_counter=step1.get("stagnation_counter", 0),
            )
            self.assertEqual(step2["target_area"]["id"], area1_id, "AI MUST stay on same area while unresolved!")
            self.assertEqual(step2["target_area"]["target_intervention_number"], 2)

    def test_road_block_scenario_targeting_and_resolution(self):
        # Apply a road block scenario
        sim.apply_events([{"type": "ROAD_BLOCK", "road_id": "R3"}])

        state_after_block = sim.compute_full_state()
        # Find Rampur Tanda (Z01)
        z01 = next(z for z in state_after_block["zones"] if z["id"] == "Z01")
        actions = get_available_actions_for_area(z01, state_after_block)

        # Must include restore_road for R3
        road_actions = [a for a in actions if a["action"] == "restore_road"]
        self.assertTrue(any(a.get("road_id") == "R3" for a in road_actions))

        # Decision agent should prioritize restoring R3 or aerial payload
        decision = consult_decision_agent(z01, actions, state_after_block, [])
        self.assertIn(decision["selected_action"], ("restore_road", "aerial_helicopter_response", "dispatch_resource"))

    def test_full_autonomous_simulation_run(self):
        res = run_full_autonomous_simulation(sim, max_steps=4)

        self.assertEqual(res["status"], "COMPLETED")
        self.assertGreater(len(res["steps"]), 0)
        self.assertLessEqual(len(res["steps"]), 4)
        self.assertIn("initial_state_summary", res)
        self.assertIn("final_state_summary", res)
        self.assertIn("impact", res)
        self.assertIn("final_ai_explanation", res)

        # Verify sequential step numbers
        for i, step in enumerate(res["steps"]):
            self.assertEqual(step["step_number"], i + 1)

    def test_api_autonomous_step_endpoint(self):
        resp = self.client.post("/api/simulation/autonomous/step", json={"reset_session": True})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_steps_so_far"], 1)
        self.assertIn("target_status", data)
        self.assertIn("continue_same_target", data)

    def test_api_autonomous_run_endpoint(self):
        resp = self.client.post("/api/simulation/autonomous/run", json={"max_steps": 3})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "COMPLETED")
        self.assertLessEqual(data["total_steps_executed"], 3)
        self.assertIn("final_ai_explanation", data)

    def test_api_autonomous_reset_endpoint(self):
        # Run 1 step
        self.client.post("/api/simulation/autonomous/step", json={"reset_session": True})
        # Reset
        resp = self.client.post("/api/simulation/autonomous/reset")
        self.assertEqual(resp.status_code, 200)
        # Next step should start at 1 again
        step_resp = self.client.post("/api/simulation/autonomous/step", json={"reset_session": False})
        self.assertEqual(step_resp.json()["step"]["step_number"], 1)

    def test_whatif_scenario_snapshot_synchronization_6_conditions(self):
        # 6 specific What-If conditions:
        # Block R11, Block R13, Block R24, Hospital H1 Offline, Block R12, Shelter S1 Full
        events = [
            {"type": "ROAD_BLOCK", "road_id": "R11"},
            {"type": "ROAD_BLOCK", "road_id": "R13"},
            {"type": "ROAD_BLOCK", "road_id": "R24"},
            {"type": "HOSPITAL_OFFLINE", "facility_id": "H1"},
            {"type": "ROAD_BLOCK", "road_id": "R12"},
            {"type": "SHELTER_FULL", "shelter_id": "S1"},
        ]
        selected_conditions = [
            "Block R11 — Primary Route",
            "Block R13 — Alternative Route",
            "Block R24 — Alternative Route",
            "Hospital H1 Offline",
            "Block R12 — Alternative Route",
            "Shelter S1 Full",
        ]
        scenario_id = "whatif_R11_R13_R24_H1_R12_S1"

        resp = self.client.post(
            "/api/simulation/autonomous/step",
            json={
                "scenario_id": scenario_id,
                "selected_conditions": selected_conditions,
                "events": events,
                "reset_session": True,
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["scenario"]["scenario_id"], scenario_id)
        self.assertEqual(len(data["scenario"]["selected_conditions"]), 6)
        self.assertEqual(data["scenario"]["active_events_count"], 6)

        # Verify that the target area and rankings reflect the degraded/blocked scenario
        step = data["step"]
        self.assertEqual(step["step_number"], 1)
        self.assertIsNotNone(step["target_area"])

        # Check that the underlying simulation state contains the 6 active events
        sim_state = step["current_state"]
        # Hospital H1 should be unavailable in current_state facilities
        h1 = next(h for h in sim_state["facilities"]["hospitals"] if h["id"] == "H1")
        self.assertEqual(h1["status"], "unavailable")
        # Road R11 should be blocked or resolved if AI restored it
        # Shelter S1 should be full or impacted
        s1 = next(s for s in sim_state["facilities"]["shelters"] if s["id"] == "S1")
        self.assertEqual(s1["status"], "full")

    def test_whatif_scenario_isolation_and_no_state_leakage(self):
        # First run with 6 conditions
        events_6 = [
            {"type": "ROAD_BLOCK", "road_id": "R11"},
            {"type": "ROAD_BLOCK", "road_id": "R13"},
            {"type": "ROAD_BLOCK", "road_id": "R24"},
            {"type": "HOSPITAL_OFFLINE", "facility_id": "H1"},
            {"type": "ROAD_BLOCK", "road_id": "R12"},
            {"type": "SHELTER_FULL", "shelter_id": "S1"},
        ]
        self.client.post(
            "/api/simulation/autonomous/step",
            json={
                "scenario_id": "scenario_6_conds",
                "selected_conditions": ["6 conditions"],
                "events": events_6,
                "reset_session": True,
            },
        )

        # Now switch to a scenario with ONLY ROAD_BLOCK R11
        events_1 = [{"type": "ROAD_BLOCK", "road_id": "R11"}]
        resp2 = self.client.post(
            "/api/simulation/autonomous/step",
            json={
                "scenario_id": "scenario_only_r11",
                "selected_conditions": ["Block R11 — Primary Route"],
                "events": events_1,
                "reset_session": True,
            },
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["scenario"]["scenario_id"], "scenario_only_r11")
        self.assertEqual(data2["scenario"]["active_events_count"], 1)

        sim_state2 = data2["step"]["current_state"]
        # Hospital H1 must NOT be offline in this new scenario
        h1 = next(h for h in sim_state2["facilities"]["hospitals"] if h["id"] == "H1")
        self.assertNotEqual(h1["status"], "unavailable")

        # Shelter S1 must NOT be full in this new scenario
        s1 = next(s for s in sim_state2["facilities"]["shelters"] if s["id"] == "S1")
        self.assertNotEqual(s1["status"], "full")

    def test_whatif_reset_preserves_scenario_conditions(self):
        events = [
            {"type": "ROAD_BLOCK", "road_id": "R11"},
            {"type": "HOSPITAL_OFFLINE", "facility_id": "H1"},
        ]
        selected_conditions = ["Block R11", "Hospital H1 Offline"]
        scenario_id = "whatif_r11_h1"

        # Execute Step 1
        resp_step1 = self.client.post(
            "/api/simulation/autonomous/step",
            json={
                "scenario_id": scenario_id,
                "selected_conditions": selected_conditions,
                "events": events,
                "reset_session": True,
            },
        )
        self.assertEqual(resp_step1.status_code, 200)

        # Call Reset passing the same scenario
        resp_reset = self.client.post(
            "/api/simulation/autonomous/reset",
            json={
                "scenario_id": scenario_id,
                "selected_conditions": selected_conditions,
                "events": events,
            },
        )
        self.assertEqual(resp_reset.status_code, 200)
        reset_data = resp_reset.json()
        self.assertEqual(reset_data["status"], "success")
        self.assertEqual(reset_data["scenario_id"], scenario_id)
        self.assertEqual(len(reset_data["active_conditions"]), 2)

        # Initial state returned must retain H1 offline
        h1_init = next(h for h in reset_data["initial_state"]["facilities"]["hospitals"] if h["id"] == "H1")
        self.assertEqual(h1_init["status"], "unavailable")

        # Next autonomous step should execute Step 1 again on this scenario
        resp_step1_after_reset = self.client.post(
            "/api/simulation/autonomous/step",
            json={
                "scenario_id": scenario_id,
                "selected_conditions": selected_conditions,
                "events": events,
                "reset_session": False,
            },
        )
        self.assertEqual(resp_step1_after_reset.status_code, 200)
        self.assertEqual(resp_step1_after_reset.json()["step"]["step_number"], 1)

    def test_acceptance_test_1_must_not_move_from_area_1_while_critical(self):
        """
        Acceptance Test 1 (Section 23):
        Area #1 is CRITICAL (e.g. 100 HCI).
        Step 1 leaves Area #1 still CRITICAL/HIGH (e.g. 98.6).
        The AI MUST stay on Area #1 in Step 2.
        It MUST NOT advance to Area #2 until Area #1 is resolved or safely concluded.
        """
        # Block R3 so Rampur Tanda has HCI 100.0
        sim.apply_events([{"type": "ROAD_BLOCK", "road_id": "R3"}])

        # Step 1
        resp1 = self.client.post(
            "/api/simulation/autonomous/step",
            json={"reset_session": True}
        )
        self.assertEqual(resp1.status_code, 200)
        d1 = resp1.json()
        target_id_1 = d1["step"]["target_area"]["id"]
        after_hci_1 = d1["step"]["target_area"]["after_hci"]

        # Rampur Tanda was 100.0. After step 1 (even if reduced to 98.6 or 80+), it remains CRITICAL/HIGH
        if after_hci_1 >= 40.0:
            self.assertTrue(d1["continue_same_target"], "AI must flag continue_same_target=True when unresolved!")
            self.assertEqual(d1["active_target_id"], target_id_1)
            self.assertIn("STILL", d1["target_status"])

            # Step 2 MUST continue on the SAME Area #1
            resp2 = self.client.post(
                "/api/simulation/autonomous/step",
                json={"reset_session": False}
            )
            self.assertEqual(resp2.status_code, 200)
            d2 = resp2.json()
            target_id_2 = d2["step"]["target_area"]["id"]
            self.assertEqual(
                target_id_1,
                target_id_2,
                f"CRITICAL FLAW DETECTED: AI moved to {target_id_2} while {target_id_1} was still unresolved ({after_hci_1} HCI)!"
            )
            self.assertEqual(d2["step"]["target_area"]["target_intervention_number"], 2)

    def test_acceptance_test_2_immediate_advance_if_area_reaches_green(self):
        """
        Acceptance Test 2 (Section 24):
        If an area drops below 40.0 HCI (GREEN / LOW), the AI immediately marks it
        RESOLVED and advances to the next highest-priority unresolved area on the next step.
        """
        resolved_ids = set()
        concluded_ids = set()
        dispatches = {}

        state = sim.compute_full_state()
        zone0_id = state["zones"][0]["id"]

        # Mark zone0 as having reached GREEN / RESOLVED
        resolved_ids.add(zone0_id)
        concluded_ids.add(zone0_id)

        step_after = execute_autonomous_step(
            sim=sim,
            resolved_ids=resolved_ids,
            step_num=2,
            history=[],
            dispatched_vehicles=dispatches,
            active_target_id=None,
            target_step_count=0,
            concluded_ids=concluded_ids,
            stagnation_counter=0,
        )

        # AI MUST have moved to the next area, NOT zone0
        self.assertNotEqual(step_after["target_area"]["id"], zone0_id)
        self.assertEqual(step_after["target_area"]["target_intervention_number"], 1)

    def test_acceptance_test_3_dynamic_reranking_after_resolution(self):
        """
        Acceptance Test 3 (Section 25):
        After an area is resolved, the system dynamically re-ranks remaining areas
        based on the updated VEDRAQ state and targets the highest priority unresolved area.
        """
        state = sim.compute_full_state()
        top_zone = state["zones"][0]
        resolved_ids = {top_zone["id"]}
        concluded_ids = {top_zone["id"]}

        # Next target chosen must be the highest HCI zone among unresolved
        next_target = get_highest_priority_unresolved_area(state, resolved_ids, concluded_ids)
        self.assertIsNotNone(next_target)

        remaining_sorted = sorted(
            [z for z in state["zones"] if z["id"] not in resolved_ids and z.get("classification") != "LOWER"],
            key=lambda z: -z["hci_score"]
        )
        self.assertEqual(next_target["id"], remaining_sorted[0]["id"])


