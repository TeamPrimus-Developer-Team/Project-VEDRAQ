package com.vedraq.app.domain.model

data class SosBeacon(
    val beaconId: String,
    val userId: String,
    val latitude: Double,
    val longitude: Double,
    val accuracyMeters: Float,
    val status: SosStatus,
    val triggeredAtTimestamp: Long = System.currentTimeMillis(),
    val batteryPercentage: Int? = null,
    val medicalNotes: String? = null,
    val activeChannel: String = "GPS_CELLULAR"
)
