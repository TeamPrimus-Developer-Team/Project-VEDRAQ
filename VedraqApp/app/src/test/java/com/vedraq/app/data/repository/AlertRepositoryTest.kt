package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.SeverityLevel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.net.HttpURLConnection

class AlertRepositoryTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var alertRepository: AlertRepositoryImpl

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val apiService = NetworkModule.createApiService(
            baseUrl = mockWebServer.url("/").toString()
        )
        alertRepository = AlertRepositoryImpl(apiService = apiService)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    @Test
    fun refresh_alerts_success_fetches_from_core_and_updates_flow() = runBlocking {
        val jsonResponse = """
            {
                "incidents": [
                    {
                        "id": "INC-20260925-VAR01",
                        "title": "Severe Embankment Flood",
                        "description": "Ganga water overtopping riverbank by 1.5m",
                        "disaster_type": "FLOOD",
                        "severity": "CRITICAL",
                        "latitude": 25.3060,
                        "longitude": 83.0100,
                        "address": "Dashashwamedh Ghat",
                        "nearest_zone_name": "Assi Ghat Colony",
                        "nearest_zone_distance_km": 1.2,
                        "status": "IN_PROGRESS",
                        "created_at": "2026-09-25T12:00:00Z",
                        "updated_at": "2026-09-25T12:00:00Z",
                        "history": []
                    }
                ],
                "total": 1
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_OK)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonResponse)
        )

        val result = alertRepository.refreshAlerts()

        assertTrue(result is Resource.Success)
        val alerts = alertRepository.getActiveAlerts().first()
        val coreAlert = alerts.firstOrNull { it.id == "alert-INC-20260925-VAR01" }

        assertNotNull(coreAlert)
        assertEquals("Severe Embankment Flood", coreAlert!!.title)
        assertEquals(DisasterType.FLOOD, coreAlert.disasterType)
        assertEquals(SeverityLevel.CRITICAL, coreAlert.severity)
        assertTrue(coreAlert.isEvacuationMandatory)
        assertEquals("Assi Ghat Colony", coreAlert.affectedRegion)

        val request = mockWebServer.takeRequest()
        assertEquals("/api/incidents", request.path)
        assertEquals("GET", request.method)
    }

    @Test
    fun refresh_alerts_offline_gracefully_preserves_cached_alerts() = runBlocking {
        mockWebServer.shutdown()

        val result = alertRepository.refreshAlerts()

        assertTrue(result is Resource.Error)
        val currentAlerts = alertRepository.getActiveAlerts().first()
        assertTrue(currentAlerts.isNotEmpty())
    }
}
