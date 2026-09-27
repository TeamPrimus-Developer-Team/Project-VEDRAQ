"""
VEDRAQ — Groq AI Integration Service
=====================================
Dedicated intelligence and systemic risk analysis layer for VEDRAQ.
Interprets deterministic calculations (HCI, Dijkstra routing, greedy allocation)
to detect cascading risks, explain risk drivers, generate prioritized recommendations,
and answer natural language operational queries.

All API keys remain strictly server-side.
Never overrides deterministic VEDRAQ engine calculations.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()
_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
_backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
for _p in (_backend_env, _root_env):
    if os.path.exists(_p):
        load_dotenv(_p, override=True)

logger = logging.getLogger("vedraq.groq_service")

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FALLBACK_MODEL = "llama-3.1-8b-instant"
DEFAULT_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "20.0"))
MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "1"))


def extract_json_payload(raw_text: str) -> Dict[str, Any]:
    """
    Safely parses JSON payload from LLM responses, handling markdown code fences,
    extraneous prefixes/suffixes, and whitespace.
    """
    text = raw_text.strip()
    # Strip markdown block quotes if present
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # Search for first '{' and last '}'
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            substr = text[start_idx : end_idx + 1]
            return json.loads(substr)
        raise ValueError(f"Could not extract valid JSON object from LLM response: {raw_text[:120]}...")


def get_api_key() -> Optional[str]:
    """Retrieve Groq API key from environment."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    return key if key and key != "gsk_your_groq_api_key_here" else None


def get_ai_status() -> Dict[str, Any]:
    """Report status and readiness of the Groq AI service."""
    key = get_api_key()
    return {
        "configured": bool(key),
        "provider": "Groq Cloud" if key else "Deterministic VEDRAQ Engine",
        "model": DEFAULT_MODEL if key else None,
        "mode": "live" if key else "deterministic_fallback",
        "status": "ready" if key else "needs_api_key",
        "timeout_seconds": DEFAULT_TIMEOUT,
        "max_retries": MAX_RETRIES,
        "message": (
            "Groq AI is active and ready."
            if key
            else "GROQ_API_KEY not configured. Running in high-fidelity deterministic fallback mode. Set GROQ_API_KEY in .env to activate live Groq AI."
        ),
    }


def build_systemic_risk_context(
    sim_state: Dict[str, Any],
    baseline_state: Optional[Dict[str, Any]] = None,
    scenario_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extracts a structured, concise context object from the authoritative VEDRAQ state.
    Sends only relevant operational data without raw data bloat.
    """
    zones: List[Dict[str, Any]] = sim_state.get("zones", [])
    roads: List[Dict[str, Any]] = sim_state.get("roads", [])
    facilities: Dict[str, Any] = sim_state.get("facilities", {})
    resources: Dict[str, Any] = sim_state.get("resources", {})
    active_events: List[Dict[str, Any]] = sim_state.get("active_events", [])
    active_dispatches: List[Dict[str, Any]] = sim_state.get("active_dispatches", [])

    # Overview statistics
    critical_zones = [z for z in zones if z.get("classification") == "CRITICAL"]
    high_zones = [z for z in zones if z.get("classification") == "HIGH"]
    moderate_zones = [z for z in zones if z.get("classification") == "MODERATE"]
    lower_zones = [z for z in zones if z.get("classification") == "LOWER"]
    total_affected = sum(z.get("affected_population", 0) for z in zones)

    # Detailed critical & high zones
    priority_focus_zones = []
    for z in (critical_zones + high_zones)[:6]:
        b_factors = [
            f"{b.get('factor')}: {b.get('severity')} (+{b.get('contribution', 0)} pts)"
            for b in z.get("bottlenecks", [])[:3]
        ]
        hosp = z.get("nearest_accessible_hospital") or {}
        shelter = z.get("nearest_accessible_shelter") or {}
        plan = z.get("response_plan") or {}

        priority_focus_zones.append({
            "zone_id": z.get("id"),
            "name": z.get("name"),
            "hci_score": z.get("hci_score"),
            "classification": z.get("classification"),
            "priority_rank": z.get("priority_rank"),
            "affected_population": z.get("affected_population"),
            "damage_percentage": z.get("damage_percentage"),
            "road_accessibility": z.get("road_accessibility"),
            "response_accessibility": z.get("response_accessibility"),
            "accessibility_reason": z.get("accessibility_reason"),
            "top_bottlenecks": b_factors,
            "response_mode": plan.get("mode", "GROUND"),
            "assigned_depot": z.get("best_depot", "DEPOT"),
            "nearest_hospital": (
                f"{hosp.get('hospital_name')} ({hosp.get('distance_km')}km, {hosp.get('eta_min')}min, {hosp.get('beds')} beds)"
                if hosp.get("feasible")
                else "NONE REACHABLE BY ROAD"
            ),
            "nearest_shelter": (
                f"{shelter.get('shelter_name')} ({shelter.get('distance_km')}km, {shelter.get('eta_min')}min, {shelter.get('free_capacity')} cap)"
                if shelter.get("feasible")
                else "NONE AVAILABLE"
            ),
            "required_resources": z.get("required_resources", {}),
        })

    # Road Network Status
    blocked_roads = [r["id"] for r in roads if r.get("status") == "blocked"]
    degraded_roads = [r["id"] for r in roads if r.get("status") == "degraded"]
    open_roads = [r["id"] for r in roads if r.get("status") == "open"]

    # Critical Facilities Status
    hospitals = facilities.get("hospitals", [])
    functional_hospitals = [h["name"] for h in hospitals if h.get("status") == "functional"]
    partial_hospitals = [h["name"] for h in hospitals if h.get("status") == "partial"]
    offline_hospitals = [h["name"] for h in hospitals if h.get("status") == "unavailable"]
    total_beds_available = sum(h.get("available_beds", 0) for h in hospitals)

    shelters = facilities.get("shelters", [])
    full_shelters = [s["name"] for s in shelters if s.get("status") == "full" or (s.get("capacity", 1) - s.get("current_occupancy", 0) <= 0)]
    open_shelters_count = len(shelters) - len(full_shelters)

    # Depots & Air Bases
    depots = facilities.get("depots", [])
    depot_summary = [
        f"{d.get('name')}: Water={d.get('water_stock_units')}u, Food={d.get('food_stock_units')}u, Med={d.get('medical_stock_units')}u"
        for d in depots[:4]
    ]
    heli_bases = facilities.get("helicopter_bases", [])

    # Active Dispatches
    active_disp_summary = []
    for d in active_dispatches:
        active_disp_summary.append({
            "resource_id": d.get("resource_id"),
            "resource_type": d.get("resource_type"),
            "destination_zone": d.get("zone_name"),
            "status": d.get("status"),
            "eta_min": d.get("eta_min"),
            "progress_pct": d.get("progress_pct"),
        })

    # Simulation Deltas (Before vs After)
    deltas = []
    if baseline_state and active_events:
        base_zones_map = {bz["id"]: bz for bz in baseline_state.get("zones", [])}
        for cz in zones:
            bz = base_zones_map.get(cz["id"])
            if bz:
                diff_hci = round(cz.get("hci_score", 0) - bz.get("hci_score", 0), 1)
                b_mode = (bz.get("response_plan") or {}).get("mode", "GROUND")
                c_mode = (cz.get("response_plan") or {}).get("mode", "GROUND")
                mode_escalated = (b_mode != "AIR" and c_mode == "AIR")

                if abs(diff_hci) >= 0.5 or mode_escalated or cz.get("response_accessibility") != bz.get("response_accessibility"):
                    deltas.append({
                        "zone_name": cz.get("name"),
                        "baseline_hci": bz.get("hci_score"),
                        "simulated_hci": cz.get("hci_score"),
                        "delta_hci": diff_hci,
                        "escalated_to_air": mode_escalated,
                        "accessibility_change": f"{bz.get('response_accessibility')} -> {cz.get('response_accessibility')}",
                    })

    if scenario_info:
        scenario_label = f"{scenario_info.get('name', 'Disaster Scenario')} — {scenario_info.get('region', '')} (Synthetic Operational Prototype)"
    elif sim_state.get("scenario_id") == "nepal":
        scenario_label = "Nepal Alpine Disaster — Bagmati & Sindhupalchok, Nepal (Synthetic Operational Prototype)"
    else:
        scenario_label = "Varanasi District Flood 2024 — Uttar Pradesh, India (Synthetic Operational Prototype)"

    return {
        "disaster_scenario": scenario_label,
        "active_what_if_events": active_events,
        "overview": {
            "total_zones": len(zones),
            "critical_zones_count": len(critical_zones),
            "high_zones_count": len(high_zones),
            "moderate_zones_count": len(moderate_zones),
            "lower_zones_count": len(lower_zones),
            "total_affected_population": total_affected,
        },
        "priority_focus_zones": priority_focus_zones,
        "road_network": {
            "total_roads": len(roads),
            "open_count": len(open_roads),
            "degraded_count": len(degraded_roads),
            "blocked_count": len(blocked_roads),
            "blocked_road_ids": blocked_roads,
            "degraded_road_ids": degraded_roads,
        },
        "infrastructure": {
            "hospitals": {
                "total": len(hospitals),
                "functional_count": len(functional_hospitals),
                "functional": functional_hospitals,
                "partial_count": len(partial_hospitals),
                "offline": offline_hospitals,
                "total_available_beds": total_beds_available,
            },
            "shelters": {
                "total": len(shelters),
                "open_count": open_shelters_count,
                "full_shelters": full_shelters,
            },
            "depots": depot_summary,
            "helicopter_bases_count": len(heli_bases),
        },
        "simulation_deltas": deltas,
        "active_dispatches": active_disp_summary,
    }


def analyze_systemic_risk(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes structured VEDRAQ context with Groq AI to produce deep systemic risk reasoning.
    Falls back gracefully to high-fidelity deterministic synthesis if API key is missing or network fails.
    """
    api_key = get_api_key()
    if not api_key:
        logger.info("GROQ_API_KEY not configured; using deterministic fallback synthesizer.")
        res = fallback_systemic_risk_analysis(context)
        res["is_fallback"] = True
        res["provider"] = "Deterministic VEDRAQ Engine"
        res["provider_notice"] = "Running deterministic VEDRAQ analyzer (Configure GROQ_API_KEY in .env to activate live Groq AI)."
        return res

    # Call official Groq API
    try:
        from groq import Groq

        client = Groq(api_key=api_key, timeout=20.0)

        system_prompt = """You are the VEDRAQ Disaster Data Analyst and Systemic Risk Intelligence Engine.
You operate on an AI-assisted disaster-response decision-support platform.
Your task is to interpret deterministic VEDRAQ calculations (HCI scores, Dijkstra road routes, multi-depot inventory, hospital statuses).

STRICT ANTI-HALLUCINATION RULES:
1. Ground all findings ONLY in the provided VEDRAQ operational context.
2. NEVER invent population figures, casualties, unlisted locations, sensor readings, or risk scores.
3. If specific information is not available, explicitly state "Insufficient data available in the current VEDRAQ dataset."
4. NEVER override or dispute VEDRAQ's computed HCI scores or priority rankings. You explain WHY scores are high.
5. In your analysis, clearly differentiate between:
   - VERIFIED GROUND TRUTH: Direct observations from VEDRAQ algorithms/data.
   - AI INFERRED REASONING: Analytical deduction of systemic dependencies.
   - POTENTIAL SCENARIO: Inferred secondary impacts if conditions worsen.

Identify:
- Executive Risk Summary (headline, overview, overall risk level, most critical zone, primary risk driver, major operational concern).
- Key Risk Drivers (systemic bottlenecks driving vulnerability).
- Critical Areas & Infrastructure Vulnerabilities (status, capacity, impact).
- Cascading Failure Detection (multi-step chains: Hazard -> Road/Facility -> Accessibility Loss -> Facility Isolation -> Secondary Operational Impact).
- Actionable Recommendations prioritized into Priority 1 (Immediate), Priority 2 (High), Priority 3 (Monitor) with concrete actions, targets, and rationale.
- AI Confidence & Evidence Basis (rating and bulleted list of verified VEDRAQ inputs).

Return your response strictly as a JSON object matching this schema:
{
  "summary": {
    "headline": "...",
    "overview": "...",
    "overall_risk_level": "CRITICAL" | "HIGH" | "MODERATE" | "LOWER",
    "most_critical_zone": "...",
    "primary_risk_driver": "...",
    "critical_infrastructure_concern": "..."
  },
  "key_risk_drivers": [
    {
      "factor": "...",
      "impact": "CRITICAL" | "HIGH" | "MODERATE",
      "description": "...",
      "affected_zones": ["..."]
    }
  ],
  "critical_areas": [
    {
      "zone_id": "...",
      "zone_name": "...",
      "hci_score": 91.0,
      "classification": "CRITICAL",
      "why_risky": "...",
      "contributing_factors": ["...", "..."],
      "operational_urgency": "..."
    }
  ],
  "cascading_risks": [
    {
      "trigger": "...",
      "chain": ["Step 1", "Step 2", "Step 3", "Step 4"],
      "severity": "CRITICAL" | "HIGH" | "MODERATE",
      "explanation": "...",
      "mitigation": "..."
    }
  ],
  "infrastructure_vulnerabilities": [
    {
      "facility_type": "...",
      "facility_name": "...",
      "status": "...",
      "impact_description": "..."
    }
  ],
  "recommendations": [
    {
      "priority": 1,
      "priority_label": "Immediate",
      "action": "...",
      "target": "...",
      "rationale": "...",
      "resource_type": "..."
    }
  ],
  "confidence": {
    "level": "HIGH" | "MODERATE",
    "evidence_basis": ["...", "..."]
  }
}
"""

        user_content = (
            "Analyze the current VEDRAQ disaster-response operational state and generate systemic risk intelligence:\n\n"
            + json.dumps(context, indent=2)
        )

        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=950,
                    timeout=DEFAULT_TIMEOUT,
                )

                raw_json = response.choices[0].message.content
                parsed = extract_json_payload(raw_json)
                parsed["is_fallback"] = False
                parsed["provider"] = "Groq Cloud"
                parsed["model_used"] = DEFAULT_MODEL
                return parsed

            except Exception as exc:
                last_error = exc
                err_str = str(exc).lower()
                is_rate_limit = "rate limit" in err_str or "429" in err_str or "tpm" in err_str or "rpm" in err_str
                if is_rate_limit:
                    logger.warning(f"Groq API rate limit encountered: {exc}. Immediately transitioning to deterministic fallback.")
                    break
                if attempt < MAX_RETRIES:
                    logger.warning(f"Groq API attempt {attempt + 1} failed ({exc}); retrying...")
                else:
                    logger.error(f"Groq API call failed after {MAX_RETRIES + 1} attempts ({exc}); reverting to fallback synthesizer.")

        res = fallback_systemic_risk_analysis(context)
        res["is_fallback"] = True
        res["provider"] = "Deterministic VEDRAQ Engine"
        err_msg = str(last_error) if last_error else "Unknown error"
        res["fallback_reason"] = f"Groq API unavailable: {err_msg}"
        res["provider_notice"] = f"Live Groq call unavailable ({err_msg[:60]}...). Showing deterministic analysis."
        return res

    except Exception as exc:
        logger.error(f"Error calling Groq API ({exc}); reverting to fallback synthesizer.", exc_info=True)
        res = fallback_systemic_risk_analysis(context)
        res["is_fallback"] = True
        res["provider"] = "Deterministic VEDRAQ Engine"
        res["fallback_reason"] = f"Groq client init/call failed: {str(exc)}"
        res["provider_notice"] = f"Live Groq call encountered an error ({str(exc)[:60]}...). Showing deterministic analysis."
        return res


def query_ai(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Answers an interactive user question about current VEDRAQ conditions,
    grounding the answer strictly in the current operational state.
    """
    api_key = get_api_key()
    if not api_key:
        return deterministic_qa_fallback(question, context)

    try:
        from groq import Groq

        client = Groq(api_key=api_key, timeout=DEFAULT_TIMEOUT)
        system_prompt = """You are the VEDRAQ Disaster AI Assistant.
Answer the responder's question about the disaster state strictly using the supplied VEDRAQ context.
STRICT RULES:
- Never make up information, numbers, or external events.
- If the context doesn't have the answer, say "Insufficient data available in the current VEDRAQ dataset."
- Cite specific zones, roads, HCI scores, hospital statuses, or depot stock from the context.
- Keep answers concise, authoritative, and actionable for incident commanders.

Return a JSON object with:
{
  "answer": "...",
  "supporting_data": ["...", "..."],
  "suggested_followups": ["...", "..."]
}
"""
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"Context:\n{json.dumps(context, indent=2)}\n\nQuestion: {question}",
                        },
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=800,
                    timeout=DEFAULT_TIMEOUT,
                )

                parsed = extract_json_payload(response.choices[0].message.content)
                parsed["is_fallback"] = False
                parsed["provider"] = "Groq Cloud"
                parsed["model_used"] = DEFAULT_MODEL
                return parsed

            except Exception as exc:
                last_error = exc
                err_str = str(exc).lower()
                is_rate_limit = "rate limit" in err_str or "429" in err_str or "tpm" in err_str or "rpm" in err_str
                if is_rate_limit:
                    logger.warning(f"Groq QA rate limit encountered: {exc}. Immediately transitioning to deterministic fallback.")
                    break
                if attempt < MAX_RETRIES:
                    logger.warning(f"Groq QA attempt {attempt + 1} failed ({exc}); retrying...")
                else:
                    logger.error(f"Groq QA query failed after {MAX_RETRIES + 1} attempts: {exc}")

        fallback = deterministic_qa_fallback(question, context)
        fallback["is_fallback"] = True
        fallback["provider"] = "Deterministic VEDRAQ Engine"
        fallback["error"] = str(last_error) if last_error else "Unknown error"
        return fallback

    except Exception as exc:
        logger.error(f"Groq query failed: {exc}", exc_info=True)
        fallback = deterministic_qa_fallback(question, context)
        fallback["is_fallback"] = True
        fallback["provider"] = "Deterministic VEDRAQ Engine"
        fallback["error"] = str(exc)
        return fallback


def fallback_systemic_risk_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic synthesizer that transforms current VEDRAQ state into the exact
    structured systemic risk schema. Used when GROQ_API_KEY is not configured or offline.
    """
    overview = context.get("overview", {})
    focus_zones = context.get("priority_focus_zones", [])
    road_net = context.get("road_network", {})
    infr = context.get("infrastructure", {})
    deltas = context.get("simulation_deltas", [])
    events = context.get("active_what_if_events", [])

    top_zone = focus_zones[0] if focus_zones else {"name": "Sector Area", "zone_id": "Z01", "hci_score": 85.0, "classification": "CRITICAL"}
    blocked_roads = road_net.get("blocked_road_ids", [])
    offline_hospitals = infr.get("hospitals", {}).get("offline", [])
    full_shelters = infr.get("shelters", {}).get("full_shelters", [])

    # Determine primary risk driver from top bottlenecks
    primary_driver = "Medical Isolation & Critical Road Disruptions"
    if focus_zones and focus_zones[0].get("top_bottlenecks"):
        primary_driver = focus_zones[0]["top_bottlenecks"][0].split(":")[0]

    # Overall risk level
    crit_count = overview.get("critical_zones_count", 0)
    overall_level = "CRITICAL" if crit_count >= 2 else "HIGH" if crit_count >= 1 else "MODERATE"

    # Build cascading risk chains from actual state
    cascading_risks = []

    # Chain 1: Road blockage to isolation
    if blocked_roads:
        roads_str = ", ".join(blocked_roads)
        isolated_zones = [z["name"] for z in focus_zones if z.get("response_accessibility") in ("INACCESSIBLE", "DIFFICULT")]
        iso_str = ", ".join(isolated_zones) if isolated_zones else top_zone["name"]
        cascading_risks.append({
            "trigger": f"Road Network Interruption ({roads_str})",
            "chain": [
                f"Severe flooding disables transit corridors ({roads_str})",
                f"Primary supply line to {iso_str} becomes impassable",
                f"Ground response travel time escalates or becomes impossible",
                f"Emergency escalation to aerial helicopter dispatch or alternate long-range bypass"
            ],
            "severity": "CRITICAL" if any(z.get("response_accessibility") == "INACCESSIBLE" for z in focus_zones) else "HIGH",
            "explanation": f"Observed ground blockage on {roads_str} directly isolates populations in {iso_str}, preventing standard ground ambulance and supply logistics.",
            "mitigation": "Clear primary road corridor with engineering crews or stage helicopter payload drops from Air Response Bases."
        })

    # Chain 2: Hospital offline to bed saturation
    if offline_hospitals:
        hosp_str = ", ".join(offline_hospitals)
        cascading_risks.append({
            "trigger": f"Facility Loss: {hosp_str} Offline",
            "chain": [
                f"{hosp_str} becomes non-operational due to flooding/power loss",
                "Local emergency cases cannot receive urgent triage locally",
                "Patient load redirects across road network to nearest functioning hospital",
                "Surrounding facility beds and ambulance transit times face secondary saturation"
            ],
            "severity": "HIGH",
            "explanation": f"When {hosp_str} goes offline, acute trauma and medical cases must travel longer distances, directly increasing mortality risk in high-HCI zones.",
            "mitigation": "Deploy mobile medical teams to affected zones and dispatch patient overflow to District Hospital."
        })

    # Chain 3: Water/Food scarcity cascade
    water_scarce = [z["name"] for z in focus_zones if "Water" in str(z.get("top_bottlenecks")) or "Food" in str(z.get("top_bottlenecks"))]
    if water_scarce:
        cascading_risks.append({
            "trigger": "Lifeline Utility Deficit (Potable Water & Food Depletion)",
            "chain": [
                f"Contamination or supply cutoff in {', '.join(water_scarce[:2])}",
                "Water availability drops to critical threshold",
                "Elevated risk of water-borne pathogens and public dehydration",
                "Emergency water tanker allocation required from central staging depots"
            ],
            "severity": "HIGH",
            "explanation": f"Zones like {water_scarce[0]} have severe water supply deficits that compound flood exposure into secondary public health emergencies.",
            "mitigation": "Immediate dispatch of water tankers and mobile purification units from NDRF Depot 01."
        })

    if not cascading_risks:
        cascading_risks.append({
            "trigger": "Localized Flood Vulnerability",
            "chain": [
                "Riverine water levels rise above danger threshold",
                "Low-lying sectors experience rapid surface inundation",
                "Civilians retreat towards local shelters",
                "Shelter capacity and local supply stocks experience sudden drawdown"
            ],
            "severity": "MODERATE",
            "explanation": "Standard disaster progression where flood exposure strains localized shelter and utility resources.",
            "mitigation": "Pre-position relief stocks and monitor feeder road conditions."
        })

    # Risk Drivers
    key_risk_drivers = [
        {
            "factor": "Medical Service Inaccessibility",
            "impact": "CRITICAL" if any(z.get("nearest_hospital") == "NONE REACHABLE BY ROAD" for z in focus_zones) else "HIGH",
            "description": "Lack of functional trauma care within immediate vicinity compounded by road disruptions.",
            "affected_zones": [z["name"] for z in focus_zones if "Medical" in str(z.get("top_bottlenecks"))] or [top_zone["name"]]
        },
        {
            "factor": "Transit Corridor Disruption",
            "impact": "CRITICAL" if blocked_roads else "MODERATE",
            "description": f"{len(blocked_roads)} road segments closed, forcing vehicles to take extended detours or stranding sectors.",
            "affected_zones": [z["name"] for z in focus_zones if z.get("response_accessibility") != "ACCESSIBLE"] or [top_zone["name"]]
        },
        {
            "factor": "Severe Lifeline Resource Scarcity",
            "impact": "HIGH",
            "description": "Potable water and dry ration shortages requiring rapid multi-depot replenishment.",
            "affected_zones": [z["name"] for z in focus_zones if "Water" in str(z.get("top_bottlenecks")) or "Food" in str(z.get("top_bottlenecks"))]
        }
    ]

    # Critical Areas
    critical_areas = []
    for z in focus_zones[:4]:
        critical_areas.append({
            "zone_id": z.get("zone_id"),
            "zone_name": z.get("name"),
            "hci_score": z.get("hci_score"),
            "classification": z.get("classification"),
            "why_risky": f"HCI {z.get('hci_score')} driven by {', '.join(z.get('top_bottlenecks', ['High vulnerability'])[:2])}.",
            "contributing_factors": z.get("top_bottlenecks", []),
            "operational_urgency": "Immediate intervention required via " + ("Helicopter" if z.get("response_mode") == "AIR" else "Ground corridor"),
        })

    # Infrastructure Vulnerabilities
    infra_vulns = []
    for h in offline_hospitals:
        infra_vulns.append({
            "facility_type": "Hospital",
            "facility_name": h,
            "status": "UNAVAILABLE",
            "impact_description": "Emergency and inpatient capacity reduced to zero; forces cross-district patient rerouting."
        })
    for s in full_shelters:
        infra_vulns.append({
            "facility_type": "Shelter",
            "facility_name": s,
            "status": "FULL / OVERCAPACITY",
            "impact_description": "Cannot admit additional displaced persons; evacuees must seek distant camps."
        })
    if blocked_roads:
        infra_vulns.append({
            "facility_type": "Road Corridors",
            "facility_name": f"Roads: {', '.join(blocked_roads)}",
            "status": "BLOCKED",
            "impact_description": "Dijkstra routing engines detect severe delays or complete ground isolation."
        })

    # Prioritized Recommendations
    recommendations = [
        {
            "priority": 1,
            "priority_label": "Immediate",
            "action": f"Dispatch urgent lifeline resources to {top_zone['name']}",
            "target": top_zone["name"],
            "rationale": f"Zone exhibits highest criticality score ({top_zone.get('hci_score')}) with acute lifeline shortages.",
            "resource_type": "water_tanker / medical_team"
        },
        {
            "priority": 2,
            "priority_label": "High",
            "action": f"Activate alternate logistics route or aerial corridor for isolated sectors",
            "target": top_zone["name"] if top_zone.get("response_mode") == "AIR" else "Transit Network",
            "rationale": "Mitigates road blockages and prevents complete response cutoff.",
            "resource_type": "helicopter / engineering_clearing"
        },
        {
            "priority": 3,
            "priority_label": "Monitor",
            "action": "Continually audit hospital bed availability and shelter food reserves",
            "target": "District Facilities",
            "rationale": "Prevents secondary systemic crisis if additional infrastructure degrades.",
            "resource_type": "monitoring_liaison"
        }
    ]

    headline = f"Systemic Risk Analysis: {top_zone['name']} at {top_zone.get('hci_score')} HCI ({overall_level})"
    overview_text = (
        f"VEDRAQ disaster intelligence identifies {overview.get('critical_zones_count', 0)} critical and "
        f"{overview.get('high_zones_count', 0)} high-risk zones impacting {overview.get('total_affected_population', 0):,} people. "
        f"Primary vulnerabilities stem from {primary_driver.lower()}, with {len(blocked_roads)} road corridors severed. "
        f"{top_zone['name']} represents the most acute operational priority."
    )

    return {
        "summary": {
            "headline": headline,
            "overview": overview_text,
            "overall_risk_level": overall_level,
            "most_critical_zone": f"{top_zone['name']} (HCI {top_zone.get('hci_score')})",
            "primary_risk_driver": primary_driver,
            "critical_infrastructure_concern": f"{len(blocked_roads)} roads blocked; {len(offline_hospitals)} hospitals offline",
        },
        "key_risk_drivers": key_risk_drivers,
        "critical_areas": critical_areas,
        "cascading_risks": cascading_risks,
        "infrastructure_vulnerabilities": infra_vulns,
        "recommendations": recommendations,
        "confidence": {
            "level": "HIGH",
            "evidence_basis": [
                "Authoritative Humanitarian Criticality Index (HCI) weighted model",
                "Deterministic Dijkstra road-graph accessibility evaluations",
                "Live facility bed tracking & multi-depot inventory states",
                "Verified What-If simulation deltas"
            ]
        }
    }


def deterministic_qa_fallback(question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic question-answering synthesizer for offline or non-keyed operation.
    """
    q_lower = question.lower()
    focus_zones = context.get("priority_focus_zones", [])
    top_zone = focus_zones[0] if focus_zones else {"name": "Rampur Tanda", "hci_score": 91.0}
    blocked_roads = context.get("road_network", {}).get("blocked_road_ids", [])
    infr = context.get("infrastructure", {})

    if "why" in q_lower or "risk" in q_lower or top_zone["name"].lower() in q_lower or "critical" in q_lower:
        z = focus_zones[0] if focus_zones else {}
        b_list = "; ".join(z.get("top_bottlenecks", ["Medical Access", "Road Inaccessibility"]))
        ans = (
            f"{z.get('name', 'Rampur Tanda')} is classified as {z.get('classification', 'CRITICAL')} "
            f"with an HCI score of {z.get('hci_score', 91.0)}/100. "
            f"Its primary risk contributors are: {b_list}. "
            f"Road accessibility is {z.get('response_accessibility', 'severely compromised')}, "
            f"and hospital status is {z.get('nearest_hospital', 'unavailable')}."
        )
        supporting = [
            f"HCI Score: {z.get('hci_score')}",
            f"Affected Population: {z.get('affected_population', 0):,}",
            f"Access Status: {z.get('response_accessibility')}",
        ]
        followups = [
            "What cascading failures could happen here?",
            "What are the top recommended actions?",
            "Which infrastructure is most vulnerable?"
        ]
    elif "cascade" in q_lower or "chain" in q_lower or "failure" in q_lower:
        ans = (
            f"A major cascading vulnerability occurs when floodwaters block road segments like {', '.join(blocked_roads) or 'R3'}. "
            f"This cuts off ground access to {top_zone['name']}, forcing traffic onto longer alternative bypasses or causing full isolation. "
            f"Simultaneously, if facilities like local clinics or hospitals go offline, acute patients cannot receive local treatment and "
            f"must be evacuated over compromised roads, necessitating aerial helicopter dispatch."
        )
        supporting = [
            f"Blocked roads: {', '.join(blocked_roads) or 'R3 (potential)'}",
            f"Response mode: {top_zone.get('response_mode', 'GROUND')}",
            f"Air bases available: {infr.get('helicopter_bases_count', 3)}"
        ]
        followups = [
            "Which infrastructure is most vulnerable right now?",
            "What are the top three operational priorities?",
            "Why is this route important?"
        ]
    hosp_sample = infr.get("hospitals", {}).get("functional", [])
    hosp_str = " and ".join(hosp_sample[:2]) if hosp_sample else "designated medical facilities"

    if "infrastructure" in q_lower or "hospital" in q_lower or "shelter" in q_lower:
        h_off = infr.get("hospitals", {}).get("offline", [])
        s_full = infr.get("shelters", {}).get("full_shelters", [])
        ans = (
            f"Infrastructure audit: {len(h_off)} hospitals currently offline ({', '.join(h_off) or 'none offline'}), "
            f"with {infr.get('hospitals', {}).get('total_available_beds', 0)} total operational beds available district-wide. "
            f"Shelter occupancy is under pressure, with {len(s_full)} full shelters ({', '.join(s_full) or 'none at capacity'}). "
            f"Road network reports {len(blocked_roads)} blocked segments ({', '.join(blocked_roads) or 'none'})."
        )
        supporting = [
            f"Available beds: {infr.get('hospitals', {}).get('total_available_beds', 0)}",
            f"Blocked roads: {len(blocked_roads)}",
            f"Open shelters: {infr.get('shelters', {}).get('open_count', 0)}"
        ]
        followups = [
            "What are the top three operational priorities?",
            f"Why is {top_zone['name']} classified as Critical?",
            "What happens if key access roads are blocked?"
        ]
    elif "priority" in q_lower or "action" in q_lower or "recommend" in q_lower:
        ans = (
            f"Top 3 Operational Priorities for responders:\n"
            f"1. IMMEDIATE: Dispatch emergency water tanker and medical team to {top_zone['name']} (HCI {top_zone.get('hci_score')}).\n"
            f"2. HIGH: Secure open transit corridors (bypass {', '.join(blocked_roads) or 'blocked corridors'}) or ready Air Response Base 01 for helicopter evacuation.\n"
            f"3. MONITOR: Continuously track hospital bed availability across {hosp_str}."
        )
        supporting = [
            f"Priority 1 target: {top_zone['name']}",
            f"Critical zones count: {context.get('overview', {}).get('critical_zones_count', 0)}",
            f"Active dispatches: {len(context.get('active_dispatches', []))}"
        ]
        followups = [
            "Why is this area high risk?",
            "What cascading risks exist?",
            "What changed compared with baseline?"
        ]
    else:
        ans = (
            f"VEDRAQ disaster intelligence summary: Currently tracking {context.get('overview', {}).get('total_zones', 15)} zones "
            f"with {context.get('overview', {}).get('critical_zones_count', 0)} critical zones. "
            f"Most critical sector is {top_zone['name']} (HCI {top_zone.get('hci_score')}). "
            f"Road accessibility has {len(blocked_roads)} closed segments. "
            f"All operational dispatches are actively routed to maximize HCI reduction."
        )
        supporting = [
            f"Total affected: {context.get('overview', {}).get('total_affected_population', 0):,}",
            f"Most critical zone: {top_zone['name']}"
        ]
        followups = [
            f"Why is {top_zone['name']} high risk?",
            "What cascading failures could happen?",
            "What are the top three operational concerns?"
        ]

    return {
        "answer": ans,
        "supporting_data": supporting,
        "suggested_followups": followups,
        "is_fallback": True,
        "note": "Deterministic VEDRAQ QA Synthesizer"
    }
