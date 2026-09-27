package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.data.remote.VedraqApiService
import com.vedraq.app.domain.model.CoreLocation
import com.vedraq.app.domain.model.CoreLocations
import com.vedraq.app.domain.model.FacilityType
import com.vedraq.app.domain.model.TacticalFacility
import com.vedraq.app.domain.repository.LocationRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import java.io.IOException

/**
 * Production implementation of LocationRepository connecting to VEDRAQ Core.
 * Manages dynamic synchronization of authoritative scenario locations, tactical zones,
 * and emergency facilities while providing graceful offline fallback and scenario isolation.
 */
class LocationRepositoryImpl(
    private val apiService: VedraqApiService = NetworkModule.apiService
) : LocationRepository {

    // Authoritative baseline facilities from data/scenarios/varanasi/facilities.json for offline fallback
    private val baselineFacilities: List<TacticalFacility> = listOf(
        TacticalFacility(
            id = "H1",
            name = "District Hospital Varanasi",
            type = FacilityType.HOSPITAL,
            latitude = 25.358,
            longitude = 83.074,
            status = "functional",
            capacity = 200,
            availableBeds = 142,
            specialization = "General, Emergency, Surgical",
            zoneId = "Z02"
        ),
        TacticalFacility(
            id = "H2",
            name = "Durgakund Medical Centre",
            type = FacilityType.HOSPITAL,
            latitude = 25.321,
            longitude = 83.003,
            status = "functional",
            capacity = 350,
            availableBeds = 265,
            specialization = "Multi-Speciality, Cardiology",
            zoneId = "Z06"
        ),
        TacticalFacility(
            id = "H3",
            name = "PHC Bhelpur",
            type = FacilityType.HOSPITAL,
            latitude = 25.341,
            longitude = 83.098,
            status = "partial",
            capacity = 80,
            availableBeds = 45,
            specialization = "Primary Healthcare, OPD",
            zoneId = "Z04"
        ),
        TacticalFacility(
            id = "S1",
            name = "Govt School Chandpur",
            type = FacilityType.SHELTER,
            latitude = 25.355,
            longitude = 83.072,
            capacity = 2500,
            currentOccupancy = 1200,
            status = "open",
            foodStockDays = 5,
            waterSupply = "functional"
        ),
        TacticalFacility(
            id = "S2",
            name = "Durgakund Community Hall",
            type = FacilityType.SHELTER,
            latitude = 25.323,
            longitude = 83.001,
            capacity = 2800,
            currentOccupancy = 1450,
            status = "open",
            foodStockDays = 7,
            waterSupply = "functional"
        ),
        TacticalFacility(
            id = "S3",
            name = "Lahartara Flood Camp",
            type = FacilityType.SHELTER,
            latitude = 25.373,
            longitude = 83.040,
            capacity = 2200,
            currentOccupancy = 880,
            status = "open",
            foodStockDays = 4,
            waterSupply = "functional"
        ),
        TacticalFacility(
            id = "DEPOT",
            name = "NDRF Resource Depot 01 — Central",
            type = FacilityType.DEPOT,
            latitude = 25.332,
            longitude = 83.025,
            capacity = 500
        )
    )

    private val _allLocationsState = MutableStateFlow<List<CoreLocation>>(CoreLocations.ALL)
    private val _facilitiesState = MutableStateFlow<List<TacticalFacility>>(baselineFacilities)

    private val _isCoreOnlineState = MutableStateFlow<Boolean?>(null)
    private val _isLiveCoreDataState = MutableStateFlow(false)

    override fun getLocations(scenarioId: String): Flow<List<CoreLocation>> {
        return _allLocationsState.map { list ->
            CoreLocations.filterByScenario(list, scenarioId)
        }
    }

    override fun getFacilities(): Flow<List<TacticalFacility>> {
        return _facilitiesState.asStateFlow()
    }

    override fun observeCoreOnline(): StateFlow<Boolean?> {
        return _isCoreOnlineState.asStateFlow()
    }

    override fun observeIsLiveCoreData(): StateFlow<Boolean> {
        return _isLiveCoreDataState.asStateFlow()
    }

    override suspend fun refreshLocations(scenarioId: String): Resource<List<CoreLocation>> {
        return try {
            val response = apiService.getLocations()
            if (response.isSuccessful && response.body() != null) {
                val locListDto = response.body()!!
                val mappedLocations = locListDto.locations.map { dto ->
                    CoreLocation(
                        id = dto.id,
                        name = dto.name,
                        region = dto.region ?: (dto.city ?: ""),
                        latitude = dto.latitude,
                        longitude = dto.longitude,
                        isScenarioCenter = dto.type.equals("SCENARIO_CENTER", ignoreCase = true),
                        associatedZoneId = if (dto.id.startsWith("Z") || dto.id.startsWith("N")) dto.id else null,
                        type = dto.type ?: "TACTICAL_ZONE"
                    )
                }

                // If zones endpoint is available, enrich with detailed operational metrics (damage %, HCI, road status)
                val enrichedLocations = try {
                    val zonesResponse = apiService.getZones()
                    if (zonesResponse.isSuccessful && zonesResponse.body() != null) {
                        val zones = zonesResponse.body()!!.zones.associateBy { it.id }
                        mappedLocations.map { loc ->
                            val zoneMeta = zones[loc.id]
                            if (zoneMeta != null) {
                                loc.copy(
                                    damagePercentage = zoneMeta.damagePercentage,
                                    classification = zoneMeta.classification,
                                    roadAccessibility = zoneMeta.roadAccessibility,
                                    population = zoneMeta.population
                                )
                            } else {
                                loc
                            }
                        }
                    } else {
                        mappedLocations
                    }
                } catch (_: Exception) {
                    mappedLocations
                }

                _allLocationsState.value = enrichedLocations
                _isCoreOnlineState.value = true
                _isLiveCoreDataState.value = true

                val filtered = CoreLocations.filterByScenario(enrichedLocations, scenarioId)
                Resource.Success(filtered)
            } else {
                _isCoreOnlineState.value = false
                val code = response.code()
                Resource.Error("Core returned HTTP $code when loading locations")
            }
        } catch (e: IOException) {
            _isCoreOnlineState.value = false
            Resource.Error("VEDRAQ Core unavailable. Displaying local cached baseline.")
        } catch (e: Exception) {
            _isCoreOnlineState.value = false
            Resource.Error("Failed to synchronize locations: ${e.localizedMessage ?: "Unknown error"}")
        }
    }

    override suspend fun refreshFacilities(): Resource<List<TacticalFacility>> {
        return try {
            val response = apiService.getFacilities()
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val facilities = mutableListOf<TacticalFacility>()

                body.hospitals.forEach { h ->
                    facilities.add(
                        TacticalFacility(
                            id = h.id,
                            name = h.name,
                            type = FacilityType.HOSPITAL,
                            latitude = h.latitude,
                            longitude = h.longitude,
                            status = h.status ?: "functional",
                            capacity = h.capacity,
                            availableBeds = h.availableBeds,
                            specialization = h.specialization,
                            zoneId = h.zoneId
                        )
                    )
                }

                body.shelters.forEach { s ->
                    facilities.add(
                        TacticalFacility(
                            id = s.id,
                            name = s.name,
                            type = FacilityType.SHELTER,
                            latitude = s.latitude,
                            longitude = s.longitude,
                            capacity = s.capacity,
                            currentOccupancy = s.currentOccupancy,
                            status = s.status ?: "open",
                            foodStockDays = s.foodStockDays,
                            waterSupply = s.waterSupply
                        )
                    )
                }

                body.depots.forEach { d ->
                    facilities.add(
                        TacticalFacility(
                            id = d.id,
                            name = d.name,
                            type = FacilityType.DEPOT,
                            latitude = d.latitude,
                            longitude = d.longitude,
                            capacity = d.capacity
                        )
                    )
                }

                _facilitiesState.value = facilities
                _isCoreOnlineState.value = true
                Resource.Success(facilities)
            } else {
                _isCoreOnlineState.value = false
                Resource.Error("Core returned HTTP ${response.code()} when loading facilities")
            }
        } catch (e: IOException) {
            _isCoreOnlineState.value = false
            Resource.Error("VEDRAQ Core unavailable. Displaying baseline tactical facilities.")
        } catch (e: Exception) {
            _isCoreOnlineState.value = false
            Resource.Error("Failed to synchronize facilities: ${e.localizedMessage ?: "Unknown error"}")
        }
    }
}
