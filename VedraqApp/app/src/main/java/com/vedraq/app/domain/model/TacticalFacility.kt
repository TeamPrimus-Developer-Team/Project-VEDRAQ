package com.vedraq.app.domain.model

enum class FacilityType {
    HOSPITAL,
    SHELTER,
    DEPOT
}

/**
 * Authoritative facility model representing Core hospitals, shelters, and resource depots.
 * Directly mirrors the facilities defined in Core data/scenarios.
 */
data class TacticalFacility(
    val id: String,
    val name: String,
    val type: FacilityType,
    val latitude: Double,
    val longitude: Double,
    val status: String = "functional",
    val capacity: Int? = null,
    val currentOccupancy: Int? = null,
    val availableBeds: Int? = null,
    val specialization: String? = null,
    val foodStockDays: Int? = null,
    val waterSupply: String? = null,
    val zoneId: String? = null
) {
    val occupancyPercentage: Int?
        get() {
            val cap = capacity ?: return null
            val occ = currentOccupancy ?: return null
            return if (cap > 0) ((occ.toDouble() / cap) * 100).toInt() else null
        }
}
