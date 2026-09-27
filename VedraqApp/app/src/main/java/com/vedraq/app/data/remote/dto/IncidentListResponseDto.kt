package com.vedraq.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * List response wrapper returned by GET /api/incidents.
 */
@JsonClass(generateAdapter = false)
data class IncidentListResponseDto(
    @param:Json(name = "incidents")
    val incidents: List<IncidentResponseDto>,

    @param:Json(name = "total")
    val total: Int
)
