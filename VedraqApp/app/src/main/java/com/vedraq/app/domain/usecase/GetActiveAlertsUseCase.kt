package com.vedraq.app.domain.usecase

import com.vedraq.app.domain.model.DisasterAlert
import com.vedraq.app.domain.repository.AlertRepository
import kotlinx.coroutines.flow.Flow

class GetActiveAlertsUseCase(
    private val alertRepository: AlertRepository
) {
    operator fun invoke(): Flow<List<DisasterAlert>> {
        return alertRepository.getActiveAlerts()
    }
}
