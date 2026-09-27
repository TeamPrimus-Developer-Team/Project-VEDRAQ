package com.vedraq.app.presentation.screens.emergency

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vedraq.app.core.location.LocationClient
import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.CoreLocation
import com.vedraq.app.domain.model.CoreLocations
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
import com.vedraq.app.domain.repository.LocationRepository
import com.vedraq.app.domain.usecase.SubmitIncidentUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.Locale
import java.util.UUID

sealed interface EmergencyReportSubmissionState {
    object Idle : EmergencyReportSubmissionState
    object Submitting : EmergencyReportSubmissionState
    data class SubmittedToCore(val serverIncidentId: String, val incident: Incident) : EmergencyReportSubmissionState
    data class OfflinePending(val localIncidentId: String, val message: String) : EmergencyReportSubmissionState
    data class NetworkError(val message: String) : EmergencyReportSubmissionState
    data class ServerError(val code: Int, val message: String) : EmergencyReportSubmissionState
    data class ValidationError(val field: String, val message: String) : EmergencyReportSubmissionState
}

data class EmergencyReportUiState(
    val title: String = "",
    val description: String = "",
    val disasterType: DisasterType = DisasterType.FLOOD,
    val severity: SeverityLevel = SeverityLevel.HIGH,
    val latitude: Double? = CoreLocations.VARANASI_CENTRAL.latitude,
    val longitude: Double? = CoreLocations.VARANASI_CENTRAL.longitude,
    val selectedCity: String = CoreLocations.VARANASI_CENTRAL.name,
    val address: String = CoreLocations.VARANASI_CENTRAL.name,
    val peopleAffectedEstimate: Int? = null,
    val isGpsAcquired: Boolean = true,
    val isGpsSearching: Boolean = false,
    val locationStatus: String = "Authoritative Location: Varanasi (Central) [25.3150° N, 83.0650° E]",
    val submissionState: EmergencyReportSubmissionState = EmergencyReportSubmissionState.Idle,
    val availableLocations: List<CoreLocation> = CoreLocations.filterByScenario(CoreLocations.ALL, "varanasi"),
    val isCoreOnline: Boolean? = null,
    val isLiveCoreData: Boolean = false
)

class EmergencyReportViewModel(
    private val submitIncidentUseCase: SubmitIncidentUseCase,
    private val locationClient: LocationClient? = null,
    private val locationRepository: LocationRepository? = null
) : ViewModel() {

    private val _uiState = MutableStateFlow(EmergencyReportUiState())
    val uiState: StateFlow<EmergencyReportUiState> = _uiState.asStateFlow()

    init {
        acquireLocation()
        observeLocations()
    }

    private fun observeLocations() {
        if (locationRepository != null) {
            viewModelScope.launch {
                locationRepository.getLocations("varanasi").collect { locations ->
                    _uiState.update { it.copy(availableLocations = locations) }
                }
            }
            viewModelScope.launch {
                locationRepository.observeCoreOnline().collect { online ->
                    _uiState.update { it.copy(isCoreOnline = online) }
                }
            }
            viewModelScope.launch {
                locationRepository.observeIsLiveCoreData().collect { live ->
                    _uiState.update { it.copy(isLiveCoreData = live) }
                }
            }
            viewModelScope.launch {
                locationRepository.refreshLocations("varanasi")
            }
        }
    }

    fun onTitleChange(newTitle: String) {
        _uiState.update { it.copy(title = newTitle, submissionState = EmergencyReportSubmissionState.Idle) }
    }

    fun onDescriptionChange(newDesc: String) {
        _uiState.update { it.copy(description = newDesc) }
    }

    fun onDisasterTypeChange(newType: DisasterType) {
        _uiState.update { it.copy(disasterType = newType) }
    }

    fun onSeverityChange(newSeverity: SeverityLevel) {
        _uiState.update { it.copy(severity = newSeverity) }
    }

    fun onSelectLocation(location: CoreLocation) {
        _uiState.update {
            it.copy(
                latitude = location.latitude,
                longitude = location.longitude,
                selectedCity = location.name,
                address = if (it.address.isBlank() || it.availableLocations.any { cl -> cl.name == it.address }) location.name else it.address,
                isGpsAcquired = true,
                locationStatus = String.format(
                    Locale.US,
                    "Core Location: %s [%.4f° N, %.4f° E]",
                    location.name,
                    location.latitude,
                    location.longitude
                )
            )
        }
    }

    fun onCoordinatesChange(latitude: Double?, longitude: Double?) {
        _uiState.update {
            it.copy(
                latitude = latitude,
                longitude = longitude,
                isGpsAcquired = latitude != null && longitude != null,
                locationStatus = if (latitude != null && longitude != null) {
                    String.format(Locale.US, "Coordinates: %.4f° N, %.4f° E", latitude, longitude)
                } else {
                    "Location not set"
                }
            )
        }
    }

    fun onAddressChange(newAddress: String) {
        _uiState.update { it.copy(address = newAddress) }
    }

    fun onPeopleAffectedChange(estimate: Int?) {
        _uiState.update { it.copy(peopleAffectedEstimate = estimate) }
    }

    fun acquireLocation() {
        if (locationClient == null) {
            // Authoritative scenario default coordinates (Varanasi Central)
            _uiState.update {
                it.copy(
                    latitude = CoreLocations.VARANASI_CENTRAL.latitude,
                    longitude = CoreLocations.VARANASI_CENTRAL.longitude,
                    selectedCity = CoreLocations.VARANASI_CENTRAL.name,
                    isGpsAcquired = true,
                    isGpsSearching = false,
                    locationStatus = "Authoritative Baseline: Varanasi (Central) [25.3150° N, 83.0650° E]"
                )
            }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isGpsSearching = true, locationStatus = "Acquiring GPS fix...") }
            val coords = locationClient.getCurrentLocation()
            if (coords != null) {
                _uiState.update {
                    it.copy(
                        latitude = coords.latitude,
                        longitude = coords.longitude,
                        isGpsAcquired = true,
                        isGpsSearching = false,
                        locationStatus = String.format(Locale.US, "GPS Locked: %.4f° N, %.4f° E (±%.0fm)", coords.latitude, coords.longitude, coords.accuracyMeters ?: 0f)
                    )
                }
            } else {
                _uiState.update {
                    it.copy(
                        isGpsAcquired = false,
                        isGpsSearching = false,
                        locationStatus = "GPS unavailable. Grant permission or enter coordinates."
                    )
                }
            }
        }
    }

    fun submitReport() {
        val state = _uiState.value

        if (state.title.trim().isBlank()) {
            _uiState.update {
                it.copy(
                    submissionState = EmergencyReportSubmissionState.ValidationError(
                        field = "title",
                        message = "Incident title / summary cannot be empty."
                    )
                )
            }
            return
        }

        val lat = state.latitude
        val lon = state.longitude

        if (lat == null || lon == null) {
            _uiState.update {
                it.copy(
                    submissionState = EmergencyReportSubmissionState.ValidationError(
                        field = "location",
                        message = "GPS coordinates unavailable. Please enable location or input manually."
                    )
                )
            }
            return
        }

        if (lat !in -90.0..90.0 || lon !in -180.0..180.0) {
            _uiState.update {
                it.copy(
                    submissionState = EmergencyReportSubmissionState.ValidationError(
                        field = "location",
                        message = "Latitude must be between -90 and 90, longitude between -180 and 180."
                    )
                )
            }
            return
        }

        _uiState.update { it.copy(submissionState = EmergencyReportSubmissionState.Submitting) }

        viewModelScope.launch {
            val clientTrackingId = "CLIENT-${UUID.randomUUID().toString().take(8).uppercase(Locale.US)}"
            val incident = Incident(
                id = clientTrackingId,
                type = state.disasterType,
                severity = state.severity,
                title = state.title.trim(),
                description = state.description.trim().ifEmpty { "Field report transmitted via VEDRAQ mobile unit." },
                latitude = lat,
                longitude = lon,
                address = state.address.trim().ifEmpty { state.selectedCity.ifEmpty { null } },
                status = IncidentStatus.REPORTED,
                peopleAffectedEstimate = state.peopleAffectedEstimate,
                isSyncedWithCore = false
            )

            when (val result = submitIncidentUseCase(incident)) {
                is Resource.Success -> {
                    val synced = result.data
                    if (synced != null && synced.isSyncedWithCore) {
                        _uiState.update {
                            it.copy(
                                submissionState = EmergencyReportSubmissionState.SubmittedToCore(
                                    serverIncidentId = synced.id,
                                    incident = synced
                                )
                            )
                        }
                    } else {
                        _uiState.update {
                            it.copy(
                                submissionState = EmergencyReportSubmissionState.OfflinePending(
                                    localIncidentId = incident.id,
                                    message = "Incident queued locally. Will synchronize once connected."
                                )
                            )
                        }
                    }
                }
                is Resource.Error -> {
                    val errorMsg = result.message ?: "Unknown transmission error"
                    val statusCode = extractStatusCode(errorMsg)
                    if (statusCode != null) {
                        _uiState.update {
                            it.copy(
                                submissionState = EmergencyReportSubmissionState.ServerError(
                                    code = statusCode,
                                    message = errorMsg
                                )
                            )
                        }
                    } else if (errorMsg.contains("Network", ignoreCase = true) ||
                               errorMsg.contains("Connection", ignoreCase = true) ||
                               errorMsg.contains("unreachable", ignoreCase = true)) {
                        _uiState.update {
                            it.copy(
                                submissionState = EmergencyReportSubmissionState.NetworkError(errorMsg)
                            )
                        }
                    } else {
                        _uiState.update {
                            it.copy(
                                submissionState = EmergencyReportSubmissionState.ServerError(
                                    code = 400,
                                    message = errorMsg
                                )
                            )
                        }
                    }
                }
                is Resource.Loading -> {
                    // Handled by Submitting state
                }
                is Resource.Idle -> {
                    // No action needed
                }
            }
        }
    }

    fun resetSubmissionState() {
        _uiState.update { it.copy(submissionState = EmergencyReportSubmissionState.Idle) }
    }

    fun resetForm() {
        _uiState.update {
            EmergencyReportUiState(
                latitude = it.latitude ?: CoreLocations.VARANASI_CENTRAL.latitude,
                longitude = it.longitude ?: CoreLocations.VARANASI_CENTRAL.longitude,
                selectedCity = it.selectedCity,
                address = it.selectedCity,
                isGpsAcquired = it.isGpsAcquired,
                locationStatus = it.locationStatus
            )
        }
    }

    private fun extractStatusCode(message: String): Int? {
        val regex = Regex("""Server error \((\d{3})\)""")
        return regex.find(message)?.groupValues?.get(1)?.toIntOrNull()
    }
}
