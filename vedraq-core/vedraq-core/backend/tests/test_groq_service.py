import unittest
from fastapi.testclient import TestClient
from app.main import app, sim, _full_state, get_baseline
from app.services.groq_service import (
    get_ai_status,
    build_systemic_risk_context,
    fallback_systemic_risk_analysis,
    deterministic_qa_fallback,
)


class GroqServiceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_ai_status(self):
        status = get_ai_status()
        self.assertIn("configured", status)
        self.assertIn("provider", status)
        self.assertIn("status", status)

    def test_build_systemic_risk_context(self):
        state = _full_state()
        base = get_baseline()
        context = build_systemic_risk_context(state, base)

        self.assertIn("overview", context)
        self.assertIn("priority_focus_zones", context)
        self.assertIn("road_network", context)
        self.assertIn("infrastructure", context)

        self.assertGreater(context["overview"]["total_zones"], 0)
        self.assertGreater(context["overview"]["total_affected_population"], 0)
        self.assertIsInstance(context["road_network"]["blocked_road_ids"], list)

    def test_fallback_schema_structure(self):
        state = _full_state()
        context = build_systemic_risk_context(state)
        analysis = fallback_systemic_risk_analysis(context)

        # Validate schema fields
        self.assertIn("summary", analysis)
        self.assertIn("headline", analysis["summary"])
        self.assertIn("overall_risk_level", analysis["summary"])
        self.assertIn("key_risk_drivers", analysis)
        self.assertIn("critical_areas", analysis)
        self.assertIn("cascading_risks", analysis)
        self.assertIn("infrastructure_vulnerabilities", analysis)
        self.assertIn("recommendations", analysis)
        self.assertIn("confidence", analysis)

        # Validate cascading risk chain structure
        self.assertGreater(len(analysis["cascading_risks"]), 0)
        first_chain = analysis["cascading_risks"][0]
        self.assertIn("trigger", first_chain)
        self.assertIn("chain", first_chain)
        self.assertIsInstance(first_chain["chain"], list)
        self.assertGreater(len(first_chain["chain"]), 1)
        self.assertIn("severity", first_chain)
        self.assertIn("explanation", first_chain)

        # Validate recommendations
        self.assertGreater(len(analysis["recommendations"]), 0)
        rec = analysis["recommendations"][0]
        self.assertIn("priority", rec)
        self.assertIn("action", rec)
        self.assertIn("rationale", rec)

    def test_deterministic_qa(self):
        state = _full_state()
        context = build_systemic_risk_context(state)

        res1 = deterministic_qa_fallback("Why is this zone high risk?", context)
        self.assertIn("answer", res1)
        self.assertIn("supporting_data", res1)
        self.assertIn("suggested_followups", res1)

        res2 = deterministic_qa_fallback("What cascading failures could occur?", context)
        self.assertIn("answer", res2)
        self.assertIn("supporting_data", res2)

    def test_api_status_endpoint(self):
        resp = self.client.get("/api/ai/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("configured", data)
        self.assertIn("provider", data)

    def test_api_systemic_risk_endpoint(self):
        resp = self.client.post("/api/ai/systemic-risk", json={"include_baseline": True})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("analysis", data)
        self.assertIn("summary", data["analysis"])
        self.assertIn("cascading_risks", data["analysis"])
        self.assertIn("recommendations", data["analysis"])

    def test_api_ask_endpoint(self):
        resp = self.client.post("/api/ai/ask", json={"question": "What are the top three operational priorities?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("response", data)
        self.assertIn("answer", data["response"])

    def test_api_ask_empty_question_fails(self):
        resp = self.client.post("/api/ai/ask", json={"question": "   "})
        self.assertEqual(resp.status_code, 400)

    def test_systemic_risk_with_active_simulation_event(self):
        # Apply a road block event to simulate cascading risk
        apply_resp = self.client.post("/api/simulation/apply", json={"events": [{"type": "ROAD_BLOCK", "road_id": "R3"}]})
        self.assertEqual(apply_resp.status_code, 200)

        # Query systemic risk
        resp = self.client.post("/api/ai/systemic-risk", json={"include_baseline": True})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        analysis = data["analysis"]

        # Check cascading risks detected the blocked road
        triggers = [c.get("trigger", "") for c in analysis.get("cascading_risks", [])]
        self.assertTrue(any("R3" in t for t in triggers))

        # Check context summary shows 1 blocked road and 1 active event
        summary = data.get("context_summary", {})
        self.assertGreaterEqual(summary.get("blocked_roads", 0), 1)
        self.assertGreaterEqual(summary.get("active_events", 0), 1)

        # Reset simulation
        reset_resp = self.client.post("/api/simulation/reset")
        self.assertEqual(reset_resp.status_code, 200)
