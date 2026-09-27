package com.vedraq.app.data.local

import com.vedraq.app.domain.model.DisasterAlert
import com.vedraq.app.domain.model.Incident
import kotlinx.coroutines.flow.Flow

/**
 * Contract interfaces for Room / local persistence.
 * Prepared for offline-first caching of incidents and alerts.
 */
interface IncidentLocalDataSource {
    fun getAllIncidents(): Flow<List<Incident>>
    suspend fun insertIncident(incident: Incident)
    suspend fun getPendingSyncIncidents(): List<Incident>
    suspend fun markAsSynced(incidentId: String)
    suspend fun getIncidentById(id: String): Incident?
}

interface AlertLocalDataSource {
    fun getCachedAlerts(): Flow<List<DisasterAlert>>
    suspend fun saveAlerts(alerts: List<DisasterAlert>)
    suspend fun clearAlerts()
}
