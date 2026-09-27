package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.data.remote.VedraqApiService
import com.vedraq.app.data.remote.dto.IncidentCreateRequestDto
import com.vedraq.app.data.remote.dto.IncidentStatusUpdateRequestDto
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
import com.vedraq.app.domain.model.SosBeacon
import com.vedraq.app.domain.model.SosStatus
import com.vedraq.app.domain.repository.IncidentRepository
import com.vedraq.app.domain.repository.SosRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.IOException
import java.util.UUID

class SosRepositoryImpl(
    private val apiService: VedraqApiService = NetworkModule.apiService,
    private val incidentRepository: IncidentRepository? = null
) : SosRepository {

    private val activeBeaconState = MutableStateFlow<SosBeacon?>(null)
    private var lastCoreIncidentId: String? = null

    override fun observeActiveBeacon(): Flow<SosBeacon?> {
        return activeBeaconState.asStateFlow()
    }

    override suspend fun triggerSos(
        latitude: Double,
        longitude: Double,
        accuracyMeters: Float,
        notes: String?
    ): Resource<SosBeacon> {
        val beaconId = "SOS-${UUID.randomUUID().toString().take(8).uppercase()}"
        val beacon = SosBeacon(
            beaconId = beaconId,
            userId = "USER-LOCAL-001",
            latitude = latitude,
            longitude = longitude,
            accuracyMeters = accuracyMeters,
            status = SosStatus.TRIGGERED,
            triggeredAtTimestamp = System.currentTimeMillis(),
            medicalNotes = notes
        )

        // Real emergency transmission to VEDRAQ Core backend
        val requestDto = IncidentCreateRequestDto(
            title = "EMERGENCY SOS: Panic Beacon Activated",
            description = "Panic SOS beacon triggered from field mobile application. Notes: ${notes ?: "Immediate emergency response requested"}. Accuracy: ±${accuracyMeters}m",
            disasterType = "MEDICAL_EMERGENCY",
            severity = "CRITICAL",
            latitude = latitude,
            longitude = longitude,
            address = "Emergency SOS Coordinates (Lat: $latitude, Lon: $longitude)",
            reporterId = beacon.userId,
            peopleAffectedEstimate = 1,
            clientIncidentId = beaconId,
            source = "VEDRAQ_APP_SOS"
        )

        try {
            val response = apiService.createIncident(requestDto)
            if (response.isSuccessful && response.body() != null) {
                lastCoreIncidentId = response.body()!!.id
                val updatedBeacon = beacon.copy(status = SosStatus.TRANSMITTING)
                activeBeaconState.value = updatedBeacon
                return Resource.Success(updatedBeacon)
            } else {
                // If Core returns an error status, keep local beacon active
                activeBeaconState.value = beacon
                queueOfflineIncident(beacon, notes)
                return Resource.Success(beacon)
            }
        } catch (e: IOException) {
            // Core offline / network unavailable: activate locally and queue for sync
            activeBeaconState.value = beacon
            queueOfflineIncident(beacon, notes)
            return Resource.Success(beacon)
        } catch (e: Exception) {
            activeBeaconState.value = beacon
            return Resource.Success(beacon)
        }
    }

    private suspend fun queueOfflineIncident(beacon: SosBeacon, notes: String?) {
        incidentRepository?.submitIncident(
            Incident(
                id = beacon.beaconId,
                type = DisasterType.MEDICAL_EMERGENCY,
                severity = SeverityLevel.CRITICAL,
                title = "EMERGENCY SOS: Panic Beacon Activated",
                description = "Panic SOS beacon triggered while offline. Notes: ${notes ?: "Immediate emergency response requested"}.",
                latitude = beacon.latitude,
                longitude = beacon.longitude,
                address = "Emergency SOS Coordinates",
                reporterId = beacon.userId,
                status = IncidentStatus.REPORTED,
                isSyncedWithCore = false
            )
        )
    }

    override suspend fun updateLocation(
        beaconId: String,
        latitude: Double,
        longitude: Double,
        accuracyMeters: Float
    ): Resource<Unit> {
        val current = activeBeaconState.value
        if (current != null && current.beaconId == beaconId) {
            activeBeaconState.value = current.copy(
                latitude = latitude,
                longitude = longitude,
                accuracyMeters = accuracyMeters,
                status = SosStatus.TRANSMITTING
            )
        }
        return Resource.Success(Unit)
    }

    override suspend fun cancelSos(beaconId: String): Resource<Unit> {
        val coreId = lastCoreIncidentId
        if (coreId != null) {
            try {
                apiService.updateIncidentStatus(
                    id = coreId,
                    request = IncidentStatusUpdateRequestDto(
                        status = "CANCELLED",
                        note = "SOS panic beacon cancelled by user"
                    )
                )
            } catch (_: Exception) {
                // Ignore failure on cancellation if Core is unreachable
            }
        }
        activeBeaconState.value = null
        lastCoreIncidentId = null
        return Resource.Success(Unit)
    }
}
