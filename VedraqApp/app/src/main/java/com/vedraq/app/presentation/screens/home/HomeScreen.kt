package com.vedraq.app.presentation.screens.home

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AddAlert
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.ReportProblem
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vedraq.app.domain.model.Incident
import com.vedraq.app.domain.repository.IncidentRepository
import com.vedraq.app.presentation.components.EmergencyActionButton
import com.vedraq.app.presentation.components.IncidentCard
import com.vedraq.app.presentation.components.SosTriggerButton
import com.vedraq.app.presentation.components.VedraqBottomBar
import com.vedraq.app.presentation.components.VedraqTopBar
import com.vedraq.app.presentation.navigation.VedraqDestinations
import com.vedraq.app.ui.theme.VedraqAmber
import com.vedraq.app.ui.theme.VedraqBlue
import com.vedraq.app.ui.theme.VedraqGreen
import com.vedraq.app.ui.theme.VedraqRed

import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.IconButton
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import kotlinx.coroutines.launch

@Composable
fun HomeScreen(
    incidentRepository: IncidentRepository,
    onNavigateToEmergencyReport: () -> Unit,
    onNavigateToSos: () -> Unit,
    onNavigateToAlerts: () -> Unit,
    onNavigateToMap: () -> Unit,
    onNavigateToProfile: () -> Unit,
    onNavigateToRoute: (String) -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val incidents by incidentRepository.getLocalIncidents().collectAsState(initial = emptyList())
    var isRefreshing by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        incidentRepository.fetchIncidentsFromCore()
    }

    Scaffold(
        topBar = {
            VedraqTopBar(
                title = "VEDRAQ Ops",
                canNavigateBack = false,
                showSystemStatus = true,
                actions = {
                    IconButton(
                        onClick = {
                            coroutineScope.launch {
                                isRefreshing = true
                                incidentRepository.syncPendingIncidents()
                                incidentRepository.fetchIncidentsFromCore()
                                isRefreshing = false
                            }
                        }
                    ) {
                        if (isRefreshing) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.primary
                            )
                        } else {
                            Icon(
                                imageVector = Icons.Default.Refresh,
                                contentDescription = "Sync & Refresh",
                                tint = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }
            )
        },
        bottomBar = {
            VedraqBottomBar(
                currentRoute = VedraqDestinations.HOME,
                onNavigateToRoute = onNavigateToRoute
            )
        }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                Spacer(modifier = Modifier.height(8.dp))

                // Active Threat Level Banner
                ActiveThreatBanner()
            }

            // Quick Emergency Actions Section
            item {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = "EMERGENCY ACTIONS",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.2.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(10.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        ActionTile(
                            title = "REPORT INCIDENT",
                            subtitle = "Disaster / Hazard",
                            icon = Icons.Default.ReportProblem,
                            containerColor = VedraqAmber,
                            onClick = onNavigateToEmergencyReport,
                            modifier = Modifier.weight(1f)
                        )

                        ActionTile(
                            title = "PANIC SOS",
                            subtitle = "Immediate Help",
                            icon = Icons.Default.CrisisAlert,
                            containerColor = VedraqRed,
                            onClick = onNavigateToSos,
                            modifier = Modifier.weight(1f)
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        ActionTile(
                            title = "ACTIVE ALERTS",
                            subtitle = "Regional Broadcasts",
                            icon = Icons.Default.Notifications,
                            containerColor = VedraqBlue,
                            onClick = onNavigateToAlerts,
                            modifier = Modifier.weight(1f)
                        )

                        ActionTile(
                            title = "TACTICAL MAP",
                            subtitle = "Zones & Shelters",
                            icon = Icons.Default.LocationOn,
                            containerColor = MaterialTheme.colorScheme.surfaceVariant,
                            contentColor = MaterialTheme.colorScheme.onSurface,
                            onClick = onNavigateToMap,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }

            // Recent Incidents Header
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "LOCAL INCIDENTS FEED",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.2.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "${incidents.size} Logged",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            // Incidents Feed
            items(incidents) { incident ->
                IncidentCard(
                    incident = incident,
                    onClick = { /* Detail view prepared for future expansion */ }
                )
            }

            item {
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}

@Composable
private fun ActiveThreatBanner() {
    Card(
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(
            containerColor = VedraqRed.copy(alpha = 0.12f)
        ),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, VedraqRed.copy(alpha = 0.4f), RoundedCornerShape(14.dp))
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .size(42.dp)
                    .clip(CircleShape)
                    .background(VedraqRed)
            ) {
                Icon(
                    imageVector = Icons.Default.Warning,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(24.dp)
                )
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(
                    text = "SECTOR STATUS: ELEVATED RISK",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Black,
                    letterSpacing = 0.8.sp,
                    color = VedraqRed
                )
                Text(
                    text = "Active Flash Flood Advisory in Lowland River Basin. Monitor live alert channel.",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurface,
                    lineHeight = 16.sp
                )
            }
        }
    }
}

@Composable
private fun ActionTile(
    title: String,
    subtitle: String,
    icon: ImageVector,
    containerColor: Color,
    contentColor: Color = Color.White,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(containerColor)
            .clickable { onClick() }
            .padding(14.dp)
    ) {
        Column {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = contentColor,
                modifier = Modifier.size(26.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = title,
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                color = contentColor,
                letterSpacing = 0.5.sp
            )
            Text(
                text = subtitle,
                fontSize = 11.sp,
                color = contentColor.copy(alpha = 0.85f)
            )
        }
    }
}
