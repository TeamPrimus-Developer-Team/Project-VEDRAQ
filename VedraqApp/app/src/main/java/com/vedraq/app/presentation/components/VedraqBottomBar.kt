package com.vedraq.app.presentation.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vedraq.app.presentation.navigation.VedraqDestinations
import com.vedraq.app.ui.theme.VedraqRed

data class BottomNavItem(
    val route: String,
    val title: String,
    val icon: ImageVector,
    val isEmergencyAction: Boolean = false,
    val badgeCount: Int = 0
)

@Composable
fun VedraqBottomBar(
    currentRoute: String?,
    onNavigateToRoute: (String) -> Unit
) {
    val items = listOf(
        BottomNavItem(VedraqDestinations.HOME, "Home", Icons.Default.Home),
        BottomNavItem(VedraqDestinations.ALERTS, "Alerts", Icons.Default.Notifications, badgeCount = 2),
        BottomNavItem(VedraqDestinations.SOS, "SOS", Icons.Default.Warning, isEmergencyAction = true),
        BottomNavItem(VedraqDestinations.MAP, "Map", Icons.Default.LocationOn),
        BottomNavItem(VedraqDestinations.PROFILE, "Profile", Icons.Default.Person)
    )

    NavigationBar(
        containerColor = MaterialTheme.colorScheme.surface,
        tonalElevation = 8.dp
    ) {
        items.forEach { item ->
            val isSelected = currentRoute == item.route

            if (item.isEmergencyAction) {
                NavigationBarItem(
                    selected = isSelected,
                    onClick = { onNavigateToRoute(item.route) },
                    icon = {
                        Box(
                            contentAlignment = Alignment.Center,
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(VedraqRed)
                                .border(1.dp, Color.White.copy(alpha = 0.6f), CircleShape)
                        ) {
                            Text(
                                text = "SOS",
                                color = Color.White,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.ExtraBold
                            )
                        }
                    },
                    label = {
                        Text(
                            text = item.title,
                            fontWeight = FontWeight.Bold,
                            color = VedraqRed,
                            fontSize = 11.sp
                        )
                    },
                    colors = NavigationBarItemDefaults.colors(
                        indicatorColor = Color.Transparent
                    )
                )
            } else {
                NavigationBarItem(
                    selected = isSelected,
                    onClick = { onNavigateToRoute(item.route) },
                    icon = {
                        if (item.badgeCount > 0) {
                            BadgedBox(
                                badge = {
                                    Badge(
                                        containerColor = VedraqRed,
                                        contentColor = Color.White
                                    ) {
                                        Text(item.badgeCount.toString())
                                    }
                                }
                            ) {
                                Icon(
                                    imageVector = item.icon,
                                    contentDescription = item.title
                                )
                            }
                        } else {
                            Icon(
                                imageVector = item.icon,
                                contentDescription = item.title
                            )
                        }
                    },
                    label = {
                        Text(
                            text = item.title,
                            fontSize = 11.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                        )
                    },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = MaterialTheme.colorScheme.primary,
                        selectedTextColor = MaterialTheme.colorScheme.primary,
                        unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        indicatorColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)
                    )
                )
            }
        }
    }
}
