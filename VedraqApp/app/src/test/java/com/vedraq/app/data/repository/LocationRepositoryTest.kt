package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.FacilityType
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.net.HttpURLConnection

class LocationRepositoryTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var repository: LocationRepositoryImpl

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val apiService = NetworkModule.createApiService(
            baseUrl = mockWebServer.url("/").toString()
        )
        repository = LocationRepositoryImpl(apiService = apiService)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    @Test
    fun getLocations_varanasi_filters_out_nepal_and_returns_only_varanasi_locations() = runBlocking {
        val locationsJson = """
            {
                "locations": [
                    {
                        "id": "varanasi_center",
                        "name": "Varanasi District Flood (Central)",
                        "city": "Varanasi",
                        "region": "Uttar Pradesh, India",
                        "latitude": 25.3150,
                        "longitude": 83.0650,
                        "type": "SCENARIO_CENTER",
                        "scenario_id": "varanasi"
                    },
                    {
                        "id": "nepal_center",
                        "name": "Nepal Alpine Disaster (Central)",
                        "city": "Nepal",
                        "region": "Bagmati & Sindhupalchok, Nepal",
                        "latitude": 27.7500,
                        "longitude": 85.5500,
                        "type": "SCENARIO_CENTER",
                        "scenario_id": "nepal"
                    },
                    {
                        "id": "Z01",
                        "name": "Rampur Tanda",
                        "city": "Varanasi",
                        "region": "Uttar Pradesh, India",
                        "latitude": 25.3120,
                        "longitude": 83.0120,
                        "type": "TACTICAL_ZONE"
                    },
                    {
                        "id": "Z02",
                        "name": "Chandpur",
                        "city": "Varanasi",
                        "region": "Uttar Pradesh, India",
                        "latitude": 25.3580,
                        "longitude": 83.0740,
                        "type": "TACTICAL_ZONE"
                    },
                    {
                        "id": "N07",
                        "name": "Dhulikhel Gateway",
                        "city": "Nepal",
                        "region": "Bagmati & Sindhupalchok, Nepal",
                        "latitude": 27.6180,
                        "longitude": 85.5540,
                        "type": "TACTICAL_ZONE"
                    }
                ],
                "total": 5
            }
        """.trimIndent()

        val zonesJson = """
            {
                "zones": [
                    {
                        "id": "Z01",
                        "name": "Rampur Tanda",
                        "latitude": 25.3120,
                        "longitude": 83.0120,
                        "population": 4200,
                        "affected_population": 3800,
                        "damage_percentage": 62,
                        "classification": "CRITICAL",
                        "road_accessibility": "blocked"
                    },
                    {
                        "id": "Z02",
                        "name": "Chandpur",
                        "latitude": 25.3580,
                        "longitude": 83.0740,
                        "population": 8000,
                        "affected_population": 5600,
                        "damage_percentage": 70,
                        "classification": "HIGH",
                        "road_accessibility": "open"
                    }
                ],
                "total": 2
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_OK)
                .setHeader("Content-Type", "application/json")
                .setBody(locationsJson)
        )

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_OK)
                .setHeader("Content-Type", "application/json")
                .setBody(zonesJson)
        )

        val result = repository.refreshLocations("varanasi")
        assertTrue(result is Resource.Success)

        val varanasiLocations = repository.getLocations("varanasi").first()
        assertFalse(varanasiLocations.isEmpty())

        // 1. Must contain Varanasi Center and Varanasi Tactical Zones
        assertTrue(varanasiLocations.any { it.id == "varanasi_center" })
        assertTrue(varanasiLocations.any { it.id == "Z01" })
        assertTrue(varanasiLocations.any { it.id == "Z02" })

        // 2. Strict scenario isolation: MUST NOT contain any Nepal locations
        assertFalse(varanasiLocations.any { it.id == "nepal_center" })
        assertFalse(varanasiLocations.any { it.id == "N07" })
        assertFalse(varanasiLocations.any { it.region.contains("Nepal") })

        // 3. Verify enrichment with zone metrics
        val z1 = varanasiLocations.first { it.id == "Z01" }
        assertEquals(62, z1.damagePercentage)
        assertEquals("CRITICAL", z1.classification)
        assertEquals("blocked", z1.roadAccessibility)

        // 4. Verify connectivity status
        assertEquals(true, repository.observeCoreOnline().value)
        assertTrue(repository.observeIsLiveCoreData().value)
    }

    @Test
    fun refreshFacilities_parses_hospitals_and_shelters_correctly() = runBlocking {
        val facilitiesJson = """
            {
                "hospitals": [
                    {
                        "id": "H1",
                        "name": "District Hospital Varanasi",
                        "latitude": 25.358,
                        "longitude": 83.074,
                        "status": "functional",
                        "capacity": 200,
                        "zone_id": "Z02",
                        "available_beds": 142,
                        "specialization": "General, Emergency, Surgical"
                    }
                ],
                "shelters": [
                    {
                        "id": "S1",
                        "name": "Govt School Chandpur",
                        "latitude": 25.355,
                        "longitude": 83.072,
                        "capacity": 2500,
                        "current_occupancy": 1200,
                        "status": "open",
                        "food_stock_days": 5,
                        "water_supply": "functional"
                    }
                ],
                "depots": [
                    {
                        "id": "DEPOT",
                        "name": "NDRF Resource Depot 01",
                        "latitude": 25.332,
                        "longitude": 83.025,
                        "capacity": 500
                    }
                ]
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_OK)
                .setHeader("Content-Type", "application/json")
                .setBody(facilitiesJson)
        )

        val result = repository.refreshFacilities()
        assertTrue(result is Resource.Success)

        val facilities = repository.getFacilities().first()
        assertEquals(3, facilities.size)

        val hospital = facilities.first { it.type == FacilityType.HOSPITAL }
        assertEquals("H1", hospital.id)
        assertEquals("District Hospital Varanasi", hospital.name)
        assertEquals(142, hospital.availableBeds)

        val shelter = facilities.first { it.type == FacilityType.SHELTER }
        assertEquals("S1", shelter.id)
        assertEquals("Govt School Chandpur", shelter.name)
        assertEquals(2500, shelter.capacity)
        assertEquals(1200, shelter.currentOccupancy)
        assertEquals(48, shelter.occupancyPercentage)
    }

    @Test
    fun offline_fallback_preserves_baseline_and_marks_offline() = runBlocking {
        // Shutdown server to simulate network unreachable
        mockWebServer.shutdown()

        val result = repository.refreshLocations("varanasi")
        assertTrue(result is Resource.Error)

        // Offline status must be clearly marked
        assertEquals(false, repository.observeCoreOnline().value)
        assertFalse(repository.observeIsLiveCoreData().value)

        // Baseline locations must still be available (never empty/crash)
        val fallbackLocations = repository.getLocations("varanasi").first()
        assertTrue(fallbackLocations.isNotEmpty())
        assertTrue(fallbackLocations.any { it.id == "Z01" })
        assertTrue(fallbackLocations.any { it.id == "Z15" })
    }
}
