package com.vedraq.app.domain.repository

import com.vedraq.app.core.util.Resource
import com.vedraq.app.domain.model.UserProfile
import kotlinx.coroutines.flow.Flow

/**
 * Interface contract for responder/citizen identity and emergency contacts.
 */
interface UserRepository {
    fun getCurrentUser(): Flow<UserProfile?>
    suspend fun updateProfile(profile: UserProfile): Resource<UserProfile>
    suspend fun authenticate(responderIdOrEmail: String, secretKey: String): Resource<UserProfile>
    suspend fun logout(): Resource<Unit>
}
