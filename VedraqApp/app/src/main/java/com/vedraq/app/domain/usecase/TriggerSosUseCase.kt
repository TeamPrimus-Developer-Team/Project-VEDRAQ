package com.vedraq.app.domain.usecase

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.SosBeacon
import com.vedraq.app.domain.repository.SosRepository

class TriggerSosUseCase(
    private val sosRepository: SosRepository
) {
    suspend operator fun invoke(
        latitude: Double,
        longitude: Double,
        accuracyMeters: Float,
        notes: String? = null
    ): Resource<SosBeacon> {
        return sosRepository.triggerSos(latitude, longitude, accuracyMeters, notes)
    }
}
