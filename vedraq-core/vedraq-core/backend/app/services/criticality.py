"""
Humanitarian Criticality Index (HCI) Scoring Engine
====================================================
DISCLAIMER: These weights and thresholds are prototype decision-support
values only. They have NOT been scientifically validated or endorsed by
any government body. They are intended for demonstration purposes in the
LIFELINE prototype.

The HCI produces a 0-100 score where 100 = most critically underserved.
"""

from typing import Dict, Any, List

# ── Configurable weights (must sum to 1.0) ───────────────────────────────────
WEIGHTS: Dict[str, float] = {
    "affected_population": 0.15,
    "damage_severity":     0.10,
    "medical_access":      0.20,
    "water_availability":  0.18,
    "food_availability":   0.12,
    "shelter_access":      0.10,
    "road_accessibility":  0.10,
    "communication":       0.05,
}

# ── Configurable classification thresholds ───────────────────────────────────
THRESHOLDS = {
    "CRITICAL":  80,
    "HIGH":      60,
    "MODERATE":  40,
    # below 40 = LOWER
}

# ── Sub-score calculators (each returns 0-100, higher = worse) ───────────────

def _score_affected_population(zone: Dict) -> float:
    """Normalize affected population. 5000+ → score 100."""
    pop = zone.get("affected_population", 0)
    return min(pop / 5000, 1.0) * 100


def _score_damage(zone: Dict) -> float:
    """Damage percentage direct map 0-100."""
    return float(zone.get("damage_percentage", 0))


def _score_medical(zone: Dict) -> float:
    """unavailable=100, partial=55, functional=10."""
    status = zone.get("hospital_status", "unavailable")
    mapping = {"unavailable": 100, "partial": 55, "functional": 10}
    return float(mapping.get(status, 100))


def _score_water(zone: Dict) -> float:
    """none=100, partial=55, adequate=10."""
    avail = zone.get("water_availability", "none")
    mapping = {"none": 100, "partial": 55, "adequate": 10}
    return float(mapping.get(avail, 100))


def _score_food(zone: Dict) -> float:
    """critical=100, partial=55, adequate=10."""
    avail = zone.get("food_availability", "critical")
    mapping = {"critical": 100, "partial": 55, "adequate": 10}
    return float(mapping.get(avail, 100))


def _score_shelter(zone: Dict) -> float:
    """Distance >20 km = 100; 0 km = 0. Cap at 20 km."""
    dist = zone.get("shelter_distance_km", 0)
    return min(dist / 20.0, 1.0) * 100


def _score_road(zone: Dict) -> float:
    """blocked=100, degraded=55, open=5."""
    status = zone.get("road_accessibility", "blocked")
    mapping = {"blocked": 100, "degraded": 55, "open": 5}
    return float(mapping.get(status, 100))


def _score_communication(zone: Dict) -> float:
    """none=100, intermittent=55, functional=5."""
    status = zone.get("communication_status", "none")
    mapping = {"none": 100, "intermittent": 55, "functional": 5}
    return float(mapping.get(status, 100))


# ── Main HCI computation ──────────────────────────────────────────────────────

def compute_hci(zone: Dict) -> Dict[str, Any]:
    """
    Compute the Humanitarian Criticality Index for a single zone.
    Returns score, classification, component breakdown, and explanation.
    """
    components = {
        "affected_population": _score_affected_population(zone),
        "damage_severity":     _score_damage(zone),
        "medical_access":      _score_medical(zone),
        "water_availability":  _score_water(zone),
        "food_availability":   _score_food(zone),
        "shelter_access":      _score_shelter(zone),
        "road_accessibility":  _score_road(zone),
        "communication":       _score_communication(zone),
    }

    # Weighted sum
    raw_score = sum(components[k] * WEIGHTS[k] for k in components)
    hci_score = round(min(raw_score, 100), 1)

    # Classification
    if hci_score >= THRESHOLDS["CRITICAL"]:
        classification = "CRITICAL"
    elif hci_score >= THRESHOLDS["HIGH"]:
        classification = "HIGH"
    elif hci_score >= THRESHOLDS["MODERATE"]:
        classification = "MODERATE"
    else:
        classification = "LOWER"

    # Explanation: rank components by weighted contribution descending
    contributions = {
        k: round(components[k] * WEIGHTS[k], 2) for k in components
    }
    sorted_bottlenecks = sorted(contributions.items(), key=lambda x: -x[1])

    # Human-readable labels
    labels = {
        "affected_population": "Affected Population",
        "damage_severity":     "Damage Severity",
        "medical_access":      "Medical Access",
        "water_availability":  "Water Availability",
        "food_availability":   "Food Availability",
        "shelter_access":      "Shelter Access",
        "road_accessibility":  "Road Accessibility",
        "communication":       "Communication",
    }

    def severity_label(score: float) -> str:
        if score >= 80: return "Critical"
        if score >= 55: return "Poor"
        if score >= 30: return "Limited"
        return "Adequate"

    explanation = []
    for key, contrib in sorted_bottlenecks[:5]:
        explanation.append({
            "factor":       labels[key],
            "raw_score":    round(components[key], 1),
            "contribution": contrib,
            "severity":     severity_label(components[key]),
        })

    return {
        "hci_score":      hci_score,
        "classification": classification,
        "components":     components,
        "bottlenecks":    explanation,
        "weights_used":   WEIGHTS,
    }


def classify_all_zones(zones: List[Dict]) -> List[Dict]:
    """Compute HCI for all zones and return sorted by score descending."""
    results = []
    for zone in zones:
        hci = compute_hci(zone)
        results.append({**zone, **hci})
    results.sort(key=lambda z: -z["hci_score"])
    for i, z in enumerate(results):
        z["priority_rank"] = i + 1
    return results
