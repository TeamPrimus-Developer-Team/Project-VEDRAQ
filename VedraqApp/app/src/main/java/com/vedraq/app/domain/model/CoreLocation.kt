package com.vedraq.app.domain.model

/**
 * Authoritative location model representing Core scenario centers and tactical zones.
 * Directly mirrors the GPS coordinates and zones defined in data/scenarios.
 */
data class CoreLocation(
    val id: String,
    val name: String,
    val region: String,
    val latitude: Double,
    val longitude: Double,
    val isScenarioCenter: Boolean = false,
    val associatedZoneId: String? = null,
    val type: String = "TACTICAL_ZONE",
    val damagePercentage: Int? = null,
    val classification: String? = null,
    val roadAccessibility: String? = null,
    val population: Int? = null
)

/**
 * Baseline catalog of scenario locations and tactical zones.
 * Used as a resilient offline fallback when VEDRAQ Core backend is unreachable.
 * Production runtime flow retrieves authoritative live data directly from Core API.
 */
object CoreLocations {
    // ── Primary Cities & Scenario Centers ───────────────────────────────────
    val VARANASI_CENTRAL = CoreLocation(
        id = "varanasi_center",
        name = "Varanasi (Central)",
        region = "Uttar Pradesh, India",
        latitude = 25.3150,
        longitude = 83.0650,
        isScenarioCenter = true,
        type = "SCENARIO_CENTER"
    )

    val NEPAL_CENTRAL = CoreLocation(
        id = "nepal_center",
        name = "Nepal (Alpine)",
        region = "Bagmati & Sindhupalchok, Nepal",
        latitude = 27.7500,
        longitude = 85.5500,
        isScenarioCenter = true,
        type = "SCENARIO_CENTER"
    )

    // ── Nepal Scenario Locations (for Nepal scenario isolation) ──────────────
    val DHULIKHEL = CoreLocation(
        id = "dhulikhel",
        name = "Dhulikhel",
        region = "Bagmati, Nepal",
        latitude = 27.6180,
        longitude = 85.5540,
        associatedZoneId = "N07"
    )

    val BANEPA = CoreLocation(
        id = "banepa",
        name = "Banepa",
        region = "Bagmati, Nepal",
        latitude = 27.6320,
        longitude = 85.5240,
        associatedZoneId = "N08"
    )

    val MELAMCHI = CoreLocation(
        id = "melamchi",
        name = "Melamchi",
        region = "Sindhupalchok, Nepal",
        latitude = 27.8320,
        longitude = 85.5800,
        associatedZoneId = "N01"
    )

    val BHAKTAPUR = CoreLocation(
        id = "bhaktapur",
        name = "Bhaktapur",
        region = "Bagmati, Nepal",
        latitude = 27.6710,
        longitude = 85.4280,
        associatedZoneId = "N06"
    )

    val SINDHUPALCHOK = CoreLocation(
        id = "sindhupalchok",
        name = "Sindhupalchok",
        region = "Sindhupalchok, Nepal",
        latitude = 27.7710,
        longitude = 85.7100,
        associatedZoneId = "N02"
    )

    // ── Complete 15 Varanasi Tactical Zones (Authoritative dataset) ─────────
    val RAMPUR_TANDA = CoreLocation(
        id = "Z01",
        name = "Rampur Tanda",
        region = "Varanasi",
        latitude = 25.3120,
        longitude = 83.0120,
        associatedZoneId = "Z01",
        damagePercentage = 62,
        classification = "CRITICAL",
        roadAccessibility = "blocked",
        population = 4200
    )

    val CHANDPUR = CoreLocation(
        id = "Z02",
        name = "Chandpur",
        region = "Varanasi",
        latitude = 25.3580,
        longitude = 83.0740,
        associatedZoneId = "Z02",
        damagePercentage = 70,
        classification = "HIGH",
        roadAccessibility = "open",
        population = 8000
    )

    val GOVINDPUR = CoreLocation(
        id = "Z03",
        name = "Govindpur",
        region = "Varanasi",
        latitude = 25.2890,
        longitude = 83.0510,
        associatedZoneId = "Z03",
        damagePercentage = 78,
        classification = "CRITICAL",
        roadAccessibility = "degraded",
        population = 2100
    )

    val BHELPUR = CoreLocation(
        id = "Z04",
        name = "Bhelpur",
        region = "Varanasi",
        latitude = 25.3410,
        longitude = 83.0980,
        associatedZoneId = "Z04",
        damagePercentage = 55,
        classification = "HIGH",
        roadAccessibility = "open",
        population = 6500
    )

    val NARAYANPUR_KALAN = CoreLocation(
        id = "Z05",
        name = "Narayanpur Kalan",
        region = "Varanasi",
        latitude = 25.2680,
        longitude = 83.0310,
        associatedZoneId = "Z05",
        damagePercentage = 85,
        classification = "CRITICAL",
        roadAccessibility = "blocked",
        population = 1500
    )

    val DURGAKUND = CoreLocation(
        id = "Z06",
        name = "Durgakund Colony",
        region = "Varanasi",
        latitude = 25.3210,
        longitude = 83.0030,
        associatedZoneId = "Z06",
        damagePercentage = 48,
        classification = "MODERATE",
        roadAccessibility = "open",
        population = 5200
    )

    val SIKANDARPUR = CoreLocation(
        id = "Z07",
        name = "Sikandarpur",
        region = "Varanasi",
        latitude = 25.3020,
        longitude = 83.0890,
        associatedZoneId = "Z07",
        damagePercentage = 67,
        classification = "HIGH",
        roadAccessibility = "degraded",
        population = 4800
    )

    val LAHARTARA = CoreLocation(
        id = "Z08",
        name = "Lahartara",
        region = "Varanasi",
        latitude = 25.3750,
        longitude = 83.0420,
        associatedZoneId = "Z08",
        damagePercentage = 38,
        classification = "MODERATE",
        roadAccessibility = "open",
        population = 7100
    )

    val PHULPUR_KHAS = CoreLocation(
        id = "Z09",
        name = "Phulpur Khas",
        region = "Varanasi",
        latitude = 25.2530,
        longitude = 83.0660,
        associatedZoneId = "Z09",
        damagePercentage = 73,
        classification = "CRITICAL",
        roadAccessibility = "degraded",
        population = 3100
    )

    val MADANPUR_KHURD = CoreLocation(
        id = "Z10",
        name = "Madanpur Khurd",
        region = "Varanasi",
        latitude = 25.3340,
        longitude = 83.1250,
        associatedZoneId = "Z10",
        damagePercentage = 59,
        classification = "HIGH",
        roadAccessibility = "open",
        population = 5800
    )

    val KHAJURI_KHAS = CoreLocation(
        id = "Z11",
        name = "Khajuri Khas",
        region = "Varanasi",
        latitude = 25.2810,
        longitude = 83.1090,
        associatedZoneId = "Z11",
        damagePercentage = 82,
        classification = "CRITICAL",
        roadAccessibility = "degraded",
        population = 2900
    )

    val RAJPUR_MAFI = CoreLocation(
        id = "Z12",
        name = "Rajpur Mafi",
        region = "Varanasi",
        latitude = 25.3660,
        longitude = 83.1150,
        associatedZoneId = "Z12",
        damagePercentage = 42,
        classification = "SAFE",
        roadAccessibility = "open",
        population = 3600
    )

    val BARAGAON = CoreLocation(
        id = "Z13",
        name = "Baragaon",
        region = "Varanasi",
        latitude = 25.2470,
        longitude = 83.0420,
        associatedZoneId = "Z13",
        damagePercentage = 76,
        classification = "CRITICAL",
        roadAccessibility = "degraded",
        population = 2200
    )

    val CHAUKAGHAT = CoreLocation(
        id = "Z14",
        name = "Chaukaghat",
        region = "Varanasi",
        latitude = 25.3180,
        longitude = 83.0570,
        associatedZoneId = "Z14",
        damagePercentage = 52,
        classification = "HIGH",
        roadAccessibility = "open",
        population = 9500
    )

    val ASSI_GHAT = CoreLocation(
        id = "Z15",
        name = "Assi Ghat Colony",
        region = "Varanasi",
        latitude = 25.2950,
        longitude = 83.0130,
        associatedZoneId = "Z15",
        damagePercentage = 65,
        classification = "HIGH",
        roadAccessibility = "degraded",
        population = 7200
    )

    /**
     * Authoritative list of all 15 Varanasi tactical operational zones.
     */
    val VARANASI_ZONES: List<CoreLocation> = listOf(
        RAMPUR_TANDA,
        CHANDPUR,
        GOVINDPUR,
        BHELPUR,
        NARAYANPUR_KALAN,
        DURGAKUND,
        SIKANDARPUR,
        LAHARTARA,
        PHULPUR_KHAS,
        MADANPUR_KHURD,
        KHAJURI_KHAS,
        RAJPUR_MAFI,
        BARAGAON,
        CHAUKAGHAT,
        ASSI_GHAT
    )

    /**
     * Curated list of primary operational cities for fast selection.
     */
    val PRIMARY_CITIES: List<CoreLocation> = listOf(
        VARANASI_CENTRAL,
        DHULIKHEL,
        BANEPA,
        MELAMCHI,
        BHAKTAPUR,
        SINDHUPALCHOK
    )

    /**
     * Complete authoritative list of all Core scenario locations and tactical zones.
     * Guaranteed backward-compatible with existing tests.
     */
    val ALL: List<CoreLocation> = listOf(
        VARANASI_CENTRAL,
        NEPAL_CENTRAL,
        DHULIKHEL,
        BANEPA,
        MELAMCHI,
        BHAKTAPUR,
        SINDHUPALCHOK
    ) + VARANASI_ZONES

    /**
     * Strict scenario-isolated filter ensuring Varanasi UI displays only Varanasi locations.
     * Prevents cross-scenario bleeding (e.g. Nepal zones in Varanasi UI).
     */
    fun filterByScenario(locations: List<CoreLocation>, scenarioId: String = "varanasi"): List<CoreLocation> {
        val target = scenarioId.lowercase()
        return locations.filter { loc ->
            if (target == "varanasi") {
                loc.id == "varanasi_center" ||
                loc.id.startsWith("Z") ||
                loc.region.contains("Varanasi", ignoreCase = true) ||
                loc.region.contains("Uttar Pradesh", ignoreCase = true)
            } else if (target == "nepal") {
                loc.id == "nepal_center" ||
                loc.id.startsWith("N") ||
                loc.region.contains("Nepal", ignoreCase = true)
            } else {
                true
            }
        }
    }

    fun findByNameOrId(query: String): CoreLocation? {
        return ALL.firstOrNull {
            it.id.equals(query, ignoreCase = true) ||
            it.name.equals(query, ignoreCase = true) ||
            it.associatedZoneId.equals(query, ignoreCase = true)
        }
    }
}
