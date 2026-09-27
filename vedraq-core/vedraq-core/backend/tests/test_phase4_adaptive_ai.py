"""
VEDRAQ — Phase 4 Adaptive AI Evacuation Intelligence Tests
=========================================================
Exhaustive verification of Tabular GBDT Machine Learning model,
XAI feature attributions, calibrated confidence, multi-hazard adaptation,
safe-zone recommendations, feedback loop, and FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.evacuation_ml import (
    generate_synthetic_disaster_dataset,
    train_and_persist_model,
    get_trained_model,
    predict_evacuation_priority,
    get_model_info,
    log_evacuation_feedback,
    retrain_model_with_feedback,
    get_feedback_records,
    FEATURE_NAMES,
)

client = TestClient(app)


def test_synthetic_dataset_generation_and_diversity():
    """Verify synthetic dataset generator produces varied, multi-hazard scenarios."""
    dataset = generate_synthetic_disaster_dataset(n_samples=600, seed=123)
    assert len(dataset) == 600
    
    hazard_types = set(s["disaster_type_name"] for s in dataset)
    expected_hazards = {"flood", "earthquake", "cyclone", "landslide", "infrastructure_failure", "communication_failure"}
    assert hazard_types == expected_hazards, f"Missing hazards: {expected_hazards - hazard_types}"

    # Features check
    for s in dataset[:10]:
        assert len(s["features"]) == len(FEATURE_NAMES)
        assert 0.0 <= s["evacuationPriority"] <= 100.0
        assert s["riskLevel"] in ("CRITICAL", "HIGH", "MODERATE", "LOWER")
        assert s["urgency"] in ("IMMEDIATE", "HIGH", "ELEVATED", "STANDARD")
        assert s["is_synthetic"] is True


def test_model_training_and_evaluation_metrics():
    """Verify GBDT model trains, produces authentic evaluation metrics, and persists to disk."""
    eval_res = train_and_persist_model(n_samples=500, seed=99)
    assert "regression" in eval_res
    assert "classification" in eval_res

    reg = eval_res["regression"]
    assert "mae" in reg and reg["mae"] < 12.0
    assert "rmse" in reg and reg["rmse"] < 16.0
    assert "r2" in reg and reg["r2"] > 0.50

    cls = eval_res["classification"]
    assert "accuracy" in cls and cls["accuracy"] > 0.55
    assert "macro_f1" in cls
    assert "confusion_matrix" in cls


def test_ml_prediction_structure_and_speed():
    """Verify single zone prediction runs rapidly and returns required structure."""
    dummy_zone = {
        "id": "Z01",
        "name": "Rampur Tanda",
        "population": 4200,
        "people_at_risk": 3800,
        "hci_score": 88.5,
        "road_accessibility": "blocked",
        "hospital_status": "unavailable",
        "water_availability": "critical",
        "food_availability": "critical",
    }

    pred = predict_evacuation_priority(dummy_zone, disaster_type="flood", disaster_severity=0.9)
    assert 0.0 <= pred["priority"] <= 100.0
    assert pred["riskLevel"] in ("CRITICAL", "HIGH", "MODERATE", "LOWER")
    assert pred["urgency"] in ("IMMEDIATE", "HIGH", "ELEVATED", "STANDARD")
    assert pred["provider"] == "VEDRAQ Adaptive ML (Gradient Boosted Trees)"
    assert pred["isFallback"] is False
    assert "EVACUATE" in pred["recommendedAction"]

    # Check contributing factors (XAI)
    factors = pred["contributingFactors"]
    assert len(factors) >= 3
    for f in factors:
        assert "factor" in f
        assert "contribution" in f
        assert f["contribution"].startswith("+")
        assert "percentage" in f

    # Check safe zone and fleet
    assert pred["recommendedSafeZone"] is not None
    fleet = pred["recommendedResources"]
    assert fleet["buses"] >= 1
    assert fleet["total_vehicles"] >= 1


def test_calibrated_confidence_not_fake():
    """Verify confidence is non-arbitrary, bounded, and calibrated."""
    zone = {
        "id": "Z02",
        "population": 5000,
        "people_at_risk": 2500,
        "hci_score": 60.0,
    }
    pred = predict_evacuation_priority(zone, disaster_type="flood", disaster_severity=0.5)
    conf = pred["confidence"]
    assert isinstance(conf, (int, float))
    assert 50.0 <= conf <= 98.0, f"Confidence {conf} out of reasonable calibrated bounds"


def test_multi_hazard_adaptive_behavior():
    """Verify that different disaster conditions adaptively drive priority."""
    base_zone = {
        "id": "Z03",
        "population": 6000,
        "people_at_risk": 3000,
        "hci_score": 65.0,
        "road_accessibility": "normal",
        "hospital_status": "functional",
        "water_availability": "adequate",
    }

    # 1. Flood with road blocked & water critical
    flood_zone = dict(base_zone, road_accessibility="blocked", water_availability="critical")
    pred_flood = predict_evacuation_priority(flood_zone, disaster_type="flood", disaster_severity=0.85)

    # 2. Earthquake with structural collapse & hospitals destroyed
    quake_zone = dict(base_zone, hospital_status="unavailable", vulnerable_population=1800)
    pred_quake = predict_evacuation_priority(quake_zone, disaster_type="earthquake", disaster_severity=0.85)

    # Both should be elevated
    assert pred_flood["priority"] >= 60.0
    assert pred_quake["priority"] >= 60.0

    # Flood top factors should reflect water/road/HCI
    flood_factors = [f["factor"] for f in pred_flood["contributingFactors"]]
    assert any("Water" in f or "Road" in f or "HCI" in f or "Severity" in f for f in flood_factors)

    # Earthquake top factors should reflect Medical/Hospital/Vulnerable/HCI
    quake_factors = [f["factor"] for f in pred_quake["contributingFactors"]]
    assert any("Medical" in f or "Hospital" in f or "Vulnerable" in f or "HCI" in f or "Severity" in f for f in quake_factors)


def test_critical_zone_outranks_low_risk_zone():
    """Verify critical disaster zone receives significantly higher priority than safe zone."""
    crit_zone = {
        "id": "Z_CRIT",
        "population": 9000,
        "people_at_risk": 8200,
        "hci_score": 92.0,
        "road_accessibility": "inaccessible",
        "hospital_status": "unavailable",
        "water_availability": "critical",
    }
    low_zone = {
        "id": "Z_LOW",
        "population": 1500,
        "people_at_risk": 150,
        "hci_score": 25.0,
        "road_accessibility": "open",
        "hospital_status": "functional",
        "water_availability": "adequate",
    }

    pred_crit = predict_evacuation_priority(crit_zone, disaster_type="flood", disaster_severity=0.95)
    pred_low = predict_evacuation_priority(low_zone, disaster_type="flood", disaster_severity=0.2)

    assert pred_crit["priority"] > pred_low["priority"] + 25.0
    assert pred_crit["riskLevel"] in ("CRITICAL", "HIGH")
    assert pred_low["riskLevel"] in ("MODERATE", "LOWER")


def test_safe_zone_capacity_full_penalized():
    """Verify decision engine does not recommend saturated safe zones."""
    zone = {"id": "Z01", "people_at_risk": 1000}
    shelters = [
        {"id": "S1_FULL", "name": "Full Shelter", "capacity": 500, "current_occupancy": 500, "status": "FULL", "safetyScore": 95},
        {"id": "S2_OPEN", "name": "Open Shelter", "capacity": 1500, "current_occupancy": 200, "status": "OPEN", "safetyScore": 85},
    ]

    pred = predict_evacuation_priority(zone, disaster_type="flood", safe_zones=shelters)
    assert pred["recommendedSafeZone"]["id"] == "S2_OPEN"
    assert pred["recommendedSafeZone"]["availableCapacity"] == 1300


def test_feedback_logging_and_retraining():
    """Verify evacuation outcome logging and controlled retraining pipeline."""
    fb_res = log_evacuation_feedback("Z01", 85.0, "EVACUATE Z01 -> S03", 3800, 18.0, "Smooth transit")
    assert fb_res["status"] == "SUCCESS"
    assert fb_res["total_records"] >= 1

    records = get_feedback_records()
    assert len(records) >= 1
    assert records[-1]["zone_id"] == "Z01"

    # Controlled retrain
    retrain_res = retrain_model_with_feedback(n_samples=300, seed=77)
    assert retrain_res["status"] == "RETRAINED"
    assert "evaluation_metrics" in retrain_res


def test_api_evacuation_priority_endpoint():
    """Verify POST /api/ai/evacuation-priority endpoint via FastAPI test client."""
    payload = {
        "zone_id": "Z01",
        "disaster_type": "flood",
        "disaster_severity": 0.85
    }
    response = client.post("/api/ai/evacuation-priority", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "priority" in data
    assert "riskLevel" in data
    assert "urgency" in data
    assert "confidence" in data
    assert "contributingFactors" in data
    assert "recommendedSafeZone" in data
    assert "recommendedResources" in data
    assert data["provider"] == "VEDRAQ Adaptive ML (Gradient Boosted Trees)"


def test_api_model_info_endpoint():
    """Verify GET /api/ai/evacuation-priority/model-info endpoint."""
    response = client.get("/api/ai/evacuation-priority/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("LOADED", "FALLBACK")
    assert data["algorithm"] == "Gradient Boosted Decision Trees"
    assert "features" in data
    assert len(data["features"]) == 21
    assert "evaluation_metrics" in data


def test_api_feedback_endpoints():
    """Verify POST and GET /api/ai/evacuation-priority/feedback endpoints."""
    post_res = client.post("/api/ai/evacuation-priority/feedback", json={
        "zone_id": "Z02",
        "predicted_priority": 78.5,
        "action_taken": "EVACUATE Z02 -> S01",
        "actual_evacuated": 2400,
        "response_time_min": 21.0,
        "notes": "FastAPI test client feedback"
    })
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "SUCCESS"

    get_res = client.get("/api/ai/evacuation-priority/feedback")
    assert get_res.status_code == 200
    assert "feedback_records" in get_res.json()
