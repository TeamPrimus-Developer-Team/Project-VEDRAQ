package com.vedraq.app.core.network

import kotlinx.coroutines.flow.Flow

/**
 * Interface for observing real-time network connectivity.
 * Essential for offline-first emergency reporting and queue synchronization.
 */
interface ConnectivityObserver {
    fun observe(): Flow<Status>

    enum class Status {
        Available,
        Unavailable,
        Losing,
        Lost
    }
}
