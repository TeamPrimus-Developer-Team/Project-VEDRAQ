package com.vedraq.app.presentation.screens.emergency

import com.vedraq.app.core.location.LocationClient
import com.vedraq.app.core.location.LocationCoordinates
import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
import com.vedraq.app.domain.repository.IncidentRepository
import com.vedraq.app.domain.usecase.SubmitIncidentUseCase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class EmergencyReportViewModelTest {

    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private class FakeIncidentRepository(
        var submitResult: Resource<Incident> = Resource.Success(
            Incident(
                id = "INC-SERVER-AUTHORITATIVE",
                type = DisasterType.FLOOD,
                severity = SeverityLevel.CRITICAL,
                title = "Flood",
                description = "Desc",
                latitude = 25.305,
                longitude = 83.010,
                isSyncedWithCore = true
            )
        )
    ) : IncidentRepository {
        var lastSubmittedIncident: Incident? = null

        override fun getLocalIncidents(): Flow<List<Incident>> = emptyFlow()

        override suspend fun submitIncident(incident: Incident): Resource<Incident> {
            lastSubmittedIncident = incident
            return submitResult
        }

        override suspend fun syncPendingIncidents(): Resource<Int> = Resource.Success(0)
        override suspend fun getIncidentById(id: String): Incident? = null
        override suspend fun fetchIncidentsFromCore(): Resource<List<Incident>> = Resource.Success(emptyList())
        override suspend fun resolveIncident(incidentId: String, note: String?): Resource<Incident> = submitResult
    }

    private class FakeLocationClient(
        var location: LocationCoordinates? = LocationCoordinates(25.3050, 83.0100, 5f)
    ) : LocationClient {
        override fun getLocationUpdates(intervalMs: Long): Flow<LocationCoordinates> = emptyFlow()
        override suspend fun getCurrentLocation(): LocationCoordinates? = location
    }

    @Test
    fun initial_state_acquires_location_and_starts_idle() = runTest {
        val fakeRepo = FakeIncidentRepository()
        val fakeLocation = FakeLocationClient()
        val viewModel = EmergencyReportViewModel(
            submitIncidentUseCase = SubmitIncidentUseCase(fakeRepo),
            locationClient = fakeLocation
        )

        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(EmergencyReportSubmissionState.Idle, state.submissionState)
        assertTrue(state.isGpsAcquired)
        assertEquals(25.3050, state.latitude!!, 0.0001)
        assertEquals(83.0100, state.longitude!!, 0.0001)
    }

    @Test
    fun validation_error_when_title_is_blank() = runTest {
        val fakeRepo = FakeIncidentRepository()
        val fakeLocation = FakeLocationClient()
        val viewModel = EmergencyReportViewModel(
            submitIncidentUseCase = SubmitIncidentUseCase(fakeRepo),
            locationClient = fakeLocation
        )
        advanceUntilIdle()

        viewModel.onTitleChange("   ")
        viewModel.submitReport()

        val state = viewModel.uiState.value
        assertTrue(state.submissionState is EmergencyReportSubmissionState.ValidationError)
        val validation = state.submissionState as EmergencyReportSubmissionState.ValidationError
        assertEquals("title", validation.field)
    }

    @Test
    fun validation_error_when_coordinates_out_of_bounds() = runTest {
        val fakeRepo = FakeIncidentRepository()
        val fakeLocation = FakeLocationClient()
        val viewModel = EmergencyReportViewModel(
            submitIncidentUseCase = SubmitIncidentUseCase(fakeRepo),
            locationClient = fakeLocation
        )
        advanceUntilIdle()

        viewModel.onTitleChange("Valid Title")
        viewModel.onCoordinatesChange(195.0, 83.0) // Invalid lat > 90
        viewModel.submitReport()

        val state = viewModel.uiState.value
        assertTrue(state.submissionState is EmergencyReportSubmissionState.ValidationError)
        val validation = state.submissionState as EmergencyReportSubmissionState.ValidationError
        assertEquals("location", validation.field)
    }

    @Test
    fun successful_submission_transitions_to_submitted_to_core_with_authoritative_id() = runTest {
        val expectedServerIncident = Incident(
            id = "INC-20260923-AUTH01",
            type = DisasterType.EARTHQUAKE,
            severity = SeverityLevel.CRITICAL,
            title = "Major Quake",
            description = "Fissures across main highway",
            latitude = 25.305,
            longitude = 83.010,
            status = IncidentStatus.REPORTED,
            isSyncedWithCore = true
        )
        val fakeRepo = FakeIncidentRepository(submitResult = Resource.Success(expectedServerIncident))
        val fakeLocation = FakeLocationClient()

        val viewModel = EmergencyReportViewModel(
            submitIncidentUseCase = SubmitIncidentUseCase(fakeRepo),
            locationClient = fakeLocation
        )
        advanceUntilIdle()

        viewModel.onTitleChange("Major Quake")
        viewModel.onDescriptionChange("Fissures across main highway")
        viewModel.onDisasterTypeChange(DisasterType.EARTHQUAKE)
        viewModel.onSeverityChange(SeverityLevel.CRITICAL)

        viewModel.submitReport()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertTrue(state.submissionState is EmergencyReportSubmissionState.SubmittedToCore)
        val submitted = state.submissionState as EmergencyReportSubmissionState.SubmittedToCore
        assertEquals("INC-20260923-AUTH01", submitted.serverIncidentId)
        assertEquals("Major Quake", submitted.incident.title)
    }

    @Test
    fun network_failure_transitions_to_network_error_state() = runTest {
        val fakeRepo = FakeIncidentRepository(
            submitResult = Resource.Error("Network unreachable: failed to connect to /10.0.2.2:8000. Queued locally.")
        )
        val fakeLocation = FakeLocationClient()

        val viewModel = EmergencyReportViewModel(
            submitIncidentUseCase = SubmitIncidentUseCase(fakeRepo),
            locationClient = fakeLocation
        )
        advanceUntilIdle()

        viewModel.onTitleChange("Flash Flood")
        viewModel.submitReport()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertTrue(state.submissionState is EmergencyReportSubmissionState.NetworkError)
    }

    @Test
    fun server_error_transitions_to_server_error_state_with_code() = runTest {
        val fakeRepo = FakeIncidentRepository(
            submitResult = Resource.Error("Server error (422): Input validation failed")
        )
        val fakeLocation = FakeLocationClient()

        val viewModel = EmergencyReportViewModel(
            submitIncidentUseCase = SubmitIncidentUseCase(fakeRepo),
            locationClient = fakeLocation
        )
        advanceUntilIdle()

        viewModel.onTitleChange("Chemical Spill")
        viewModel.submitReport()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertTrue(state.submissionState is EmergencyReportSubmissionState.ServerError)
        val serverError = state.submissionState as EmergencyReportSubmissionState.ServerError
        assertEquals(422, serverError.code)
    }

    @Test
    fun select_location_varanasi_updates_coordinates_and_status() = runTest {
        val fakeRepo = FakeIncidentRepository()
        val viewModel = EmergencyReportViewModel(SubmitIncidentUseCase(fakeRepo))
        advanceUntilIdle()

        viewModel.onSelectLocation(com.vedraq.app.domain.model.CoreLocations.VARANASI_CENTRAL)

        val state = viewModel.uiState.value
        assertEquals("Varanasi (Central)", state.selectedCity)
        assertEquals(25.3150, state.latitude!!, 0.0001)
        assertEquals(83.0650, state.longitude!!, 0.0001)
        assertTrue(state.locationStatus.contains("Varanasi (Central)"))
    }

    @Test
    fun select_location_dhulikhel_nepal_updates_coordinates_and_submits_unchanged() = runTest {
        val fakeRepo = FakeIncidentRepository()
        val viewModel = EmergencyReportViewModel(SubmitIncidentUseCase(fakeRepo))
        advanceUntilIdle()

        viewModel.onSelectLocation(com.vedraq.app.domain.model.CoreLocations.DHULIKHEL)
        viewModel.onTitleChange("Road Cutoff in Dhulikhel")
        viewModel.submitReport()
        advanceUntilIdle()

        val submitted = fakeRepo.lastSubmittedIncident
        org.junit.Assert.assertNotNull(submitted)
        // Verify coordinates sent to Core match Core Dhulikhel dataset exactly
        assertEquals(27.6180, submitted!!.latitude, 0.0001)
        assertEquals(85.5540, submitted.longitude, 0.0001)
        assertEquals("Dhulikhel", submitted.address)
    }

    @Test
    fun select_location_banepa_nepal_updates_coordinates_and_submits_unchanged() = runTest {
        val fakeRepo = FakeIncidentRepository()
        val viewModel = EmergencyReportViewModel(SubmitIncidentUseCase(fakeRepo))
        advanceUntilIdle()

        viewModel.onSelectLocation(com.vedraq.app.domain.model.CoreLocations.BANEPA)
        viewModel.onTitleChange("Flash Flood in Market")
        viewModel.submitReport()
        advanceUntilIdle()

        val submitted = fakeRepo.lastSubmittedIncident
        org.junit.Assert.assertNotNull(submitted)
        // Verify coordinates sent to Core match Core Banepa dataset exactly
        assertEquals(27.6320, submitted!!.latitude, 0.0001)
        assertEquals(85.5240, submitted.longitude, 0.0001)
        assertEquals("Banepa", submitted.address)
    }
}
