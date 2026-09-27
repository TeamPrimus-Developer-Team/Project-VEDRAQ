package com.vedraq.app.domain.model

data class Incident(
    val id: String,
    val type: DisasterType,
    val severity: SeverityLevel,
    val title: String,
    val description: String,
    val latitude: Double,
    val longitude: Double,
    val address: String? = null,
    val reporterId: String? = null,
    val status: IncidentStatus = IncidentStatus.REPORTED,
    val timestamp: Long = System.currentTimeMillis(),
    val peopleAffectedEstimate: Int? = null,
    val isSyncedWithCore: Boolean = false,
    val nearestZoneName: String? = null,
    val nearestZoneDistanceKm: Double? = null
)
