import pytest
from fastapi.testclient import TestClient
from app.main import app, CURRENT_SCENARIO_ID, AVAILABLE_SCENARIOS

client = TestClient(app)

def test_list_scenarios():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert "scenarios" in data
    sc_ids = [s["id"] for s in data["scenarios"]]
    assert "varanasi" in sc_ids
    assert "nepal" in sc_ids


def test_scenario_switching_and_isolation():
    # 1. Start in Varanasi
    client.post("/api/scenario/switch", json={"scenario_id": "varanasi"})
    r1 = client.get("/api/zones")
    assert r1.status_code == 200
    assert r1.json()["total"] == 15
    v_ids = {z["id"] for z in r1.json()["zones"]}
    assert "Z01" in v_ids

    # 2. Switch to Nepal
    sw = client.post("/api/scenario/switch", json={"scenario_id": "nepal"})
    assert sw.status_code == 200
    sw_data = sw.json()
    assert sw_data["status"] == "success"
    assert sw_data["scenario_id"] == "nepal"
    assert "Nepal" in sw_data["name"]
    assert "Nepal" in sw_data["region"]
    assert sw_data["zones_count"] == 10
    assert sw_data["roads_count"] == 12
    assert sw_data["center"] == [27.750, 85.550]
    assert sw_data["zoom"] == 11

    # 3. Verify Nepal zones state
    r2 = client.get("/api/zones")
    assert r2.status_code == 200
    assert r2.json()["total"] == 10
    n_ids = {z["id"] for z in r2.json()["zones"]}
    assert "N01" in n_ids
    assert "N10" in n_ids
    # Ensure complete isolation: No Varanasi zones in Nepal!
    assert len(v_ids.intersection(n_ids)) == 0

    # 4. Verify Nepal roads
    roads_res = client.get("/api/roads")
    assert roads_res.status_code == 200
    road_ids = {r["id"] for r in roads_res.json()["roads"]}
    assert "NR1" in road_ids
    assert "NR3" in road_ids
    assert "R1" not in road_ids  # Varanasi road shouldn't exist

    # 5. Verify Nepal facilities
    fac_res = client.get("/api/facilities")
    assert fac_res.status_code == 200
    facs = fac_res.json()
    hosp_ids = {h["id"] for h in facs.get("hospitals", [])}
    assert "HN1" in hosp_ids
    shelter_ids = {s["id"] for s in facs.get("shelters", [])}
    assert "SN1" in shelter_ids

    # 6. Verify Nepal routing
    route_res = client.get("/api/routes/N01")
    assert route_res.status_code == 200
    r_data = route_res.json()
    assert r_data["zone_id"] == "N01"
    assert r_data["route"]["reachable"] is True
    assert "NR3" in r_data["route"]["road_ids"]

    # 7. Verify Nepal baseline and state endpoints have scenario_id
    base_res = client.get("/api/baseline")
    assert base_res.status_code == 200
    assert base_res.json()["scenario_id"] == "nepal"
    assert len(base_res.json()["zones"]) == 10

    st_res = client.get("/api/state")
    assert st_res.status_code == 200
    assert st_res.json()["scenario_id"] == "nepal"
    assert len(st_res.json()["zones"]) == 10

    # 8. Verify Nepal events
    ev_res = client.get("/api/events")
    assert ev_res.status_code == 200
    assert ev_res.json()["scenario_id"] == "nepal"
    assert len(ev_res.json()["events"]) > 0

    # 9. Verify systemic risk includes Nepal scenario info
    risk_res = client.post("/api/ai/systemic-risk", json={"include_baseline": True})
    assert risk_res.status_code == 200
    assert risk_res.json()["status"] == "success"

    # 10. Switch back to Varanasi
    sw_back = client.post("/api/scenario/switch", json={"scenario_id": "varanasi"})
    assert sw_back.status_code == 200
    assert sw_back.json()["scenario_id"] == "varanasi"
    assert sw_back.json()["zones_count"] == 15

    # 11. Verify Varanasi is restored
    r3 = client.get("/api/zones")
    assert r3.status_code == 200
    assert r3.json()["total"] == 15
    restored_v_ids = {z["id"] for z in r3.json()["zones"]}
    assert "Z01" in restored_v_ids
    assert "N01" not in restored_v_ids


def test_repeated_switching():
    """Default -> Nepal -> Default -> Nepal -> Default: ensures zero state leakage or caching anomalies."""
    for cycle in range(3):
        # Switch to Nepal
        sw_n = client.post("/api/scenario/switch", json={"scenario_id": "nepal"})
        assert sw_n.status_code == 200
        assert sw_n.json()["scenario_id"] == "nepal"
        zn = client.get("/api/zones").json()
        assert zn["total"] == 10
        assert zn["zones"][0]["id"].startswith("N")

        # Switch to Varanasi
        sw_v = client.post("/api/scenario/switch", json={"scenario_id": "varanasi"})
        assert sw_v.status_code == 200
        assert sw_v.json()["scenario_id"] == "varanasi"
        zv = client.get("/api/zones").json()
        assert zv["total"] == 15
        assert zv["zones"][0]["id"].startswith("Z")


def test_dispatch_and_evac_cleared_on_switch():
    """Ensure active dispatches and evacuation plans do not bleed across scenarios."""
    # 1. Reset to Varanasi
    client.post("/api/scenario/switch", json={"scenario_id": "varanasi"})

    # 2. Dispatch a vehicle in Varanasi
    disp_res = client.post("/api/dispatch/send", json={"zone_id": "Z09", "resource_type": "water_tanker"})
    assert disp_res.status_code == 200
    assert disp_res.json()["status"] == "DISPATCHED"

    # Check active dispatches has 1 item
    act = client.get("/api/dispatch/active").json()
    assert len(act.get("dispatches", [])) == 1

    # 3. Switch to Nepal
    sw = client.post("/api/scenario/switch", json={"scenario_id": "nepal"})
    assert sw.status_code == 200

    # 4. Active dispatches must be empty in new scenario
    act_after = client.get("/api/dispatch/active").json()
    assert len(act_after.get("dispatches", [])) == 0

    # 5. Switch back to Varanasi
    client.post("/api/scenario/switch", json={"scenario_id": "varanasi"})
    act_restored = client.get("/api/dispatch/active").json()
    assert len(act_restored.get("dispatches", [])) == 0


def test_invalid_scenario_id():
    res = client.post("/api/scenario/switch", json={"scenario_id": "nonexistent_scenario"})
    assert res.status_code == 400
    assert "Unknown scenario" in res.json()["detail"]
