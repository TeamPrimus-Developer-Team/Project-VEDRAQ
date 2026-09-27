// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.compose) apply false
}

// Redirect build artifacts outside OneDrive to eliminate Windows OneDrive file-locking conflicts
allprojects {
    val buildCacheDir = File(System.getProperty("user.home"), ".vedraq_build/VedraqApp/$name")
    layout.buildDirectory.set(buildCacheDir)
}