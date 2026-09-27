package com.vedraq.app.data.remote

import com.vedraq.app.data.remote.dto.IncidentResponseDto
import com.vedraq.app.data.remote.mapper.toCreateRequestDto
import com.vedraq.app.data.remote.mapper.toDomain
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class IncidentMapperTest {

    @Test
    fun domain_to_create_request_dto_maps_all_fields_correctly() {
        val domainIncident = Incident(
            id = "CLIENT-12345",
            type = DisasterType.FLOOD,
            severity = SeverityLevel.CRITICAL,
            title = "  Flash Flood on Riverbank  ",
            description = "  Water rising rapidly  ",
            latitude = 25.3050,
            longitude = 83.0100,
            address = "  Ghat Road  ",
            reporterId = "AGENT-007",
            status = IncidentStatus.REPORTED,
            peopleAffectedEstimate = 150,
            isSyncedWithCore = false
        )

        val dto = domainIncident.toCreateRequestDto()

        assertEquals("Flash Flood on Riverbank", dto.title)
        assertEquals("Water rising rapidly", dto.description)
        assertEquals("FLOOD", dto.disasterType)
        assertEquals("CRITICAL", dto.severity)
        assertEquals(25.3050, dto.latitude, 0.0001)
        assertEquals(83.0100, dto.longitude, 0.0001)
        assertEquals("Ghat Road", dto.address)
        assertEquals("AGENT-007", dto.reporterId)
        assertEquals(150, dto.peopleAffectedEstimate)
        assertEquals("CLIENT-12345", dto.clientIncidentId)
        assertEquals("VEDRAQ_APP", dto.source)
    }

    @Test
    fun response_dto_to_domain_maps_authoritative_server_id_and_synced_state() {
        val serverDto = IncidentResponseDto(
            id = "INC-20260923-99AA88",
            title = "Bridge Failure",
            description = "Structural collapse observed",
            disasterType = "INFRASTRUCTURE_FAILURE",
            severity = "HIGH",
            latitude = 25.3100,
            longitude = 83.0150,
            address = "North Bridge",
            reporterId = "UNIT-1",
            peopleAffectedEstimate = 50,
            status = "ACKNOWLEDGED",
            clientIncidentId = "CLIENT-ORIG",
            source = "VEDRAQ_APP",
            nearestZoneId = "ZONE-1",
            nearestZoneName = "Sector 1 Shelter",
            nearestZoneDistanceKm = 1.45,
            createdAt = "2026-09-23T16:45:00.000Z",
            updatedAt = "2026-09-23T16:45:00.000Z"
        )

        val domain = serverDto.toDomain()

        assertEquals("INC-20260923-99AA88", domain.id)
        assertEquals(DisasterType.INFRASTRUCTURE_FAILURE, domain.type)
        assertEquals(SeverityLevel.HIGH, domain.severity)
        assertEquals("Bridge Failure", domain.title)
        assertEquals("Structural collapse observed", domain.description)
        assertEquals(25.3100, domain.latitude, 0.0001)
        assertEquals(83.0150, domain.longitude, 0.0001)
        assertEquals("North Bridge", domain.address)
        assertEquals(IncidentStatus.VERIFIED, domain.status)
        assertTrue(domain.isSyncedWithCore)
        assertTrue(domain.timestamp > 0)
    }

    @Test
    fun response_dto_uses_nearest_zone_fallback_when_address_is_null() {
        val serverDto = IncidentResponseDto(
            id = "INC-20260923-112233",
            title = "Forest Fire",
            description = "Flames near ridge",
            disasterType = "WILDFIRE",
            severity = "CRITICAL",
            latitude = 25.3500,
            longitude = 83.0500,
            address = null,
            status = "REPORTED",
            nearestZoneName = "Highland Base",
            nearestZoneDistanceKm = 2.34,
            createdAt = "2026-09-23T17:00:00.000Z",
            updatedAt = "2026-09-23T17:00:00.000Z"
        )

        val domain = serverDto.toDomain()

        assertNotNull(domain.address)
        assertTrue(domain.address!!.contains("Highland Base"))
        assertTrue(domain.address!!.contains("2.3 km"))
        assertEquals("Highland Base", domain.nearestZoneName)
        assertEquals(2.34, domain.nearestZoneDistanceKm ?: 0.0, 0.01)
    }

    @Test
    fun response_dto_preserves_distinct_address_and_nearest_zone_when_different() {
        val serverDto = IncidentResponseDto(
            id = "INC-20260925-VAR001",
            title = "Central Embankment Flood",
            description = "High surge near command area",
            disasterType = "FLOOD",
            severity = "HIGH",
            latitude = 25.3150,
            longitude = 83.0650,
            address = "Varanasi (Central)",
            status = "REPORTED",
            nearestZoneId = "Z14",
            nearestZoneName = "Chaukaghat",
            nearestZoneDistanceKm = 0.87,
            createdAt = "2026-09-25T01:00:00.000Z",
            updatedAt = "2026-09-25T01:00:00.000Z"
        )

        val domain = serverDto.toDomain()

        // Verify Incident Location preserves selected city
        assertEquals("Varanasi (Central)", domain.address)

        // Verify Nearest Tactical Zone preserves Core resolved zone
        assertEquals("Chaukaghat", domain.nearestZoneName)
        assertEquals(0.87, domain.nearestZoneDistanceKm ?: 0.0, 0.01)

        // Crucial requirement: selected city != nearest zone
        assertTrue(domain.address != domain.nearestZoneName)
    }
}
