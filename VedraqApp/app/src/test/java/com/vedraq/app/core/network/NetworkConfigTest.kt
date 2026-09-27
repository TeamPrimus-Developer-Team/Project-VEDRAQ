package com.vedraq.app.core.network

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class NetworkConfigTest {

    @Before
    fun setUp() {
        NetworkConfig.resetToDefault()
    }

    @Test
    fun test_default_base_url_is_configured() {
        val defaultUrl = NetworkConfig.getBaseUrl()
        assertTrue(defaultUrl.startsWith("http://") || defaultUrl.startsWith("https://"))
        assertTrue(defaultUrl.endsWith("/"))
        assertTrue(defaultUrl.contains("8001"))
    }

    @Test
    fun test_normalize_url_adds_protocol_and_trailing_slash() {
        assertEquals("http://192.168.1.50:8001/", NetworkConfig.normalizeUrl("192.168.1.50:8001"))
        assertEquals("http://192.168.1.50:8001/", NetworkConfig.normalizeUrl("http://192.168.1.50:8001"))
        assertEquals("https://vedraq.internal:8001/", NetworkConfig.normalizeUrl("https://vedraq.internal:8001"))
        assertEquals("http://10.0.0.1:8001/", NetworkConfig.normalizeUrl("  10.0.0.1:8001/  "))
    }

    @Test
    fun test_set_and_reset_base_url() {
        val success = NetworkConfig.setBaseUrl("192.168.0.120:8001")
        assertTrue(success)
        assertEquals("http://192.168.0.120:8001/", NetworkConfig.getBaseUrl())

        NetworkConfig.resetToDefault()
        assertTrue(NetworkConfig.getBaseUrl().contains("8001"))
    }

    @Test
    fun test_invalid_url_returns_false() {
        val success = NetworkConfig.setBaseUrl("   ")
        assertFalse(success)
    }
}
