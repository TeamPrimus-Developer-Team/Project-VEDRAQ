package com.vedraq.app.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = VedraqRedLight,
    onPrimary = TacticalDarkBackground,
    primaryContainer = VedraqRedDark,
    onPrimaryContainer = TacticalDarkTextPrimary,
    secondary = VedraqBlueLight,
    onSecondary = TacticalDarkBackground,
    secondaryContainer = VedraqBlueDark,
    onSecondaryContainer = TacticalDarkTextPrimary,
    tertiary = VedraqAmberLight,
    onTertiary = TacticalDarkBackground,
    background = TacticalDarkBackground,
    onBackground = TacticalDarkTextPrimary,
    surface = TacticalDarkSurface,
    onSurface = TacticalDarkTextPrimary,
    surfaceVariant = TacticalDarkCard,
    onSurfaceVariant = TacticalDarkTextSecondary,
    outline = TacticalDarkBorder
)

private val LightColorScheme = lightColorScheme(
    primary = VedraqRed,
    onPrimary = OperationsLightSurface,
    primaryContainer = VedraqRedLight.copy(alpha = 0.2f),
    onPrimaryContainer = VedraqRedDark,
    secondary = VedraqBlue,
    onSecondary = OperationsLightSurface,
    secondaryContainer = VedraqBlueLight.copy(alpha = 0.2f),
    onSecondaryContainer = VedraqBlueDark,
    tertiary = VedraqAmber,
    onTertiary = OperationsLightSurface,
    background = OperationsLightBackground,
    onBackground = OperationsLightTextPrimary,
    surface = OperationsLightSurface,
    onSurface = OperationsLightTextPrimary,
    surfaceVariant = OperationsLightCard,
    onSurfaceVariant = OperationsLightTextSecondary,
    outline = OperationsLightBorder
)

@Composable
fun VedraqTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as? Activity)?.window
            if (window != null) {
                WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
            }
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
