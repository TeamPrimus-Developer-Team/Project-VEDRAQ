"""
Unit tests for Synthetic 10-Year Disaster History dataset (2017 - 2026).
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

def test_disaster_history_files_exist():
    varanasi_path = DATA_DIR / "scenarios" / "varanasi" / "disaster_history.json"
    nepal_path = DATA_DIR / "scenarios" / "nepal" / "disaster_history.json"

    assert varanasi_path.exists(), f"Missing {varanasi_path}"
    assert nepal_path.exists(), f"Missing {nepal_path}"

def test_varanasi_zones_disaster_history():
    varanasi_path = DATA_DIR / "scenarios" / "varanasi" / "disaster_history.json"
    with open(varanasi_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    expected_zones = [f"Z{i:02d}" for i in range(1, 16)]
    for zid in expected_zones:
        assert zid in data, f"Zone {zid} missing from Varanasi disaster history"
        events = data[zid]
        assert 5 <= len(events) <= 10, f"Zone {zid} has {len(events)} events (expected 5-10)"

        for ev in events:
            assert "year" in ev
            assert 2017 <= ev["year"] <= 2026, f"Year {ev['year']} outside 2017-2026 range"
            assert "type" in ev and len(ev["type"]) > 0
            assert ev["severity"] in ["Low", "Moderate", "High", "Critical"]
            assert "description" in ev and len(ev["description"]) > 0
            assert isinstance(ev["affectedPopulation"], int) and ev["affectedPopulation"] > 0

def test_nepal_zones_disaster_history():
    nepal_path = DATA_DIR / "scenarios" / "nepal" / "disaster_history.json"
    with open(nepal_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    expected_zones = [f"N{i:02d}" for i in range(1, 11)]
    for zid in expected_zones:
        assert zid in data, f"Zone {zid} missing from Nepal disaster history"
        events = data[zid]
        assert 5 <= len(events) <= 10, f"Zone {zid} has {len(events)} events (expected 5-10)"

        for ev in events:
            assert "year" in ev
            assert 2017 <= ev["year"] <= 2026, f"Year {ev['year']} outside 2017-2026 range"
            assert "type" in ev and len(ev["type"]) > 0
            assert ev["severity"] in ["Low", "Moderate", "High", "Critical"]
            assert "description" in ev and len(ev["description"]) > 0
            assert isinstance(ev["affectedPopulation"], int) and ev["affectedPopulation"] > 0

def test_api_disaster_history_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    # Test Varanasi zone
    r = client.get("/api/disaster-history/Z01?scenario_id=varanasi")
    assert r.status_code == 200
    res = r.json()
    assert res["zone_id"] == "Z01"
    assert res["is_synthetic"] is True
    assert len(res["events"]) >= 5

    # Test Nepal zone
    r2 = client.get("/api/disaster-history/N01?scenario_id=nepal")
    assert r2.status_code == 200
    res2 = r2.json()
    assert res2["zone_id"] == "N01"
    assert res2["is_synthetic"] is True
    assert len(res2["events"]) >= 5

    # Test unknown zone fallback (empty list, not crash)
    r3 = client.get("/api/disaster-history/UNKNOWN_ZONE_999")
    assert r3.status_code == 200
    res3 = r3.json()
    assert res3["events"] == []

    # Test India scenario with alias "india"
    r4 = client.get("/api/disaster-history/Z01?scenario_id=india")
    assert r4.status_code == 200
    res4 = r4.json()
    assert res4["zone_id"] == "Z01"
    assert len(res4["events"]) >= 5

    # Test strict scenario isolation: Nepal zone under India returns empty
    r5 = client.get("/api/disaster-history/N01?scenario_id=varanasi")
    assert r5.status_code == 200
    assert r5.json()["events"] == []

    # Test strict scenario isolation: Varanasi zone under Nepal returns empty
    r6 = client.get("/api/disaster-history/Z01?scenario_id=nepal")
    assert r6.status_code == 200
    assert r6.json()["events"] == []

def test_india_varanasi_geographical_appropriateness():
    """Verify that NO Varanasi/India zone has snowfall, avalanche, blizzard, or snowstorm."""
    varanasi_path = DATA_DIR / "scenarios" / "varanasi" / "disaster_history.json"
    with open(varanasi_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    forbidden = ["snow", "avalanche", "blizzard", "freeze", "frost", "glacial"]
    for zid, events in data.items():
        for ev in events:
            text = (ev.get("type", "") + " " + ev.get("description", "")).lower()
            for term in forbidden:
                assert term not in text, f"Zone {zid} contains inappropriate term '{term}': {ev}"

def test_nepal_alpine_appropriateness():
    """Verify that Nepal zones DO appropriately include mountain/alpine disaster types."""
    nepal_path = DATA_DIR / "scenarios" / "nepal" / "disaster_history.json"
    with open(nepal_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_types = [ev["type"].lower() for evs in data.values() for ev in evs]
    assert any("avalanche" in t for t in all_types), "Expected avalanche events in Nepal scenario"
    assert any("landslide" in t for t in all_types), "Expected landslide events in Nepal scenario"
    assert any("flash flood" in t for t in all_types), "Expected flash flood events in Nepal scenario"
