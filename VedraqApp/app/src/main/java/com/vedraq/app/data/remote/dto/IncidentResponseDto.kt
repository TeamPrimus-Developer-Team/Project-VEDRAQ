package com.vedraq.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * Historical status transition entry for an incident.
 */
@JsonClass(generateAdapter = false)
data class IncidentHistoryEntryDto(
    @param:Json(name = "status")
    val status: String,

    @param:Json(name = "timestamp")
    val timestamp: String,

    @param:Json(name = "note")
    val note: String? = null
)

/**
 * Authoritative incident payload returned by VEDRAQ Core.
 * Contains server-generated ID, timestamp, and tactical zone data.
 */
@JsonClass(generateAdapter = false)
data class IncidentResponseDto(
    @param:Json(name = "id")
    val id: String,

    @param:Json(name = "title")
    val title: String,

    @param:Json(name = "description")
    val description: String,

    @param:Json(name = "disaster_type")
    val disasterType: String,

    @param:Json(name = "severity")
    val severity: String,

    @param:Json(name = "latitude")
    val latitude: Double,

    @param:Json(name = "longitude")
    val longitude: Double,

    @param:Json(name = "address")
    val address: String? = null,

    @param:Json(name = "reporter_id")
    val reporterId: String? = null,

    @param:Json(name = "people_affected_estimate")
    val peopleAffectedEstimate: Int? = null,

    @param:Json(name = "status")
    val status: String,

    @param:Json(name = "client_incident_id")
    val clientIncidentId: String? = null,

    @param:Json(name = "source")
    val source: String = "VEDRAQ_APP",

    @param:Json(name = "nearest_zone_id")
    val nearestZoneId: String? = null,

    @param:Json(name = "nearest_zone_name")
    val nearestZoneName: String? = null,

    @param:Json(name = "nearest_zone_distance_km")
    val nearestZoneDistanceKm: Double? = null,

    @param:Json(name = "created_at")
    val createdAt: String,

    @param:Json(name = "updated_at")
    val updatedAt: String,

    @param:Json(name = "history")
    val history: List<IncidentHistoryEntryDto> = emptyList()
)
