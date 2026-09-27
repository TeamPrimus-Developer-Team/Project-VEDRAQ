package com.vedraq.app.core.location

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Looper
import com.vedraq.app.core.permissions.PermissionHelper
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * Standard Android implementation of LocationClient using Android LocationManager.
 * Does not depend on Google Play Services, ensuring compatibility across all devices and emulators.
 */
class AndroidLocationClient(
    private val context: Context
) : LocationClient {

    private val locationManager: LocationManager by lazy {
        context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    }

    @SuppressLint("MissingPermission")
    override suspend fun getCurrentLocation(): LocationCoordinates? {
        if (!PermissionHelper.hasLocationPermission(context)) {
            return null
        }

        val providers = listOf(
            LocationManager.GPS_PROVIDER,
            LocationManager.NETWORK_PROVIDER,
            LocationManager.PASSIVE_PROVIDER
        )

        var bestLocation: Location? = null

        for (provider in providers) {
            try {
                if (locationManager.isProviderEnabled(provider)) {
                    val location = locationManager.getLastKnownLocation(provider)
                    if (location != null && (bestLocation == null || location.accuracy < bestLocation.accuracy)) {
                        bestLocation = location
                    }
                }
            } catch (_: SecurityException) {
                // Handled by permission check
            } catch (_: Exception) {
                // Provider may not be supported on this device/emulator
            }
        }

        return bestLocation?.toCoordinates()
    }

    @SuppressLint("MissingPermission")
    override fun getLocationUpdates(intervalMs: Long): Flow<LocationCoordinates> = callbackFlow {
        if (!PermissionHelper.hasLocationPermission(context)) {
            close(LocationClient.LocationException("Location permissions not granted"))
            return@callbackFlow
        }

        val isGpsEnabled = locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)
        val isNetworkEnabled = locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)

        if (!isGpsEnabled && !isNetworkEnabled) {
            close(LocationClient.LocationException("Location services are disabled"))
            return@callbackFlow
        }

        val listener = object : LocationListener {
            override fun onLocationChanged(location: Location) {
                trySend(location.toCoordinates())
            }

            @Deprecated("Deprecated in Java")
            override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) = Unit
            override fun onProviderEnabled(provider: String) = Unit
            override fun onProviderDisabled(provider: String) = Unit
        }

        // Emit cached fix if available
        getCurrentLocation()?.let { trySend(it) }

        val provider = if (isGpsEnabled) LocationManager.GPS_PROVIDER else LocationManager.NETWORK_PROVIDER

        try {
            locationManager.requestLocationUpdates(
                provider,
                intervalMs,
                5f, // 5 meters min distance
                listener,
                Looper.getMainLooper()
            )
        } catch (e: Exception) {
            close(LocationClient.LocationException(e.message ?: "Failed to request location updates"))
        }

        awaitClose {
            try {
                locationManager.removeUpdates(listener)
            } catch (_: Exception) {
            }
        }
    }

    private fun Location.toCoordinates(): LocationCoordinates {
        return LocationCoordinates(
            latitude = latitude,
            longitude = longitude,
            accuracyMeters = if (hasAccuracy()) accuracy else null,
            altitudeMeters = if (hasAltitude()) altitude else null,
            timestamp = time
        )
    }
}
