"""
VEDRAQ Incident Storage & Management Service
============================================
Thread-safe in-memory incident repository and business logic.
Provides authoritative ID assignment, server timestamping,
nearest zone derivation, and status tracking.

Ready for drop-in replacement with PostgreSQL/PostGIS repository.
"""

import math
import uuid
import logging
from datetime import datetime, timezone
from threading import RLock
from typing import List, Dict, Any, Optional

from app.models.incident import (
    IncidentCreateRequest,
    IncidentStatus,
    IncidentResponse,
    IncidentHistoryEntry,
)

logger = logging.getLogger("vedraq.incidents")


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class IncidentStore:
    """
    Thread-safe in-memory store for emergency incidents.
    Keeps state isolated from static scenario datasets.
    """

    def __init__(self):
        self._lock = RLock()
        self._incidents: Dict[str, Dict[str, Any]] = {}

    def _generate_authoritative_id(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        unique_token = uuid.uuid4().hex[:6].upper()
        return f"INC-{date_str}-{unique_token}"

    def create_incident(
        self,
        req: IncidentCreateRequest,
        active_zones: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            incident_id = self._generate_authoritative_id()
            now_iso = datetime.now(timezone.utc).isoformat()

            # Optional derived metadata: nearest zone within active scenario
            nearest_zone_id = None
            nearest_zone_name = None
            nearest_zone_distance_km = None

            if active_zones:
                min_dist = float("inf")
                best_zone = None
                for z in active_zones:
                    z_lat = z.get("latitude")
                    z_lon = z.get("longitude")
                    if z_lat is not None and z_lon is not None:
                        dist = calculate_haversine_distance(req.latitude, req.longitude, float(z_lat), float(z_lon))
                        if dist < min_dist:
                            min_dist = dist
                            best_zone = z
                if best_zone:
                    nearest_zone_id = best_zone.get("id")
                    nearest_zone_name = best_zone.get("name")
                    nearest_zone_distance_km = round(min_dist, 2)

            initial_history = [
                {
                    "status": IncidentStatus.REPORTED.value,
                    "timestamp": now_iso,
                    "note": f"Incident reported via {req.source or 'VEDRAQ_APP'}",
                }
            ]

            incident_record = {
                "id": incident_id,
                "title": req.title,
                "description": req.description,
                "disaster_type": req.disaster_type.value if hasattr(req.disaster_type, "value") else str(req.disaster_type),
                "severity": req.severity.value if hasattr(req.severity, "value") else str(req.severity),
                "latitude": req.latitude,
                "longitude": req.longitude,
                "address": req.address,
                "reporter_id": req.reporter_id,
                "people_affected_estimate": req.people_affected_estimate,
                "status": IncidentStatus.REPORTED.value,
                "client_incident_id": req.client_incident_id,
                "source": req.source or "VEDRAQ_APP",
                "nearest_zone_id": nearest_zone_id,
                "nearest_zone_name": nearest_zone_name,
                "nearest_zone_distance_km": nearest_zone_distance_km,
                "created_at": now_iso,
                "updated_at": now_iso,
                "history": initial_history,
            }

            self._incidents[incident_id] = incident_record
            logger.info(f"Registered new incident: {incident_id} ({req.title})")
            return dict(incident_record)

    def get_all(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._incidents.values())
            if status_filter:
                items = [i for i in items if i.get("status") == status_filter]
            # Order newest first
            items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return [dict(i) for i in items]

    def get_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            item = self._incidents.get(incident_id)
            return dict(item) if item else None

    def update_status(
        self,
        incident_id: str,
        new_status: IncidentStatus,
        note: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            if incident_id not in self._incidents:
                return None

            now_iso = datetime.now(timezone.utc).isoformat()
            target_status_val = new_status.value if hasattr(new_status, "value") else str(new_status)

            record = self._incidents[incident_id]
            record["status"] = target_status_val
            record["updated_at"] = now_iso
            record["history"].append(
                {
                    "status": target_status_val,
                    "timestamp": now_iso,
                    "note": note or f"Status changed to {target_status_val}",
                }
            )
            logger.info(f"Updated incident {incident_id} status to {target_status_val}")
            return dict(record)

    def clear(self) -> None:
        """Clears all incidents from store (for testing)."""
        with self._lock:
            self._incidents.clear()


# Global shared instance
incident_store = IncidentStore()
