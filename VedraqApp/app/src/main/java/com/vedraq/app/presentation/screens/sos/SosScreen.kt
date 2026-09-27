package com.vedraq.app.presentation.screens.sos

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vedraq.app.domain.model.SosStatus
import com.vedraq.app.domain.repository.SosRepository
import com.vedraq.app.presentation.components.SosTriggerButton
import com.vedraq.app.core.location.LocationClient
import com.vedraq.app.presentation.components.VedraqBottomBar
import com.vedraq.app.presentation.components.VedraqTopBar
import com.vedraq.app.presentation.navigation.VedraqDestinations
import com.vedraq.app.ui.theme.VedraqAmber
import com.vedraq.app.ui.theme.VedraqGreen
import com.vedraq.app.ui.theme.VedraqRed
import kotlinx.coroutines.launch

@Composable
fun SosScreen(
    sosRepository: SosRepository,
    locationClient: LocationClient? = null,
    onNavigateBack: () -> Unit,
    onNavigateToRoute: (String) -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val activeBeacon by sosRepository.observeActiveBeacon().collectAsState(initial = null)
    val isBeaconActive = activeBeacon != null

    Scaffold(
        topBar = {
            VedraqTopBar(
                title = "Emergency SOS",
                canNavigateBack = true,
                onNavigateBack = onNavigateBack,
                showSystemStatus = false
            )
        },
        bottomBar = {
            VedraqBottomBar(
                currentRoute = VedraqDestinations.SOS,
                onNavigateToRoute = onNavigateToRoute
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // Warning Notice
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = if (isBeaconActive) VedraqRed.copy(alpha = 0.15f) else MaterialTheme.colorScheme.surfaceVariant
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = if (isBeaconActive) Icons.Default.CrisisAlert else Icons.Default.Warning,
                        contentDescription = null,
                        tint = if (isBeaconActive) VedraqRed else VedraqAmber,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = if (isBeaconActive) {
                            "EMERGENCY BEACON ACTIVE: Transmitting live coordinates to local operations desk."
                        } else {
                            "Use in life-threatening scenarios. Activating immediately alerts emergency coordinators."
                        },
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium,
                        color = MaterialTheme.colorScheme.onSurface,
                        lineHeight = 16.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Big Central SOS Panic Button
            SosTriggerButton(
                isPulsing = isBeaconActive,
                onClick = {
                    coroutineScope.launch {
                        if (!isBeaconActive) {
                            val loc = locationClient?.getCurrentLocation()
                            val lat = loc?.latitude ?: 25.3150
                            val lon = loc?.longitude ?: 83.0050
                            val acc = loc?.accuracyMeters ?: 4.0f
                            sosRepository.triggerSos(
                                latitude = lat,
                                longitude = lon,
                                accuracyMeters = acc,
                                notes = "Panic beacon triggered from field application."
                            )
                        }
                    }
                }
            )

            Spacer(modifier = Modifier.height(28.dp))

            Text(
                text = if (isBeaconActive) "BEACON BROADCASTING" else "TAP TO ACTIVATE SOS",
                fontSize = 18.sp,
                fontWeight = FontWeight.Black,
                letterSpacing = 1.5.sp,
                color = if (isBeaconActive) VedraqRed else MaterialTheme.colorScheme.onBackground
            )

            Text(
                text = if (isBeaconActive) "Broadcasting GPS fix & emergency medical telemetry to VEDRAQ Core" else "Press once to broadcast your position to nearby responders and VEDRAQ Core",
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp)
            )

            // Active Beacon Telemetry Details
            AnimatedVisibility(visible = isBeaconActive) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 16.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(MaterialTheme.colorScheme.surfaceVariant)
                        .border(1.dp, VedraqRed.copy(alpha = 0.5f), RoundedCornerShape(12.dp))
                        .padding(16.dp)
                ) {
                    Text(
                        text = "LIVE TELEMETRY STREAM",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = VedraqRed,
                        letterSpacing = 1.sp
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    val telemetryCoords = activeBeacon?.let {
                        String.format(java.util.Locale.US, "Coordinates: %.4f° N, %.4f° E (±%.1fm)", it.latitude, it.longitude, it.accuracyMeters)
                    } ?: "Coordinates: Acquiring GPS..."
                    Text(
                        text = telemetryCoords,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = "Status: ${activeBeacon?.status?.displayName ?: "Broadcasting"}",
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(12.dp))

                    Button(
                        onClick = {
                            coroutineScope.launch {
                                activeBeacon?.let { sosRepository.cancelSos(it.beaconId) }
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.surface,
                            contentColor = MaterialTheme.colorScheme.error
                        ),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Icon(Icons.Default.Cancel, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("CANCEL SOS BEACON", fontWeight = FontWeight.Bold, fontSize = 12.sp)
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Direct Emergency Helplines
            Column(
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = "EMERGENCY HOTLINES",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                HelplineCard(label = "National Emergency Services", number = "112 / 911")
                Spacer(modifier = Modifier.height(8.dp))
                HelplineCard(label = "Disaster Management Authority", number = "1078")
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun HelplineCard(label: String, number: String) {
    Card(
        shape = RoundedCornerShape(10.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(text = label, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.onSurface)
                Text(text = number, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            }
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .size(36.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f))
            ) {
                Icon(
                    imageVector = Icons.Default.Call,
                    contentDescription = "Call",
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}
