package com.vedraq.app.domain.repository

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.SosBeacon
import kotlinx.coroutines.flow.Flow

/**
 * Interface contract for emergency SOS panic beacon activation, tracking, and cancellation.
 */
interface SosRepository {
    fun observeActiveBeacon(): Flow<SosBeacon?>
    suspend fun triggerSos(latitude: Double, longitude: Double, accuracyMeters: Float, notes: String?): Resource<SosBeacon>
    suspend fun updateLocation(beaconId: String, latitude: Double, longitude: Double, accuracyMeters: Float): Resource<Unit>
    suspend fun cancelSos(beaconId: String): Resource<Unit>
}
