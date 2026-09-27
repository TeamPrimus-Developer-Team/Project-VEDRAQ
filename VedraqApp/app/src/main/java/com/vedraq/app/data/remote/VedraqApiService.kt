package com.vedraq.app.data.remote

import com.vedraq.app.data.remote.dto.FacilitiesResponseDto
import com.vedraq.app.data.remote.dto.IncidentCreateRequestDto
import com.vedraq.app.data.remote.dto.IncidentListResponseDto
import com.vedraq.app.data.remote.dto.IncidentResponseDto
import com.vedraq.app.data.remote.dto.IncidentStatusUpdateRequestDto
import com.vedraq.app.data.remote.dto.LocationListResponseDto
import com.vedraq.app.data.remote.dto.ZoneListResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Retrofit REST API interface for VEDRAQ Core emergency backend.
 */
interface VedraqApiService {

    /**
     * Dispatch an emergency incident report to VEDRAQ Core.
     * Expects HTTP 201 Created on success.
     */
    @POST("api/incidents")
    suspend fun createIncident(
        @Body request: IncidentCreateRequestDto
    ): Response<IncidentResponseDto>

    /**
     * Fetch list of reported incidents from VEDRAQ Core.
     */
    @GET("api/incidents")
    suspend fun getIncidents(
        @Query("status") status: String? = null
    ): Response<IncidentListResponseDto>

    /**
     * Fetch single incident by authoritative server ID.
     */
    @GET("api/incidents/{id}")
    suspend fun getIncidentById(
        @Path("id") id: String
    ): Response<IncidentResponseDto>

    /**
     * Update incident lifecycle status on VEDRAQ Core (e.g. ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CANCELLED).
     */
    @PATCH("api/incidents/{id}")
    suspend fun updateIncidentStatus(
        @Path("id") id: String,
        @Body request: IncidentStatusUpdateRequestDto
    ): Response<IncidentResponseDto>

    /**
     * Fetch authoritative locations across scenarios from VEDRAQ Core.
     */
    @GET("api/locations")
    suspend fun getLocations(): Response<LocationListResponseDto>

    /**
     * Fetch authoritative tactical operational zones for the active scenario from VEDRAQ Core.
     */
    @GET("api/zones")
    suspend fun getZones(): Response<ZoneListResponseDto>

    /**
     * Fetch authoritative facilities (hospitals, shelters, depots) from VEDRAQ Core.
     */
    @GET("api/facilities")
    suspend fun getFacilities(): Response<FacilitiesResponseDto>

    /**
     * Diagnostic health check to verify VEDRAQ Core connectivity.
     */
    @GET("api/health")
    suspend fun checkHealth(): Response<Map<String, Any>>
}
