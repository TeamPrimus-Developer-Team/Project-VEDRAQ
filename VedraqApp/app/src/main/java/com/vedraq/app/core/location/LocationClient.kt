package com.vedraq.app.core.location

import kotlinx.coroutines.flow.Flow

/**
 * Domain model representing a verified geographic location coordinate.
 */
data class LocationCoordinates(
    val latitude: Double,
    val longitude: Double,
    val accuracyMeters: Float? = null,
    val altitudeMeters: Double? = null,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * Interface contract for location providers (GPS, Fused Location Provider).
 * Ready for high-precision emergency beacon location tracking.
 */
interface LocationClient {
    fun getLocationUpdates(intervalMs: Long): Flow<LocationCoordinates>
    suspend fun getCurrentLocation(): LocationCoordinates?

    class LocationException(message: String) : Exception(message)
}
