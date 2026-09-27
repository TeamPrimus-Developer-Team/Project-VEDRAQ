package com.vedraq.app.presentation.screens.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vedraq.app.core.location.LocationClient
import com.vedraq.app.domain.model.CoreLocation
import com.vedraq.app.domain.model.CoreLocations
import com.vedraq.app.domain.model.FacilityType
import com.vedraq.app.domain.model.TacticalFacility
import com.vedraq.app.domain.repository.LocationRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

data class MapUiState(
    val zones: List<CoreLocation> = emptyList(),
    val facilities: List<TacticalFacility> = emptyList(),
    val isCoreOnline: Boolean? = null,
    val isLiveCoreData: Boolean = false,
    val isLoading: Boolean = false,
    val showHazards: Boolean = true,
    val showShelters: Boolean = true,
    val showHospitals: Boolean = true,
    val selectedFacility: TacticalFacility? = null,
    val selectedZone: CoreLocation? = null,
    val userLatitude: Double = CoreLocations.VARANASI_CENTRAL.latitude,
    val userLongitude: Double = CoreLocations.VARANASI_CENTRAL.longitude
) {
    /**
     * Finds nearest evacuation shelter dynamically from Core-provided facilities.
     */
    val nearestShelter: TacticalFacility?
        get() {
            val shelters = facilities.filter { it.type == FacilityType.SHELTER }
            if (shelters.isEmpty()) return null
            return shelters.minByOrNull { s ->
                haversineDistanceKm(userLatitude, userLongitude, s.latitude, s.longitude)
            }
        }

    val nearestShelterDistanceKm: Double?
        get() {
            val shelter = nearestShelter ?: return null
            return haversineDistanceKm(userLatitude, userLongitude, shelter.latitude, shelter.longitude)
        }
}

private fun haversineDistanceKm(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
    val r = 6371.0
    val dLat = Math.toRadians(lat2 - lat1)
    val dLon = Math.toRadians(lon2 - lon1)
    val a = sin(dLat / 2) * sin(dLat / 2) +
            cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) *
            sin(dLon / 2) * sin(dLon / 2)
    val c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c
}

class MapViewModel(
    private val locationRepository: LocationRepository,
    private val locationClient: LocationClient? = null
) : ViewModel() {

    private val _uiState = MutableStateFlow(MapUiState())
    val uiState: StateFlow<MapUiState> = _uiState.asStateFlow()

    init {
        acquireUserLocation()
        observeCoreData()
    }

    private fun observeCoreData() {
        viewModelScope.launch {
            locationRepository.getLocations("varanasi").collect { locations ->
                val tacticalZones = locations.filter { it.id.startsWith("Z") }
                _uiState.update { it.copy(zones = tacticalZones) }
            }
        }

        viewModelScope.launch {
            locationRepository.getFacilities().collect { facs ->
                _uiState.update { it.copy(facilities = facs) }
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

        refreshData()
    }

    fun refreshData() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            locationRepository.refreshLocations("varanasi")
            locationRepository.refreshFacilities()
            _uiState.update { it.copy(isLoading = false) }
        }
    }

    fun toggleHazards() {
        _uiState.update { it.copy(showHazards = !it.showHazards) }
    }

    fun toggleShelters() {
        _uiState.update { it.copy(showShelters = !it.showShelters) }
    }

    fun toggleHospitals() {
        _uiState.update { it.copy(showHospitals = !it.showHospitals) }
    }

    fun selectFacility(facility: TacticalFacility) {
        _uiState.update { it.copy(selectedFacility = facility, selectedZone = null) }
    }

    fun selectZone(zone: CoreLocation) {
        _uiState.update { it.copy(selectedZone = zone, selectedFacility = null) }
    }

    fun clearSelection() {
        _uiState.update { it.copy(selectedFacility = null, selectedZone = null) }
    }

    fun acquireUserLocation() {
        if (locationClient == null) return
        viewModelScope.launch {
            val coords = locationClient.getCurrentLocation()
            if (coords != null) {
                _uiState.update {
                    it.copy(
                        userLatitude = coords.latitude,
                        userLongitude = coords.longitude
                    )
                }
            }
        }
    }
}
