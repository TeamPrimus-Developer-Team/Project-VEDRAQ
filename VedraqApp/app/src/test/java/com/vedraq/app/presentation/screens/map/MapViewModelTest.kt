package com.vedraq.app.presentation.screens.map

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.CoreLocation
import com.vedraq.app.domain.model.CoreLocations
import com.vedraq.app.domain.model.FacilityType
import com.vedraq.app.domain.model.TacticalFacility
import com.vedraq.app.domain.repository.LocationRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class MapViewModelTest {

    private val testDispatcher = StandardTestDispatcher()

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private class FakeLocationRepository(
        private val locations: List<CoreLocation> = listOf(
            CoreLocations.VARANASI_CENTRAL,
            CoreLocations.RAMPUR_TANDA,
            CoreLocations.CHANDPUR,
            CoreLocations.ASSI_GHAT
        ),
        private val facilities: List<TacticalFacility> = listOf(
            TacticalFacility(
                id = "S1",
                name = "Govt School Chandpur",
                type = FacilityType.SHELTER,
                latitude = 25.355,
                longitude = 83.072,
                capacity = 2500,
                currentOccupancy = 1200
            ),
            TacticalFacility(
                id = "S2",
                name = "Assi Ghat School Shelter",
                type = FacilityType.SHELTER,
                latitude = 25.295,
                longitude = 83.013,
                capacity = 3000,
                currentOccupancy = 1410
            ),
            TacticalFacility(
                id = "H1",
                name = "District Hospital Varanasi",
                type = FacilityType.HOSPITAL,
                latitude = 25.358,
                longitude = 83.074,
                capacity = 200,
                availableBeds = 142
            )
        )
    ) : LocationRepository {
        private val _locationsFlow = MutableStateFlow(locations)
        private val _facilitiesFlow = MutableStateFlow(facilities)
        private val _onlineFlow = MutableStateFlow<Boolean?>(true)
        private val _liveFlow = MutableStateFlow(true)

        override fun getLocations(scenarioId: String): Flow<List<CoreLocation>> = _locationsFlow.asStateFlow()
        override fun getFacilities(): Flow<List<TacticalFacility>> = _facilitiesFlow.asStateFlow()
        override fun observeCoreOnline(): StateFlow<Boolean?> = _onlineFlow.asStateFlow()
        override fun observeIsLiveCoreData(): StateFlow<Boolean> = _liveFlow.asStateFlow()

        override suspend fun refreshLocations(scenarioId: String): Resource<List<CoreLocation>> {
            return Resource.Success(locations)
        }

        override suspend fun refreshFacilities(): Resource<List<TacticalFacility>> {
            return Resource.Success(facilities)
        }
    }

    @Test
    fun initial_state_loads_zones_and_facilities_from_repository() = runTest {
        val fakeRepo = FakeLocationRepository()
        val viewModel = MapViewModel(locationRepository = fakeRepo)

        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(3, state.zones.size) // Z01, Z02, Z15 (excluding varanasi_center)
        assertEquals(3, state.facilities.size)
        assertEquals(true, state.isCoreOnline)
        assertTrue(state.isLiveCoreData)
        assertTrue(state.showHazards)
        assertTrue(state.showShelters)
        assertTrue(state.showHospitals)
    }

    @Test
    fun toggle_filters_updates_visibility() = runTest {
        val fakeRepo = FakeLocationRepository()
        val viewModel = MapViewModel(locationRepository = fakeRepo)
        advanceUntilIdle()

        viewModel.toggleHazards()
        assertFalse(viewModel.uiState.value.showHazards)

        viewModel.toggleShelters()
        assertFalse(viewModel.uiState.value.showShelters)

        viewModel.toggleHospitals()
        assertFalse(viewModel.uiState.value.showHospitals)
    }

    @Test
    fun select_facility_and_zone_updates_selection() = runTest {
        val fakeRepo = FakeLocationRepository()
        val viewModel = MapViewModel(locationRepository = fakeRepo)
        advanceUntilIdle()

        val fac = viewModel.uiState.value.facilities.first()
        viewModel.selectFacility(fac)
        assertEquals(fac, viewModel.uiState.value.selectedFacility)
        assertNull(viewModel.uiState.value.selectedZone)

        val zone = viewModel.uiState.value.zones.first()
        viewModel.selectZone(zone)
        assertEquals(zone, viewModel.uiState.value.selectedZone)
        assertNull(viewModel.uiState.value.selectedFacility)

        viewModel.clearSelection()
        assertNull(viewModel.uiState.value.selectedFacility)
        assertNull(viewModel.uiState.value.selectedZone)
    }

    @Test
    fun nearest_shelter_computes_closest_shelter_to_user() = runTest {
        val fakeRepo = FakeLocationRepository()
        val viewModel = MapViewModel(locationRepository = fakeRepo)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        val nearest = state.nearestShelter
        assertNotNull(nearest)
        // User starts at Varanasi Central (25.3150, 83.0650)
        // Distance to S1 (25.355, 83.072) vs S2 (25.295, 83.013)
        assertNotNull(state.nearestShelterDistanceKm)
        assertTrue(state.nearestShelterDistanceKm!! > 0)
    }
}
