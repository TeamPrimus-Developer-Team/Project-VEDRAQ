package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.data.remote.VedraqApiService
import com.vedraq.app.data.remote.dto.IncidentStatusUpdateRequestDto
import com.vedraq.app.data.remote.mapper.toCreateRequestDto
import com.vedraq.app.data.remote.mapper.toDomain
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.model.IncidentStatus
import com.vedraq.app.domain.model.SeverityLevel
import com.vedraq.app.domain.repository.IncidentRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.io.IOException

/**
 * Production implementation of IncidentRepository communicating with VEDRAQ Core.
 * Provides resilient offline queuing, reactive StateFlow updates, and server-authoritative reconciliation.
 */
class IncidentRepositoryImpl(
    private val apiService: VedraqApiService = NetworkModule.apiService
) : IncidentRepository {

    private val mutex = Mutex()
    private val incidentsState = MutableStateFlow<List<Incident>>(
        listOf(
            Incident(
                id = "INC-LOCAL-001",
                type = DisasterType.FLOOD,
                severity = SeverityLevel.HIGH,
                title = "Flash Flood Warning - Sector 4",
                description = "Rapid water level rise observed near river embankment. Drainage channels overflowing.",
                latitude = 25.3150,
                longitude = 83.0050,
                address = "Riverbank Corridor, Sector 4, Varanasi",
                timestamp = System.currentTimeMillis() - 1000 * 60 * 45,
                status = IncidentStatus.RESPONDING,
                isSyncedWithCore = true
            ),
            Incident(
                id = "INC-LOCAL-002",
                type = DisasterType.INFRASTRUCTURE_FAILURE,
                severity = SeverityLevel.CRITICAL,
                title = "Bridge Structural Damage",
                description = "Vehicular transit halted due to bridge girder crack. Alternate route activated.",
                latitude = 25.3200,
                longitude = 83.0150,
                address = "North Crossing Bridge, Varanasi",
                timestamp = System.currentTimeMillis() - 1000 * 60 * 120,
                status = IncidentStatus.VERIFIED,
                isSyncedWithCore = true
            )
        )
    )

    override fun getLocalIncidents(): Flow<List<Incident>> {
        return incidentsState.asStateFlow()
    }

    override suspend fun submitIncident(incident: Incident): Resource<Incident> {
        val requestDto = incident.toCreateRequestDto()

        return try {
            val response = apiService.createIncident(requestDto)

            if (response.isSuccessful) {
                val body = response.body()
                if (body != null) {
                    val authoritativeIncident = body.toDomain()
                    mutex.withLock {
                        val currentList = incidentsState.value.toMutableList()
                        // Remove temporary client copy if present, prepend authoritative record
                        currentList.removeAll { it.id == incident.id || it.id == authoritativeIncident.id }
                        currentList.add(0, authoritativeIncident)
                        incidentsState.value = currentList
                    }
                    Resource.Success(authoritativeIncident)
                } else {
                    Resource.Error("Server returned empty response body")
                }
            } else {
                val errorBody = response.errorBody()?.string() ?: "HTTP ${response.code()}"
                Resource.Error("Server error (${response.code()}): $errorBody")
            }
        } catch (e: IOException) {
            // Network unreachable / timeout: queue locally in offline store
            val offlineIncident = incident.copy(isSyncedWithCore = false)
            mutex.withLock {
                val currentList = incidentsState.value.toMutableList()
                currentList.removeAll { it.id == offlineIncident.id }
                currentList.add(0, offlineIncident)
                incidentsState.value = currentList
            }
            Resource.Error("Network unreachable: Core offline. Queued locally in offline storage.")
        } catch (e: Exception) {
            Resource.Error("Unexpected failure dispatching incident: ${e.localizedMessage ?: "Unknown error"}")
        }
    }

    override suspend fun resolveIncident(incidentId: String, note: String?): Resource<Incident> {
        val requestDto = IncidentStatusUpdateRequestDto(
            status = "RESOLVED",
            note = note ?: "Incident resolved and verified by first responder"
        )
        return try {
            val response = apiService.updateIncidentStatus(incidentId, requestDto)
            if (response.isSuccessful && response.body() != null) {
                val updated = response.body()!!.toDomain()
                mutex.withLock {
                    val currentList = incidentsState.value.toMutableList()
                    val index = currentList.indexOfFirst { it.id == incidentId }
                    if (index >= 0) {
                        currentList[index] = updated
                    } else {
                        currentList.add(0, updated)
                    }
                    incidentsState.value = currentList
                }
                Resource.Success(updated)
            } else {
                val errorBody = response.errorBody()?.string() ?: "HTTP ${response.code()}"
                Resource.Error("Failed to resolve incident on Core: $errorBody")
            }
        } catch (e: IOException) {
            // Offline queueing: mark resolved locally pending sync
            mutex.withLock {
                val currentList = incidentsState.value.toMutableList()
                val index = currentList.indexOfFirst { it.id == incidentId }
                if (index >= 0) {
                    val locallyResolved = currentList[index].copy(
                        status = IncidentStatus.RESOLVED,
                        isSyncedWithCore = false
                    )
                    currentList[index] = locallyResolved
                    incidentsState.value = currentList
                    Resource.Success(locallyResolved)
                } else {
                    Resource.Error("Incident '$incidentId' not found in local offline storage")
                }
            }
        } catch (e: Exception) {
            Resource.Error("Unexpected error resolving incident: ${e.localizedMessage ?: "Unknown error"}")
        }
    }

    override suspend fun syncPendingIncidents(): Resource<Int> {
        val pendingList = incidentsState.value.filter { !it.isSyncedWithCore }
        var syncedCount = 0

        for (pending in pendingList) {
            try {
                if (pending.status == IncidentStatus.RESOLVED && !pending.id.startsWith("INC-LOCAL") && !pending.id.startsWith("CLIENT-")) {
                    // Update resolved status on server
                    val response = apiService.updateIncidentStatus(
                        id = pending.id,
                        request = IncidentStatusUpdateRequestDto(
                            status = "RESOLVED",
                            note = "Resolved via VEDRAQ offline synchronization"
                        )
                    )
                    if (response.isSuccessful && response.body() != null) {
                        val authoritative = response.body()!!.toDomain()
                        mutex.withLock {
                            val current = incidentsState.value.toMutableList()
                            val index = current.indexOfFirst { it.id == pending.id }
                            if (index >= 0) current[index] = authoritative
                            incidentsState.value = current
                        }
                        syncedCount++
                    }
                } else {
                    // Submit unsynced incident
                    val response = apiService.createIncident(pending.toCreateRequestDto())
                    if (response.isSuccessful && response.body() != null) {
                        val authoritative = response.body()!!.toDomain()
                        mutex.withLock {
                            val current = incidentsState.value.toMutableList()
                            current.removeAll { it.id == pending.id }
                            current.add(0, authoritative)
                            incidentsState.value = current
                        }
                        syncedCount++
                    }
                }
            } catch (_: Exception) {
                // Keep pending for next retry cycle
            }
        }

        return Resource.Success(syncedCount)
    }

    override suspend fun getIncidentById(id: String): Incident? {
        val local = incidentsState.value.firstOrNull { it.id == id }
        if (local != null) return local

        return try {
            val response = apiService.getIncidentById(id)
            if (response.isSuccessful) {
                response.body()?.toDomain()
            } else {
                null
            }
        } catch (_: Exception) {
            null
        }
    }

    override suspend fun fetchIncidentsFromCore(): Resource<List<Incident>> {
        return try {
            val response = apiService.getIncidents()
            if (response.isSuccessful) {
                val remoteList = response.body()?.incidents?.map { it.toDomain() } ?: emptyList()
                mutex.withLock {
                    val pendingLocal = incidentsState.value.filter { !it.isSyncedWithCore }
                    val merged = (pendingLocal + remoteList).distinctBy { it.id }
                    incidentsState.value = merged
                }
                Resource.Success(remoteList)
            } else {
                val errorBody = response.errorBody()?.string() ?: "HTTP ${response.code()}"
                Resource.Error("Failed to fetch incidents from Core: $errorBody")
            }
        } catch (e: Exception) {
            Resource.Error("Network failure connecting to VEDRAQ Core: ${e.localizedMessage ?: "Unknown error"}")
        }
    }
}
