package com.vedraq.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * Request payload sent to VEDRAQ Core when dispatching an emergency incident report.
 * Matches backend `IncidentCreateRequest` schema.
 */
@JsonClass(generateAdapter = false)
data class IncidentCreateRequestDto(
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

    @param:Json(name = "client_incident_id")
    val clientIncidentId: String? = null,

    @param:Json(name = "source")
    val source: String = "VEDRAQ_APP"
)
