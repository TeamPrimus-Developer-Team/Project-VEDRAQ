package com.vedraq.app.data.repository

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.EmergencyContact
import com.vedraq.app.domain.model.UserProfile
import com.vedraq.app.domain.model.UserRole
import com.vedraq.app.domain.repository.UserRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class UserRepositoryImpl : UserRepository {

    private val userState = MutableStateFlow<UserProfile?>(
        UserProfile(
            id = "USR-7821",
            fullName = "Alex Mercer",
            email = "a.mercer@vedraq-response.net",
            phoneNumber = "+1 (555) 019-2834",
            role = UserRole.FIRST_RESPONDER,
            bloodType = "O+",
            emergencyContacts = listOf(
                EmergencyContact("Sarah Mercer", "Spouse", "+1 (555) 019-2835"),
                EmergencyContact("Sector Operations Desk", "Command", "+1 (800) 555-HELP")
            ),
            responderBadgeId = "RESP-ALPHA-04"
        )
    )

    override fun getCurrentUser(): Flow<UserProfile?> {
        return userState.asStateFlow()
    }

    override suspend fun updateProfile(profile: UserProfile): Resource<UserProfile> {
        userState.value = profile
        return Resource.Success(profile)
    }

    override suspend fun authenticate(
        responderIdOrEmail: String,
        secretKey: String
    ): Resource<UserProfile> {
        val user = userState.value ?: UserProfile(
            id = "USR-AUTH-01",
            fullName = responderIdOrEmail.substringBefore("@"),
            email = responderIdOrEmail,
            phoneNumber = "+1 (555) 000-0000",
            role = UserRole.FIRST_RESPONDER
        )
        userState.value = user
        return Resource.Success(user)
    }

    override suspend fun logout(): Resource<Unit> {
        userState.value = null
        return Resource.Success(Unit)
    }
}
