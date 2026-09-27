package com.vedraq.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * Payload for updating an incident lifecycle status via PATCH /api/incidents/{id}.
 */
@JsonClass(generateAdapter = false)
data class IncidentStatusUpdateRequestDto(
    @param:Json(name = "status")
    val status: String,

    @param:Json(name = "note")
    val note: String? = null
)
