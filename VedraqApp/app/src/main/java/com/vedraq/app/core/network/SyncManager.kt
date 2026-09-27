package com.vedraq.app.core.network

import com.vedraq.app.domain.repository.AlertRepository
import com.vedraq.app.domain.repository.IncidentRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Observes network connectivity and automatically triggers synchronization
 * of locally queued incidents and refreshes alerts when connection to VEDRAQ Core is restored.
 */
class SyncManager(
    private val connectivityObserver: ConnectivityObserver,
    private val incidentRepository: IncidentRepository,
    private val alertRepository: AlertRepository,
    private val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
) {
    fun startObserving() {
        scope.launch {
            connectivityObserver.observe().collectLatest { status ->
                if (status == ConnectivityObserver.Status.Available) {
                    try {
                        incidentRepository.syncPendingIncidents()
                        alertRepository.refreshAlerts()
                    } catch (_: Exception) {
                        // Resilient retry on next network tick
                    }
                }
            }
        }
    }
}
