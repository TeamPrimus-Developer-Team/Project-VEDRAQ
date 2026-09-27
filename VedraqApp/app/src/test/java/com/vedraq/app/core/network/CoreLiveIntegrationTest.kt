package com.vedraq.app.core.network

import com.vedraq.app.core.util.Resource
import com.vedraq.app.data.remote.dto.IncidentCreateRequestDto
import com.vedraq.app.data.repository.LocationRepositoryImpl
import com.vedraq.app.domain.model.CoreLocations
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Test
import java.net.Socket

class CoreLiveIntegrationTest {

    private val liveBaseUrl = "http://127.0.0.1:8001/"
    private var isCoreLive = false

    @Before
    fun checkIfCoreRunning() {
        isCoreLive = try {
            Socket("127.0.0.1", 8001).use { true }
        } catch (_: Exception) {
            false
        }
    }

    @Test
    fun live_core_health_check_returns_ok() = runBlocking {
        assumeTrue("VEDRAQ Core is running on port 8001", isCoreLive)

        val apiService = NetworkModule.createApiService(baseUrl = liveBaseUrl)
        val response = apiService.checkHealth()

        assertTrue(response.isSuccessful)
        val body = response.body()
        assertNotNull(body)
        assertEquals("ok", body!!["status"])
        assertEquals("VEDRAQ", body["service"])
    }

    @Test
    fun live_core_locations_returns_15_varanasi_zones_without_nepal() = runBlocking {
        assumeTrue("VEDRAQ Core is running on port 8001", isCoreLive)

        val apiService = NetworkModule.createApiService(baseUrl = liveBaseUrl)
        val repository = LocationRepositoryImpl(apiService = apiService)

        val result = repository.refreshLocations("varanasi")
        assertTrue(result is Resource.Success)

        val varanasiLocations = repository.getLocations("varanasi").first()

        // Verify all 15 Varanasi zones are present
        val zoneIds = varanasiLocations.filter { it.id.startsWith("Z") }.map { it.id }.toSet()
        assertEquals(15, zoneIds.size)
        for (i in 1..15) {
            val expectedId = "Z%02d".format(java.util.Locale.US, i)
            assertTrue("Zone $expectedId must be present in Varanasi locations", zoneIds.contains(expectedId))
        }

        // Verify scenario isolation: no Nepal zones present
        assertFalse(varanasiLocations.any { it.id.startsWith("N") })
        assertFalse(varanasiLocations.any { it.region.contains("Nepal") })

        // Verify connectivity state is marked online and live
        assertEquals(true, repository.observeCoreOnline().value)
        assertTrue(repository.observeIsLiveCoreData().value)
    }

    @Test
    fun live_core_facilities_returns_authoritative_hospitals_and_shelters() = runBlocking {
        assumeTrue("VEDRAQ Core is running on port 8001", isCoreLive)

        val apiService = NetworkModule.createApiService(baseUrl = liveBaseUrl)
        val repository = LocationRepositoryImpl(apiService = apiService)

        val result = repository.refreshFacilities()
        assertTrue(result is Resource.Success)

        val facilities = repository.getFacilities().first()
        assertTrue(facilities.any { it.name.contains("District Hospital Varanasi") })
        assertTrue(facilities.any { it.name.contains("Govt School Chandpur") })
    }

    @Test
    fun live_core_incident_creation_returns_authoritative_id_and_nearest_zone() = runBlocking {
        assumeTrue("VEDRAQ Core is running on port 8001", isCoreLive)

        val apiService = NetworkModule.createApiService(baseUrl = liveBaseUrl)
        val request = IncidentCreateRequestDto(
            title = "Live Test Flood Report",
            description = "Observation near Assi Ghat corridor",
            disasterType = "FLOOD",
            severity = "CRITICAL",
            latitude = 25.2950,
            longitude = 83.0130,
            address = "Assi Ghat Colony",
            source = "VEDRAQ_APP"
        )

        val response = apiService.createIncident(request)
        assertTrue(response.isSuccessful)
        val body = response.body()
        assertNotNull(body)
        assertTrue(body!!.id.startsWith("INC-"))
        assertEquals("Z15", body.nearestZoneId)
        assertEquals("Assi Ghat Colony", body.nearestZoneName)
    }
}
