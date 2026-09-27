package com.vedraq.app.domain.model

enum class DisasterType(val displayName: String) {
    FLOOD("Flood"),
    WILDFIRE("Wildfire"),
    EARTHQUAKE("Earthquake"),
    CYCLONE("Cyclone / Storm"),
    TSUNAMI("Tsunami"),
    LANDSLIDE("Landslide"),
    HAZMAT("Hazmat / Chemical"),
    MEDICAL_EMERGENCY("Medical Emergency"),
    INFRASTRUCTURE_FAILURE("Infrastructure Failure"),
    OTHER("Other Hazard")
}

enum class SeverityLevel(val displayName: String) {
    CRITICAL("Critical - Immediate Threat"),
    HIGH("High - Severe Hazard"),
    MODERATE("Moderate - Caution Advised"),
    LOW("Low - Advisory"),
    SAFE("Normal / Safe")
}

enum class IncidentStatus(val displayName: String) {
    REPORTED("Reported"),
    VERIFIED("Verified"),
    RESPONDING("Response in Progress"),
    RESOLVED("Resolved")
}

enum class SosStatus(val displayName: String) {
    STANDBY("Standby"),
    TRIGGERED("Triggered"),
    TRANSMITTING("Transmitting Coordinates"),
    ACKNOWLEDGED("Acknowledged by Response Center"),
    DISPATCHED("Responders Dispatched"),
    RESOLVED("Resolved")
}
