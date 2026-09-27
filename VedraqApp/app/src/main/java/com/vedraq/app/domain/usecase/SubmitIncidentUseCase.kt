package com.vedraq.app.domain.usecase

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.repository.IncidentRepository

class SubmitIncidentUseCase(
    private val incidentRepository: IncidentRepository
) {
    suspend operator fun invoke(incident: Incident): Resource<Incident> {
        if (incident.title.isBlank()) {
            return Resource.Error("Incident title cannot be empty")
        }
        return incidentRepository.submitIncident(incident)
    }
}
