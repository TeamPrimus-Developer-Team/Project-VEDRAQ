package com.vedraq.app.domain.model

data class DisasterAlert(
    val id: String,
    val title: String,
    val summary: String,
    val instructions: String,
    val severity: SeverityLevel,
    val disasterType: DisasterType,
    val affectedRegion: String,
    val radiusKilometers: Double,
    val issuedAtTimestamp: Long,
    val expiresAtTimestamp: Long? = null,
    val isEvacuationMandatory: Boolean = false,
    val issuingAuthority: String = "VEDRAQ Emergency Operations Center"
)
