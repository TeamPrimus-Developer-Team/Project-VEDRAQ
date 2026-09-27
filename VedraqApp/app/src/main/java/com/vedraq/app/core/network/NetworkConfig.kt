package com.vedraq.app.core.network

import android.content.Context
import android.content.SharedPreferences
import com.vedraq.app.BuildConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

/**
 * Single source of truth for VEDRAQ Core Gateway base URL configuration.
 *
 * Defaults to [BuildConfig.VEDRAQ_CORE_BASE_URL] (configured in gradle.properties).
 * Supports dynamic runtime URL modification for connecting to MacBook/LAN IP without rebuild.
 */
object NetworkConfig {

    private const val PREFS_NAME = "vedraq_network_config"
    private const val KEY_CUSTOM_BASE_URL = "custom_base_url"

    private var sharedPreferences: SharedPreferences? = null

    private val _baseUrlState = MutableStateFlow(normalizeUrl(BuildConfig.VEDRAQ_CORE_BASE_URL))
    val baseUrlState: StateFlow<String> = _baseUrlState.asStateFlow()

    /**
     * Initialize with application context to load persisted base URL override if present.
     */
    fun init(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        sharedPreferences = prefs
        val savedUrl = prefs.getString(KEY_CUSTOM_BASE_URL, null)
        if (!savedUrl.isNullOrBlank()) {
            _baseUrlState.value = normalizeUrl(savedUrl)
        }
    }

    /**
     * Get the currently active base URL.
     */
    fun getBaseUrl(): String = _baseUrlState.value

    /**
     * Set a new base URL dynamically at runtime (e.g. from developer/profile settings).
     * Automatically normalizes protocol (http://) and trailing slash (/).
     */
    fun setBaseUrl(newUrl: String): Boolean {
        val normalized = normalizeUrl(newUrl)
        val httpUrl = normalized.toHttpUrlOrNull() ?: return false
        _baseUrlState.value = normalized
        sharedPreferences?.edit()?.putString(KEY_CUSTOM_BASE_URL, normalized)?.apply()
        return true
    }

    /**
     * Reset base URL back to default build-time configuration.
     */
    fun resetToDefault() {
        val defaultUrl = normalizeUrl(BuildConfig.VEDRAQ_CORE_BASE_URL)
        _baseUrlState.value = defaultUrl
        sharedPreferences?.edit()?.remove(KEY_CUSTOM_BASE_URL)?.apply()
    }

    fun normalizeUrl(rawUrl: String): String {
        var url = rawUrl.trim()
        if (!url.startsWith("http://", ignoreCase = true) && !url.startsWith("https://", ignoreCase = true)) {
            url = "http://$url"
        }
        if (!url.endsWith("/")) {
            url = "$url/"
        }
        return url
    }
}
