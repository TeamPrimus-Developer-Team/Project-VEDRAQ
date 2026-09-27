package com.vedraq.app.domain.repository

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.Incident
import kotlinx.coroutines.flow.Flow

/**
 * Interface contract for reporting, caching, and retrieving emergency incidents.
 * Connected to VEDRAQ Core REST API and local offline queue.
 */
interface IncidentRepository {
    fun getLocalIncidents(): Flow<List<Incident>>
    suspend fun submitIncident(incident: Incident): Resource<Incident>
    suspend fun syncPendingIncidents(): Resource<Int>
    suspend fun getIncidentById(id: String): Incident?
    suspend fun fetchIncidentsFromCore(): Resource<List<Incident>>
    suspend fun resolveIncident(incidentId: String, note: String? = null): Resource<Incident>
}
