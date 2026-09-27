"""
VEDRAQ Incident Domain Models & Schemas
========================================
Authoritative Pydantic schemas for emergency incident reporting,
tracking, validation, and lifecycle status management.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IncidentStatus(str, Enum):
    REPORTED = "REPORTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class DisasterType(str, Enum):
    FLOOD = "FLOOD"
    WILDFIRE = "WILDFIRE"
    EARTHQUAKE = "EARTHQUAKE"
    CYCLONE = "CYCLONE"
    TSUNAMI = "TSUNAMI"
    LANDSLIDE = "LANDSLIDE"
    HAZMAT = "HAZMAT"
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    OTHER = "OTHER"


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    SAFE = "SAFE"


class IncidentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Short title or summary")
    description: str = Field(..., min_length=1, max_length=2000, description="Detailed observations and danger context")
    disaster_type: DisasterType = Field(..., description="Hazard or disaster category")
    severity: SeverityLevel = Field(..., description="Severity level assessment")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude coordinate (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude coordinate (-180 to 180)")
    address: Optional[str] = Field(None, max_length=300, description="Optional street address or landmark location")
    reporter_id: Optional[str] = Field(None, max_length=100, description="Reporting agent or responder ID")
    people_affected_estimate: Optional[int] = Field(None, ge=0, description="Estimated number of affected citizens")
    client_incident_id: Optional[str] = Field(None, max_length=100, description="Client local ID for correlation")
    source: Optional[str] = Field("VEDRAQ_APP", max_length=50, description="Client source identifier")


class IncidentStatusUpdateRequest(BaseModel):
    status: IncidentStatus = Field(..., description="Target lifecycle status")
    note: Optional[str] = Field(None, max_length=500, description="Optional note or rationale for status update")


class IncidentHistoryEntry(BaseModel):
    status: IncidentStatus
    timestamp: str
    note: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str = Field(..., description="Authoritative server-generated incident ID")
    title: str
    description: str
    disaster_type: DisasterType
    severity: SeverityLevel
    latitude: float
    longitude: float
    address: Optional[str] = None
    reporter_id: Optional[str] = None
    people_affected_estimate: Optional[int] = None
    status: IncidentStatus
    client_incident_id: Optional[str] = None
    source: str = "VEDRAQ_APP"
    nearest_zone_id: Optional[str] = None
    nearest_zone_name: Optional[str] = None
    nearest_zone_distance_km: Optional[float] = None
    created_at: str
    updated_at: str
    history: List[IncidentHistoryEntry] = []


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int
