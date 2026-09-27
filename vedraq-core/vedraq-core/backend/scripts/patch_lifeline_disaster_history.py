"""
Script to patch frontend/lifeline.html with region-aware synthetic disaster history:
- Strict isolation between India (Varanasi) and Nepal scenarios.
- Complete exclusion of snowfall, avalanche, blizzard, and snowstorm for Indian/Varanasi zones.
- Support for window.disasterHistory.india, window.disasterHistory.varanasi, window.disasterHistory.nepal.
- Realistic India disaster types: Flood, Flash Flood, Urban Flooding, Heavy Rainfall, Extreme Rainfall,
  Heatwave, Thunderstorm, Lightning, Waterlogging, Hailstorm, Drought, Dust Storm, Cloudburst, Fire.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
HTML_PATH = BASE_DIR / "frontend" / "lifeline.html"
VARANASI_JSON_PATH = BASE_DIR / "data" / "scenarios" / "varanasi" / "disaster_history.json"
NEPAL_JSON_PATH = BASE_DIR / "data" / "scenarios" / "nepal" / "disaster_history.json"

with open(VARANASI_JSON_PATH, "r", encoding="utf-8") as f:
    varanasi_history = json.load(f)

with open(NEPAL_JSON_PATH, "r", encoding="utf-8") as f:
    nepal_history = json.load(f)

# Sanitize Varanasi history to ensure 100% absence of cold/snow/avalanche
forbidden_keywords = ["snow", "avalanche", "blizzard", "freeze", "frost", "glacial"]
for zid, ev_list in varanasi_history.items():
    for ev in ev_list:
        combined_txt = (ev.get("type", "") + " " + ev.get("description", "")).lower()
        for kw in forbidden_keywords:
            if kw in combined_txt:
                raise ValueError(f"Forbidden keyword '{kw}' found in Varanasi zone {zid}: {ev}")

combined_data = {
    "india": varanasi_history,
    "varanasi": varanasi_history,
    "nepal": nepal_history
}

js_dataset_code = f"""// ═══════════════════════════════════════════════════════
// 10-YEAR SYNTHETIC DISASTER HISTORY DATASET (2017 – 2026)
// Region-Aware: Strict separation between India and Nepal
// ═══════════════════════════════════════════════════════
const disasterHistory = {json.dumps(combined_data, indent=2, ensure_ascii=False)};
window.disasterHistory = disasterHistory;
const SYNTHETIC_DISASTER_HISTORY = disasterHistory;

function getDisasterIcon(dtype) {{
  const t = (dtype || '').toLowerCase();
  if (t.includes('dust storm')) return '🌪️';
  if (t.includes('hail')) return '🌨️';
  if (t.includes('cyclone') || t.includes('tropical storm') || t.includes('squall')) return '🌀';
  if (t.includes('flood') || t.includes('inundat') || t.includes('waterlog') || t.includes('river')) return '🌊';
  if (t.includes('landslide') || t.includes('mudslide') || t.includes('debris') || t.includes('rockfall') || t.includes('slope')) return '🏔️';
  if (t.includes('earthquake') || t.includes('seismic') || t.includes('tremor')) return '🌋';
  if (t.includes('avalanche') || t.includes('snow') || t.includes('blizzard')) return '❄️';
  if (t.includes('cloudburst') || t.includes('rain') || t.includes('downpour') || t.includes('storm')) return '🌧️';
  if (t.includes('lightning') || t.includes('thunder')) return '⚡';
  if (t.includes('heat') || t.includes('drought') || t.includes('dry')) return '☀️';
  if (t.includes('fire')) return '🔥';
  return '⚠️';
}}

function renderDisasterHistory(zone, scenarioId) {{
  if (!zone) return '';

  let scKey = (scenarioId || currentScenario || 'varanasi').toLowerCase();
  if (scKey.includes('nepal')) {{
    scKey = 'nepal';
  }} else {{
    scKey = 'varanasi';
  }}

  // Strict scenario isolation: prevent mixing India and Nepal histories
  if (scKey === 'varanasi' && zone.id && zone.id.startsWith('N')) {{
    return `
      <div class="disaster-history-card">
        <div class="dh-header">
          <div class="dh-title-wrap">
            <div class="dh-tag">Historical Intelligence</div>
            <div class="dh-title">10-Year Disaster History <span class="dh-range-pill">2017 – 2026</span></div>
          </div>
          <span class="dh-disclaimer-pill" title="Synthetic demo dataset for VEDRAQ disaster intelligence evaluation">Synthetic Demo Data</span>
        </div>
        <div class="dh-empty-history">
          No historical disaster records available for this zone.
        </div>
      </div>
    `;
  }}

  if (scKey === 'nepal' && zone.id && zone.id.startsWith('Z')) {{
    return `
      <div class="disaster-history-card">
        <div class="dh-header">
          <div class="dh-title-wrap">
            <div class="dh-tag">Historical Intelligence</div>
            <div class="dh-title">10-Year Disaster History <span class="dh-range-pill">2017 – 2026</span></div>
          </div>
          <span class="dh-disclaimer-pill" title="Synthetic demo dataset for VEDRAQ disaster intelligence evaluation">Synthetic Demo Data</span>
        </div>
        <div class="dh-empty-history">
          No historical disaster records available for this zone.
        </div>
      </div>
    `;
  }}

  const scData = (window.disasterHistory && window.disasterHistory[scKey]) || SYNTHETIC_DISASTER_HISTORY[scKey] || {{}};
  const rawEvents = scData[zone.id] || [];

  // Regional relevance check: non-Himalayan Indian zones strictly exclude snow/avalanche/blizzard
  const isHimalayan = scKey === 'nepal' || (zone.name && /himalay|kashmir|ladakh|shimla|manali|uttarakhand/i.test(zone.name));
  const events = rawEvents.filter(ev => {{
    if (!isHimalayan) {{
      const txt = ((ev.type || '') + ' ' + (ev.description || '')).toLowerCase();
      if (txt.includes('snow') || txt.includes('avalanche') || txt.includes('blizzard') || txt.includes('freeze') || txt.includes('frost')) {{
        return false;
      }}
    }}
    return true;
  }});

  if (!events || events.length === 0) {{
    return `
      <div class="disaster-history-card">
        <div class="dh-header">
          <div class="dh-title-wrap">
            <div class="dh-tag">Historical Intelligence</div>
            <div class="dh-title">10-Year Disaster History <span class="dh-range-pill">2017 – 2026</span></div>
          </div>
          <span class="dh-disclaimer-pill" title="Synthetic demo dataset for VEDRAQ disaster intelligence evaluation">Synthetic Demo Data</span>
        </div>
        <div class="dh-empty-history">
          No historical disaster records available for this zone.
        </div>
      </div>
    `;
  }}

  // Sort events chronologically descending (newest 2026 down to 2017)
  const sortedEvents = [...events].sort((a, b) => b.year - a.year);

  // Statistics calculation
  const totalEvents = events.length;
  const highSevCount = events.filter(e => e.severity === 'High' || e.severity === 'Critical').length;

  // Most frequent disaster type
  const typeCounts = {{}};
  events.forEach(e => {{
    typeCounts[e.type] = (typeCounts[e.type] || 0) + 1;
  }});
  let mostFrequentType = '—';
  let maxCount = 0;
  for (const [t, c] of Object.entries(typeCounts)) {{
    if (c > maxCount) {{
      maxCount = c;
      mostFrequentType = t;
    }}
  }}

  // Highest impact year (by affected population)
  let highestImpactYear = '—';
  let maxAffected = -1;
  events.forEach(e => {{
    const pop = Number(e.affectedPopulation) || 0;
    if (pop > maxAffected) {{
      maxAffected = pop;
      highestImpactYear = `${{e.year}} (${{maxAffected.toLocaleString()}})`;
    }}
  }});

  const timelineItemsHtml = sortedEvents.map(ev => {{
    const icon = getDisasterIcon(ev.type);
    const sevClass = (ev.severity || 'Moderate').toUpperCase();
    const durationHtml = ev.duration ? `<span class="dh-meta-pill">⏱ ${{ev.duration}}</span>` : '';
    const outcomeHtml = ev.outcome ? `<span class="dh-meta-pill" title="${{ev.outcome}}">✓ ${{ev.outcome}}</span>` : '';

    return `
      <div class="dh-timeline-item">
        <div class="dh-timeline-node ${{sevClass}}"></div>
        <div class="dh-timeline-card ${{sevClass}}">
          <div class="dh-item-header">
            <div class="dh-item-year-sev">
              <span class="dh-item-year">${{ev.year}}</span>
              <span class="dh-item-sev-badge ${{sevClass}}">${{ev.severity}}</span>
            </div>
            <div style="font-size:10px;color:var(--text-muted);font-weight:700">
              👥 <span class="dh-affected-val">${{(Number(ev.affectedPopulation) || 0).toLocaleString()}}</span> affected
            </div>
          </div>
          <div class="dh-item-type">${{icon}} ${{ev.type}}</div>
          <div class="dh-item-desc">"${{ev.description}}"</div>
          ${{(durationHtml || outcomeHtml) ? `
            <div class="dh-item-footer">
              ${{durationHtml}}
              ${{outcomeHtml}}
            </div>
          ` : ''}}
        </div>
      </div>
    `;
  }}).join('');

  return `
    <div class="disaster-history-card">
      <div class="dh-header">
        <div class="dh-title-wrap">
          <div class="dh-tag">Historical Intelligence</div>
          <div class="dh-title">10-Year Disaster History <span class="dh-range-pill">2017 – 2026</span></div>
        </div>
        <span class="dh-disclaimer-pill" title="Synthetic demo dataset for VEDRAQ disaster intelligence evaluation">Synthetic Demo Data</span>
      </div>

      <div class="dh-summary-grid">
        <div class="dh-stat-box">
          <span class="dh-stat-lbl">Total Events</span>
          <span class="dh-stat-val">${{totalEvents}}</span>
        </div>
        <div class="dh-stat-box">
          <span class="dh-stat-lbl">High Severity</span>
          <span class="dh-stat-val high-crit">${{highSevCount}}</span>
        </div>
        <div class="dh-stat-box" title="${{mostFrequentType}}">
          <span class="dh-stat-lbl">Most Frequent</span>
          <span class="dh-stat-val accent" style="font-size:11px">${{mostFrequentType}}</span>
        </div>
        <div class="dh-stat-box" title="Peak impact: ${{highestImpactYear}}">
          <span class="dh-stat-lbl">Peak Impact Year</span>
          <span class="dh-stat-val" style="font-size:11px">${{highestImpactYear}}</span>
        </div>
      </div>

      <div style="font-size:8.5px;color:var(--text-muted);font-weight:750;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">
        Chronological Timeline (${{zone.name}})
      </div>
      <div class="dh-timeline-container">
        ${{timelineItemsHtml}}
      </div>
    </div>
  `;
}}
"""

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html_content = f.read()

# Replace previous SYNTHETIC_DISASTER_HISTORY block up to "// ZONE DETAIL PANEL"
start_marker = "// ═══════════════════════════════════════════════════════\n// 10-YEAR SYNTHETIC DISASTER HISTORY DATASET (2017 – 2026)"
end_marker = "// ═══════════════════════════════════════════════════════\n// ZONE DETAIL PANEL"

start_idx = html_content.find(start_marker)
end_idx = html_content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"Error: Markers not found. start_idx: {start_idx}, end_idx: {end_idx}")
    exit(1)

html_content = html_content[:start_idx] + js_dataset_code + "\n\n" + html_content[end_idx:]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully updated {HTML_PATH} with region-aware disaster history.")
