package com.vedraq.app.core.network

/**
 * Generic wrapper for network operations.
 * Prepared for future Retrofit/OkHttp integration with VEDRAQ Core.
 */
sealed class ApiResult<out T> {
    data class Success<out T>(val data: T) : ApiResult<T>()
    data class Error(val message: String, val code: Int? = null, val cause: Throwable? = null) : ApiResult<Nothing>()
    object Loading : ApiResult<Nothing>()
}
