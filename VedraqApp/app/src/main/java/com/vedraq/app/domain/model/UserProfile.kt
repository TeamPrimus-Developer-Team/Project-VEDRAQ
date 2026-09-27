package com.vedraq.app.domain.model

data class UserProfile(
    val id: String,
    val fullName: String,
    val email: String,
    val phoneNumber: String,
    val role: UserRole = UserRole.CITIZEN,
    val bloodType: String? = null,
    val emergencyContacts: List<EmergencyContact> = emptyList(),
    val responderBadgeId: String? = null
)

data class EmergencyContact(
    val name: String,
    val relation: String,
    val phoneNumber: String
)

enum class UserRole {
    CITIZEN,
    FIRST_RESPONDER,
    DISASTER_COORDINATOR,
    MEDICAL_STAFF
}
