package com.vedraq.app.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * Authoritative location entry returned by Core's GET /api/locations.
 */
@JsonClass(generateAdapter = false)
data class LocationDto(
    @param:Json(name = "id")
    val id: String,

    @param:Json(name = "name")
    val name: String,

    @param:Json(name = "city")
    val city: String? = null,

    @param:Json(name = "region")
    val region: String? = null,

    @param:Json(name = "latitude")
    val latitude: Double,

    @param:Json(name = "longitude")
    val longitude: Double,

    @param:Json(name = "type")
    val type: String? = null,

    @param:Json(name = "scenario_id")
    val scenarioId: String? = null
)

/**
 * Root container for GET /api/locations.
 */
@JsonClass(generateAdapter = false)
data class LocationListResponseDto(
    @param:Json(name = "locations")
    val locations: List<LocationDto> = emptyList(),

    @param:Json(name = "total")
    val total: Int = 0
)

/**
 * Tactical operational zone entry returned by Core's GET /api/zones.
 */
@JsonClass(generateAdapter = false)
data class ZoneDto(
    @param:Json(name = "id")
    val id: String,

    @param:Json(name = "name")
    val name: String,

    @param:Json(name = "latitude")
    val latitude: Double,

    @param:Json(name = "longitude")
    val longitude: Double,

    @param:Json(name = "population")
    val population: Int? = null,

    @param:Json(name = "affected_population")
    val affectedPopulation: Int? = null,

    @param:Json(name = "damage_percentage")
    val damagePercentage: Int? = null,

    @param:Json(name = "hospital_status")
    val hospitalStatus: String? = null,

    @param:Json(name = "hospital_capacity")
    val hospitalCapacity: Int? = null,

    @param:Json(name = "water_availability")
    val waterAvailability: String? = null,

    @param:Json(name = "food_availability")
    val foodAvailability: String? = null,

    @param:Json(name = "shelter_capacity")
    val shelterCapacity: Int? = null,

    @param:Json(name = "shelter_distance_km")
    val shelterDistanceKm: Double? = null,

    @param:Json(name = "road_accessibility")
    val roadAccessibility: String? = null,

    @param:Json(name = "communication_status")
    val communicationStatus: String? = null,

    @param:Json(name = "primary_road_id")
    val primaryRoadId: String? = null,

    @param:Json(name = "best_depot")
    val bestDepot: String? = null,

    @param:Json(name = "hci_score")
    val hciScore: Double? = null,

    @param:Json(name = "classification")
    val classification: String? = null,

    @param:Json(name = "priority_rank")
    val priorityRank: Int? = null,

    @param:Json(name = "people_at_risk")
    val peopleAtRisk: Int? = null,

    @param:Json(name = "evacuation_status")
    val evacuationStatus: String? = null
)

/**
 * Root container for GET /api/zones.
 */
@JsonClass(generateAdapter = false)
data class ZoneListResponseDto(
    @param:Json(name = "zones")
    val zones: List<ZoneDto> = emptyList(),

    @param:Json(name = "total")
    val total: Int = 0
)

/**
 * Hospital facility from Core's GET /api/facilities.
 */
@JsonClass(generateAdapter = false)
data class HospitalDto(
    @param:Json(name = "id")
    val id: String,

    @param:Json(name = "name")
    val name: String,

    @param:Json(name = "latitude")
    val latitude: Double,

    @param:Json(name = "longitude")
    val longitude: Double,

    @param:Json(name = "status")
    val status: String? = null,

    @param:Json(name = "capacity")
    val capacity: Int? = null,

    @param:Json(name = "zone_id")
    val zoneId: String? = null,

    @param:Json(name = "available_beds")
    val availableBeds: Int? = null,

    @param:Json(name = "specialization")
    val specialization: String? = null
)

/**
 * Shelter facility from Core's GET /api/facilities.
 */
@JsonClass(generateAdapter = false)
data class ShelterDto(
    @param:Json(name = "id")
    val id: String,

    @param:Json(name = "name")
    val name: String,

    @param:Json(name = "latitude")
    val latitude: Double,

    @param:Json(name = "longitude")
    val longitude: Double,

    @param:Json(name = "capacity")
    val capacity: Int? = null,

    @param:Json(name = "current_occupancy")
    val currentOccupancy: Int? = null,

    @param:Json(name = "status")
    val status: String? = null,

    @param:Json(name = "food_stock_days")
    val foodStockDays: Int? = null,

    @param:Json(name = "water_supply")
    val waterSupply: String? = null
)

/**
 * Depot facility from Core's GET /api/facilities.
 */
@JsonClass(generateAdapter = false)
data class DepotDto(
    @param:Json(name = "id")
    val id: String,

    @param:Json(name = "name")
    val name: String,

    @param:Json(name = "latitude")
    val latitude: Double,

    @param:Json(name = "longitude")
    val longitude: Double,

    @param:Json(name = "capacity")
    val capacity: Int? = null
)

/**
 * Root container for GET /api/facilities.
 */
@JsonClass(generateAdapter = false)
data class FacilitiesResponseDto(
    @param:Json(name = "hospitals")
    val hospitals: List<HospitalDto> = emptyList(),

    @param:Json(name = "shelters")
    val shelters: List<ShelterDto> = emptyList(),

    @param:Json(name = "depots")
    val depots: List<DepotDto> = emptyList()
)
