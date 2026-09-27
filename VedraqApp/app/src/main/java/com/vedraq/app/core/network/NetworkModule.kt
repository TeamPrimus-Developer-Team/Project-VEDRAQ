package com.vedraq.app.core.network

import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import com.vedraq.app.data.remote.VedraqApiService
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Singleton networking factory providing configured Retrofit, OkHttp, and Moshi instances.
 * Routes requests dynamically to the active VEDRAQ Core instance configured via [NetworkConfig].
 */
object NetworkModule {

    val moshi: Moshi by lazy {
        Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()
    }

    fun createOkHttpClient(includeHostInterceptor: Boolean = true): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val builder = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)

        if (includeHostInterceptor) {
            builder.addInterceptor(HostSelectionInterceptor())
        }

        return builder.build()
    }

    fun createApiService(
        baseUrl: String? = null,
        client: OkHttpClient? = null
    ): VedraqApiService {
        val activeBaseUrl = baseUrl ?: NetworkConfig.getBaseUrl()
        val normalizedBaseUrl = if (activeBaseUrl.endsWith("/")) activeBaseUrl else "$activeBaseUrl/"
        // If baseUrl is explicitly provided (e.g. in MockWebServer unit tests), do not hijack with HostSelectionInterceptor
        val resolvedClient = client ?: createOkHttpClient(includeHostInterceptor = (baseUrl == null))

        return Retrofit.Builder()
            .baseUrl(normalizedBaseUrl)
            .client(resolvedClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(VedraqApiService::class.java)
    }

    val apiService: VedraqApiService by lazy {
        createApiService()
    }

    /**
     * Diagnostic health check to verify VEDRAQ Core reachability.
     */
    suspend fun checkCoreHealth(): ApiResult<Map<String, Any>> {
        return try {
            val response = apiService.checkHealth()
            if (response.isSuccessful && response.body() != null) {
                ApiResult.Success(response.body()!!)
            } else {
                ApiResult.Error("VEDRAQ Core returned HTTP ${response.code()}", code = response.code())
            }
        } catch (e: Exception) {
            ApiResult.Error(
                message = e.localizedMessage ?: "Connection refused: VEDRAQ Core unavailable",
                cause = e
            )
        }
    }
}
