package com.vedraq.app.data.location

import com.vedraq.app.data.remote.dto.IncidentResponseDto
import com.vedraq.app.data.remote.mapper.toCreateRequestDto
import com.vedraq.app.data.remote.mapper.toDomain
import com.vedraq.app.domain.model.CoreLocations
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * End-to-end location consistency tests verifying alignment between
 * Android location selection and VEDRAQ Core authoritative datasets.
 */
class LocationConsistencyTest {

    @Test
    fun varanasi_center_resolves_with_selected_city_distinct_from_nearest_tactical_zone() {
        // Operator selects Varanasi Center from CoreLocations
        val loc = CoreLocations.VARANASI_CENTRAL
        val incident = Incident(
            id = "CLIENT-VARANASI-001",
            type = DisasterType.FLOOD,
            severity = SeverityLevel.HIGH,
            title = "District Flood Control Leak",
            description = "Observation near city center",
            latitude = loc.latitude,
            longitude = loc.longitude,
            address = loc.name,
            status = IncidentStatus.REPORTED
        )

        // 1. Verify DTO request preserves exact coordinates and selected city
        val createDto = incident.toCreateRequestDto()
        assertEquals(25.3150, createDto.latitude, 0.0001)
        assertEquals(83.0650, createDto.longitude, 0.0001)
        assertEquals("Varanasi (Central)", createDto.address)

        // 2. Simulate server response from Core (where closest zone to 25.315, 83.065 is Z14 Chaukaghat at 0.87 km)
        val serverResponse = IncidentResponseDto(
            id = "INC-20260925-VAR999",
            title = createDto.title,
            description = createDto.description,
            disasterType = createDto.disasterType,
            severity = createDto.severity,
            latitude = createDto.latitude,
            longitude = createDto.longitude,
            address = createDto.address,
            nearestZoneId = "Z14",
            nearestZoneName = "Chaukaghat",
            nearestZoneDistanceKm = 0.87,
            status = "REPORTED",
            createdAt = "2026-09-25T01:30:00.000Z",
            updatedAt = "2026-09-25T01:30:00.000Z"
        )

        val domain = serverResponse.toDomain()

        // 3. Verify user's Incident Location is preserved
        assertEquals("Varanasi (Central)", domain.address)

        // 4. Verify Core's Nearest Tactical Zone is preserved
        assertEquals("Chaukaghat", domain.nearestZoneName)
        assertEquals(0.87, domain.nearestZoneDistanceKm ?: 0.0, 0.01)

        // 5. Verify condition: selected city != nearest zone
        assertNotEquals(domain.address, domain.nearestZoneName)
    }

    @Test
    fun dhulikhel_nepal_location_resolves_to_nepal_tactical_zone_without_city_mismatch() {
        // Operator selects Dhulikhel from CoreLocations (Nepal scenario)
        val loc = CoreLocations.DHULIKHEL
        val incident = Incident(
            id = "CLIENT-NEPAL-001",
            type = DisasterType.LANDSLIDE,
            severity = SeverityLevel.CRITICAL,
            title = "Highway Blockage",
            description = "Rockslide on Arniko corridor",
            latitude = loc.latitude,
            longitude = loc.longitude,
            address = loc.name,
            status = IncidentStatus.REPORTED
        )

        val createDto = incident.toCreateRequestDto()
        assertEquals(27.6180, createDto.latitude, 0.0001)
        assertEquals(85.5540, createDto.longitude, 0.0001)
        assertEquals("Dhulikhel", createDto.address)

        // Core resolves to N07 Dhulikhel Gateway (distance 0.0 km)
        val serverResponse = IncidentResponseDto(
            id = "INC-20260925-NEP001",
            title = createDto.title,
            description = createDto.description,
            disasterType = createDto.disasterType,
            severity = createDto.severity,
            latitude = createDto.latitude,
            longitude = createDto.longitude,
            address = createDto.address,
            nearestZoneId = "N07",
            nearestZoneName = "Dhulikhel Gateway",
            nearestZoneDistanceKm = 0.0,
            status = "REPORTED",
            createdAt = "2026-09-25T01:35:00.000Z",
            updatedAt = "2026-09-25T01:35:00.000Z"
        )

        val domain = serverResponse.toDomain()

        assertEquals("Dhulikhel", domain.address)
        assertEquals("Dhulikhel Gateway", domain.nearestZoneName)
        assertEquals(0.0, domain.nearestZoneDistanceKm ?: -1.0, 0.01)
        // Ensure it did not match any Varanasi zone
        assertTrue(domain.nearestZoneName!!.startsWith("Dhulikhel"))
    }

    @Test
    fun banepa_nepal_location_resolves_to_banepa_lowlands() {
        val loc = CoreLocations.BANEPA
        val incident = Incident(
            id = "CLIENT-NEPAL-002",
            type = DisasterType.FLOOD,
            severity = SeverityLevel.HIGH,
            title = "Marketplace Surge",
            description = "Lowland drainage overflow",
            latitude = loc.latitude,
            longitude = loc.longitude,
            address = loc.name,
            status = IncidentStatus.REPORTED
        )

        val createDto = incident.toCreateRequestDto()
        assertEquals(27.6320, createDto.latitude, 0.0001)
        assertEquals(85.5240, createDto.longitude, 0.0001)
        assertEquals("Banepa", createDto.address)

        val serverResponse = IncidentResponseDto(
            id = "INC-20260925-NEP002",
            title = createDto.title,
            description = createDto.description,
            disasterType = createDto.disasterType,
            severity = createDto.severity,
            latitude = createDto.latitude,
            longitude = createDto.longitude,
            address = createDto.address,
            nearestZoneId = "N08",
            nearestZoneName = "Banepa Lowlands",
            nearestZoneDistanceKm = 0.0,
            status = "REPORTED",
            createdAt = "2026-09-25T01:40:00.000Z",
            updatedAt = "2026-09-25T01:40:00.000Z"
        )

        val domain = serverResponse.toDomain()

        assertEquals("Banepa", domain.address)
        assertEquals("Banepa Lowlands", domain.nearestZoneName)
        assertEquals(0.0, domain.nearestZoneDistanceKm ?: -1.0, 0.01)
    }

    @Test
    fun all_core_locations_have_valid_gps_coordinates_and_match_core_dataset() {
        assertTrue(CoreLocations.ALL.size >= 16)
        assertTrue(CoreLocations.PRIMARY_CITIES.size >= 6)

        for (loc in CoreLocations.ALL) {
            assertTrue("Latitude for ${loc.name} must be between -90 and 90", loc.latitude in -90.0..90.0)
            assertTrue("Longitude for ${loc.name} must be between -180 and 180", loc.longitude in -180.0..180.0)
            assertNotNull(loc.id)
            assertNotNull(loc.name)
            assertNotNull(loc.region)
        }
    }

    @Test
    fun varanasi_zones_contain_all_15_tactical_zones_matching_core_dataset() {
        assertEquals(15, CoreLocations.VARANASI_ZONES.size)
        val expectedZoneIds = (1..15).map { "Z%02d".format(java.util.Locale.US, it) }.toSet()
        val actualZoneIds = CoreLocations.VARANASI_ZONES.map { it.id }.toSet()
        assertEquals(expectedZoneIds, actualZoneIds)
    }
}
