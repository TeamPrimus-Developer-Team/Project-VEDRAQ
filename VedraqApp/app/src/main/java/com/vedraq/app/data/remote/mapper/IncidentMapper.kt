package com.vedraq.app.data.remote.mapper

import com.vedraq.app.data.remote.dto.IncidentCreateRequestDto
import com.vedraq.app.data.remote.dto.IncidentResponseDto
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
import java.time.Instant
import java.time.format.DateTimeParseException

/**
 * Maps domain Incident model to remote create request DTO.
 */
fun Incident.toCreateRequestDto(): IncidentCreateRequestDto {
    return IncidentCreateRequestDto(
        title = title.trim(),
        description = description.trim(),
        disasterType = type.name,
        severity = severity.name,
        latitude = latitude,
        longitude = longitude,
        address = address?.trim()?.ifEmpty { null },
        reporterId = reporterId?.trim()?.ifEmpty { null },
        peopleAffectedEstimate = peopleAffectedEstimate,
        clientIncidentId = id.ifEmpty { null },
        source = "VEDRAQ_APP"
    )
}

/**
 * Maps authoritative remote IncidentResponseDto to domain Incident model.
 * Assigns server-authoritative ID, parsed timestamp, and marks as synced.
 */
fun IncidentResponseDto.toDomain(): Incident {
    val domainType = DisasterType.values().firstOrNull {
        it.name.equals(disasterType, ignoreCase = true)
    } ?: DisasterType.OTHER

    val domainSeverity = SeverityLevel.values().firstOrNull {
        it.name.equals(severity, ignoreCase = true)
    } ?: SeverityLevel.HIGH

    val domainStatus = when (status.uppercase()) {
        "REPORTED" -> IncidentStatus.REPORTED
        "ACKNOWLEDGED" -> IncidentStatus.VERIFIED
        "IN_PROGRESS" -> IncidentStatus.RESPONDING
        "RESOLVED" -> IncidentStatus.RESOLVED
        else -> IncidentStatus.REPORTED
    }

    val parsedTimestamp = try {
        Instant.parse(createdAt).toEpochMilli()
    } catch (e: Exception) {
        System.currentTimeMillis()
    }

    val incidentAddress = address?.trim()?.ifEmpty { null }
        ?: nearestZoneName?.let { "Near $it (${String.format(java.util.Locale.US, "%.1f", nearestZoneDistanceKm ?: 0.0)} km)" }

    return Incident(
        id = id,
        type = domainType,
        severity = domainSeverity,
        title = title,
        description = description,
        latitude = latitude,
        longitude = longitude,
        address = incidentAddress,
        reporterId = reporterId,
        status = domainStatus,
        timestamp = parsedTimestamp,
        peopleAffectedEstimate = peopleAffectedEstimate,
        isSyncedWithCore = true,
        nearestZoneName = nearestZoneName?.trim()?.ifEmpty { null },
        nearestZoneDistanceKm = nearestZoneDistanceKm
    )
}
