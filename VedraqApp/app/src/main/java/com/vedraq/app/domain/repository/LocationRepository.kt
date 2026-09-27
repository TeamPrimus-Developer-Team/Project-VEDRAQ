package com.vedraq.app.domain.repository

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.CoreLocation
import com.vedraq.app.domain.model.TacticalFacility
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow

/**
 * Domain repository managing authoritative scenario locations, tactical operational zones,
 * and emergency facilities (hospitals, shelters, depots) from VEDRAQ Core.
 */
interface LocationRepository {

    /**
     * Observe authoritative locations for the requested scenario (default "varanasi").
     * Filters out non-matching scenarios (e.g. Nepal locations when Varanasi is selected).
     */
    fun getLocations(scenarioId: String = "varanasi"): Flow<List<CoreLocation>>

    /**
     * Observe authoritative tactical facilities (hospitals, shelters, depots) from Core.
     */
    fun getFacilities(): Flow<List<TacticalFacility>>

    /**
     * Synchronize authoritative locations from VEDRAQ Core API (GET /api/locations & GET /api/zones).
     */
    suspend fun refreshLocations(scenarioId: String = "varanasi"): Resource<List<CoreLocation>>

    /**
     * Synchronize authoritative facilities from VEDRAQ Core API (GET /api/facilities).
     */
    suspend fun refreshFacilities(): Resource<List<TacticalFacility>>

    /**
     * Observe real-time Core connectivity state (true = Online, false = Offline, null = Unknown).
     */
    fun observeCoreOnline(): StateFlow<Boolean?>

    /**
     * Observe whether currently emitted data was live synchronized from Core or is local fallback.
     */
    fun observeIsLiveCoreData(): StateFlow<Boolean>
}
