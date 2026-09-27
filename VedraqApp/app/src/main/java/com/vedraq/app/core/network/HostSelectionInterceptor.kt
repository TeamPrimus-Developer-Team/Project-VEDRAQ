package com.vedraq.app.core.network

import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.Interceptor
import okhttp3.Response

/**
 * OkHttp Interceptor that dynamically routes requests to the active VEDRAQ Core base URL
 * configured in [NetworkConfig]. Enables hot-swapping server IP/host/port without restarting.
 */
class HostSelectionInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var request = chain.request()
        val targetBaseUrl = NetworkConfig.getBaseUrl().toHttpUrlOrNull()

        if (targetBaseUrl != null) {
            val newUrl = request.url.newBuilder()
                .scheme(targetBaseUrl.scheme)
                .host(targetBaseUrl.host)
                .port(targetBaseUrl.port)
                .build()
            request = request.newBuilder().url(newUrl).build()
        }

        return chain.proceed(request)
    }
}
