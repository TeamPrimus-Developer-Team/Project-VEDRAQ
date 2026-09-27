package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.SosStatus
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.net.HttpURLConnection

class SosRepositoryTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var incidentRepository: IncidentRepositoryImpl
    private lateinit var sosRepository: SosRepositoryImpl

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val apiService = NetworkModule.createApiService(
            baseUrl = mockWebServer.url("/").toString()
        )
        incidentRepository = IncidentRepositoryImpl(apiService = apiService)
        sosRepository = SosRepositoryImpl(
            apiService = apiService,
            incidentRepository = incidentRepository
        )
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    @Test
    fun trigger_sos_online_dispatches_critical_incident_to_core() = runBlocking {
        val jsonResponse = """
            {
                "id": "INC-20260925-SOS99",
                "title": "EMERGENCY SOS: Panic Beacon Activated",
                "description": "Panic SOS beacon triggered from field mobile application.",
                "disaster_type": "MEDICAL_EMERGENCY",
                "severity": "CRITICAL",
                "latitude": 25.3150,
                "longitude": 83.0050,
                "status": "REPORTED",
                "created_at": "2026-09-25T12:00:00Z",
                "updated_at": "2026-09-25T12:00:00Z",
                "history": []
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_CREATED)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonResponse)
        )

        val result = sosRepository.triggerSos(
            latitude = 25.3150,
            longitude = 83.0050,
            accuracyMeters = 3.0f,
            notes = "Trapped in flood waters near Dashashwamedh"
        )

        assertTrue(result is Resource.Success)
        val beacon = (result as Resource.Success).data
        assertNotNull(beacon)
        assertEquals(SosStatus.TRANSMITTING, beacon!!.status)

        // Verify request payload sent to Core
        val request = mockWebServer.takeRequest()
        assertEquals("/api/incidents", request.path)
        assertEquals("POST", request.method)
        val body = request.body.readUtf8()
        assertTrue(body.contains("MEDICAL_EMERGENCY"))
        assertTrue(body.contains("CRITICAL"))
        assertTrue(body.contains("VEDRAQ_APP_SOS"))
    }

    @Test
    fun trigger_sos_offline_activates_locally_and_enqueues_in_incident_queue() = runBlocking {
        mockWebServer.shutdown()

        val result = sosRepository.triggerSos(
            latitude = 25.3150,
            longitude = 83.0050,
            accuracyMeters = 5.0f,
            notes = "Offline panic"
        )

        assertTrue(result is Resource.Success)
        val activeBeacon = sosRepository.observeActiveBeacon().first()
        assertNotNull(activeBeacon)
        assertEquals(SosStatus.TRIGGERED, activeBeacon!!.status)

        // Verify it was enqueued in incident offline queue
        val feed = incidentRepository.getLocalIncidents().first()
        val queuedSos = feed.firstOrNull { it.title.contains("SOS", ignoreCase = true) }
        assertNotNull(queuedSos)
        assertEquals(false, queuedSos!!.isSyncedWithCore)
    }

    @Test
    fun cancel_sos_resets_beacon_and_patches_core() = runBlocking {
        // First trigger
        val createJson = """
            {
                "id": "INC-20260925-SOS-CANCEL",
                "title": "EMERGENCY SOS",
                "description": "SOS",
                "disaster_type": "MEDICAL_EMERGENCY",
                "severity": "CRITICAL",
                "latitude": 25.3150,
                "longitude": 83.0050,
                "status": "REPORTED",
                "created_at": "2026-09-25T12:00:00Z",
                "updated_at": "2026-09-25T12:00:00Z",
                "history": []
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_CREATED)
                .setHeader("Content-Type", "application/json")
                .setBody(createJson)
        )

        val triggerResult = sosRepository.triggerSos(25.3150, 83.0050, 3f, "Test")
        val beacon = (triggerResult as Resource.Success).data!!

        // Drain create request
        mockWebServer.takeRequest()

        // Enqueue cancel patch response
        val cancelJson = """
            {
                "id": "INC-20260925-SOS-CANCEL",
                "title": "EMERGENCY SOS",
                "description": "SOS",
                "disaster_type": "MEDICAL_EMERGENCY",
                "severity": "CRITICAL",
                "latitude": 25.3150,
                "longitude": 83.0050,
                "status": "CANCELLED",
                "created_at": "2026-09-25T12:00:00Z",
                "updated_at": "2026-09-25T12:01:00Z",
                "history": []
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_OK)
                .setHeader("Content-Type", "application/json")
                .setBody(cancelJson)
        )

        val cancelResult = sosRepository.cancelSos(beacon.beaconId)
        assertTrue(cancelResult is Resource.Success)

        val active = sosRepository.observeActiveBeacon().first()
        assertNull(active)

        val cancelRequest = mockWebServer.takeRequest()
        assertEquals("/api/incidents/INC-20260925-SOS-CANCEL", cancelRequest.path)
        assertEquals("PATCH", cancelRequest.method)
        val patchBody = cancelRequest.body.readUtf8()
        assertTrue(patchBody.contains("CANCELLED"))
    }
}
