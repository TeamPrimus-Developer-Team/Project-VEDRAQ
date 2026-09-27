package com.vedraq.app.domain.repository

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.DisasterAlert
import kotlinx.coroutines.flow.Flow

/**
 * Interface contract for receiving emergency disaster alerts and advisories.
 */
interface AlertRepository {
    fun getActiveAlerts(): Flow<List<DisasterAlert>>
    suspend fun refreshAlerts(): Resource<List<DisasterAlert>>
    suspend fun getAlertById(id: String): DisasterAlert?
}
