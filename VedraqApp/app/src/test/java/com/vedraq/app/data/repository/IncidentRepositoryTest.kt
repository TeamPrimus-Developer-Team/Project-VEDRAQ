package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
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

class IncidentRepositoryTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var repository: IncidentRepositoryImpl

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val apiService = NetworkModule.createApiService(
            baseUrl = mockWebServer.url("/").toString()
        )
        repository = IncidentRepositoryImpl(apiService = apiService)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    @Test
    fun submit_incident_success_201_receives_server_authoritative_id_and_updates_feed() = runBlocking {
        val jsonResponse = """
            {
                "id": "INC-20260923-TEST99",
                "title": "Submerged Crossing",
                "description": "Culvert blocked by debris",
                "disaster_type": "FLOOD",
                "severity": "CRITICAL",
                "latitude": 25.305,
                "longitude": 83.010,
                "address": "South Crossing",
                "reporter_id": "FIELD-01",
                "people_affected_estimate": 40,
                "status": "REPORTED",
                "client_incident_id": "CLIENT-LOCAL-1",
                "source": "VEDRAQ_APP",
                "created_at": "2026-09-23T18:00:00.000Z",
                "updated_at": "2026-09-23T18:00:00.000Z",
                "history": []
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_CREATED)
                .setHeader("Content-Type", "application/json")
                .setBody(jsonResponse)
        )

        val localIncident = Incident(
            id = "CLIENT-LOCAL-1",
            type = DisasterType.FLOOD,
            severity = SeverityLevel.CRITICAL,
            title = "Submerged Crossing",
            description = "Culvert blocked by debris",
            latitude = 25.305,
            longitude = 83.010,
            address = "South Crossing",
            status = IncidentStatus.REPORTED,
            isSyncedWithCore = false
        )

        val result = repository.submitIncident(localIncident)

        assertTrue(result is Resource.Success)
        val data = (result as Resource.Success).data
        assertNotNull(data)
        assertEquals("INC-20260923-TEST99", data!!.id)
        assertTrue(data.isSyncedWithCore)

        // Verify request payload sent to Core
        val recordedRequest = mockWebServer.takeRequest()
        assertEquals("/api/incidents", recordedRequest.path)
        assertEquals("POST", recordedRequest.method)
        val requestBody = recordedRequest.body.readUtf8()
        assertTrue(requestBody.contains("Submerged Crossing"))
        assertTrue(requestBody.contains("FLOOD"))
        assertTrue(requestBody.contains("CRITICAL"))
        assertTrue(requestBody.contains("VEDRAQ_APP"))

        // Verify local feed contains authoritative incident at head
        val localFeed = repository.getLocalIncidents().first()
        val firstInFeed = localFeed.first()
        assertEquals("INC-20260923-TEST99", firstInFeed.id)
        assertTrue(firstInFeed.isSyncedWithCore)
    }

    @Test
    fun submit_incident_server_error_422_returns_error_resource() = runBlocking {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(422)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"detail":[{"loc":["body","latitude"],"msg":"Input should be greater than or equal to -90"}]}""")
        )

        val invalidIncident = Incident(
            id = "CLIENT-BAD",
            type = DisasterType.FLOOD,
            severity = SeverityLevel.HIGH,
            title = "Bad Coordinates",
            description = "Description",
            latitude = -150.0,
            longitude = 83.010,
            isSyncedWithCore = false
        )

        val result = repository.submitIncident(invalidIncident)

        assertTrue(result is Resource.Error)
        val errorMsg = (result as Resource.Error).message ?: ""
        assertTrue(errorMsg.contains("422"))
    }

    @Test
    fun submit_incident_offline_network_failure_queues_locally() = runBlocking {
        // Shut down server to simulate unreachable host
        mockWebServer.shutdown()

        val offlineIncident = Incident(
            id = "CLIENT-OFFLINE-77",
            type = DisasterType.EARTHQUAKE,
            severity = SeverityLevel.HIGH,
            title = "Tremors in District",
            description = "Minor fissures observed",
            latitude = 25.305,
            longitude = 83.010,
            isSyncedWithCore = false
        )

        val result = repository.submitIncident(offlineIncident)

        assertTrue(result is Resource.Error)
        val errorMsg = (result as Resource.Error).message ?: ""
        assertTrue(errorMsg.contains("Network unreachable"))

        // Verify incident was saved in local offline queue
        val feed = repository.getLocalIncidents().first()
        val saved = feed.firstOrNull { it.id == "CLIENT-OFFLINE-77" }
        assertNotNull(saved)
        assertFalse(saved!!.isSyncedWithCore)
    }

    @Test
    fun fetch_incidents_from_core_merges_with_local_state() = runBlocking {
        val listJson = """
            {
                "incidents": [
                    {
                        "id": "INC-20260923-CORE01",
                        "title": "Industrial Gas Leak",
                        "description": "Ammonia tank rupture",
                        "disaster_type": "HAZMAT",
                        "severity": "CRITICAL",
                        "latitude": 25.312,
                        "longitude": 83.018,
                        "status": "IN_PROGRESS",
                        "created_at": "2026-09-23T17:30:00.000Z",
                        "updated_at": "2026-09-23T17:30:00.000Z",
                        "history": []
                    }
                ],
                "total": 1
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(listJson)
        )

        val result = repository.fetchIncidentsFromCore()

        assertTrue(result is Resource.Success)
        val remoteIncidents = (result as Resource.Success).data ?: emptyList()
        assertEquals(1, remoteIncidents.size)
        assertEquals("INC-20260923-CORE01", remoteIncidents[0].id)
        assertEquals(DisasterType.HAZMAT, remoteIncidents[0].type)
        assertEquals(IncidentStatus.RESPONDING, remoteIncidents[0].status)

        // Verify local feed contains this remote incident
        val localFeed = repository.getLocalIncidents().first()
        val found = localFeed.firstOrNull { it.id == "INC-20260923-CORE01" }
        assertNotNull(found)
    }

    @Test
    fun resolve_incident_patches_core_and_updates_local_status() = runBlocking {
        val patchResponseJson = """
            {
                "id": "INC-20260925-RESOLVE01",
                "title": "Submerged Culvert",
                "description": "Drain cleared",
                "disaster_type": "FLOOD",
                "severity": "LOW",
                "latitude": 25.305,
                "longitude": 83.010,
                "status": "RESOLVED",
                "created_at": "2026-09-25T10:00:00Z",
                "updated_at": "2026-09-25T11:30:00Z",
                "history": []
            }
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(HttpURLConnection.HTTP_OK)
                .setHeader("Content-Type", "application/json")
                .setBody(patchResponseJson)
        )

        val result = repository.resolveIncident(
            incidentId = "INC-20260925-RESOLVE01",
            note = "Flood water receded, verified safe"
        )

        assertTrue(result is Resource.Success)
        val resolved = (result as Resource.Success).data
        assertNotNull(resolved)
        assertEquals(IncidentStatus.RESOLVED, resolved!!.status)
        assertTrue(resolved.isSyncedWithCore)

        val recordedRequest = mockWebServer.takeRequest()
        assertEquals("/api/incidents/INC-20260925-RESOLVE01", recordedRequest.path)
        assertEquals("PATCH", recordedRequest.method)
        val requestBody = recordedRequest.body.readUtf8()
        assertTrue(requestBody.contains("RESOLVED"))
        assertTrue(requestBody.contains("Flood water receded, verified safe"))
    }
}

