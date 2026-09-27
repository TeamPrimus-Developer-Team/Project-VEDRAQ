package com.vedraq.app.data.repository

import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.core.util.Resource
import com.vedraq.app.data.remote.VedraqApiService
import com.vedraq.app.domain.model.DisasterAlert
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.SeverityLevel
import com.vedraq.app.domain.repository.AlertRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.time.Instant

class AlertRepositoryImpl(
    private val apiService: VedraqApiService = NetworkModule.apiService
) : AlertRepository {

    private val alertsState = MutableStateFlow<List<DisasterAlert>>(
        listOf(
            DisasterAlert(
                id = "alert-varanasi-001",
                title = "Flash Flood Emergency Broadcast",
                summary = "Heavy monsoon riverine inundation across Assi Ghat and Dashashwamedh corridor. Rapid water level rise observed.",
                instructions = "Do not transit submerged roads. Follow designated evacuation paths toward higher ground shelters.",
                severity = SeverityLevel.CRITICAL,
                disasterType = DisasterType.FLOOD,
                affectedRegion = "Varanasi Riverbank & Assi Ghat Basin",
                radiusKilometers = 8.5,
                issuedAtTimestamp = System.currentTimeMillis() - 1000 * 60 * 30,
                isEvacuationMandatory = true
            ),
            DisasterAlert(
                id = "alert-varanasi-002",
                title = "Submerged Culvert & Road Block Advisory",
                summary = "Critical access roads R3 and R6 impassable due to waterlogging and debris accumulation.",
                instructions = "Ground vehicles must reroute via GT Road bypass. Check tactical map for open routes.",
                severity = SeverityLevel.HIGH,
                disasterType = DisasterType.INFRASTRUCTURE_FAILURE,
                affectedRegion = "Chaukaghat & Northern Access Arteries",
                radiusKilometers = 14.0,
                issuedAtTimestamp = System.currentTimeMillis() - 1000 * 60 * 90,
                isEvacuationMandatory = false
            ),
            DisasterAlert(
                id = "alert-varanasi-003",
                title = "Chemical Storage Depot Precaution",
                summary = "Proximity alert near industrial storage depot in sector 7. Containment inspection underway.",
                instructions = "Maintain 500m safety clearance until hazmat certification is completed.",
                severity = SeverityLevel.MODERATE,
                disasterType = DisasterType.HAZMAT,
                affectedRegion = "Industrial Depot Sector 7",
                radiusKilometers = 3.5,
                issuedAtTimestamp = System.currentTimeMillis() - 1000 * 60 * 240,
                isEvacuationMandatory = false
            )
        )
    )

    override fun getActiveAlerts(): Flow<List<DisasterAlert>> {
        return alertsState.asStateFlow()
    }

    override suspend fun refreshAlerts(): Resource<List<DisasterAlert>> {
        return try {
            val response = apiService.getIncidents()
            if (response.isSuccessful && response.body() != null) {
                val incidents = response.body()!!.incidents
                val dynamicAlerts = incidents.map { inc ->
                    val domainSeverity = SeverityLevel.values().firstOrNull {
                        it.name.equals(inc.severity, ignoreCase = true)
                    } ?: SeverityLevel.HIGH

                    val domainType = DisasterType.values().firstOrNull {
                        it.name.equals(inc.disasterType, ignoreCase = true)
                    } ?: DisasterType.OTHER

                    val parsedTimestamp = try {
                        Instant.parse(inc.createdAt).toEpochMilli()
                    } catch (_: Exception) {
                        System.currentTimeMillis()
                    }

                    DisasterAlert(
                        id = "alert-${inc.id}",
                        title = inc.title,
                        summary = inc.description,
                        instructions = "Status: ${inc.status}. Assigned Tactical Sector: ${inc.nearestZoneName ?: inc.address ?: "Operations Zone"}.",
                        severity = domainSeverity,
                        disasterType = domainType,
                        affectedRegion = inc.nearestZoneName ?: inc.address ?: "Varanasi District",
                        radiusKilometers = inc.nearestZoneDistanceKm ?: 6.0,
                        issuedAtTimestamp = parsedTimestamp,
                        isEvacuationMandatory = (domainSeverity == SeverityLevel.CRITICAL)
                    )
                }

                if (dynamicAlerts.isNotEmpty()) {
                    // Merge with baseline defaults
                    val merged = (dynamicAlerts + alertsState.value).distinctBy { it.id }
                    alertsState.value = merged
                }
                Resource.Success(alertsState.value)
            } else {
                Resource.Error("Core returned HTTP ${response.code()}. Displaying cached alerts.")
            }
        } catch (e: Exception) {
            // Resilient offline fallback
            Resource.Error("Core unreachable (${e.localizedMessage ?: "Offline"}). Retaining offline cached alerts.")
        }
    }

    override suspend fun getAlertById(id: String): DisasterAlert? {
        return alertsState.value.firstOrNull { it.id == id }
    }
}
