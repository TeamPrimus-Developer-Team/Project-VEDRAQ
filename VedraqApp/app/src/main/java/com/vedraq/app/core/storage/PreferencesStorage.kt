package com.vedraq.app.core.storage

import kotlinx.coroutines.flow.Flow

/**
 * Storage abstraction contract for user preferences, responder session,
 * and offline sync parameters.
 */
interface PreferencesStorage {
    fun getString(key: String, defaultValue: String? = null): Flow<String?>
    suspend fun setString(key: String, value: String)
    fun getBoolean(key: String, defaultValue: Boolean = false): Flow<Boolean>
    suspend fun setBoolean(key: String, value: Boolean)
    suspend fun clear()
}
