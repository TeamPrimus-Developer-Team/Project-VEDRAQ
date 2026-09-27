package com.vedraq.app.presentation.screens.profile

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
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Bloodtype
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Dns
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Storage
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vedraq.app.core.network.ApiResult
import com.vedraq.app.core.network.NetworkConfig
import com.vedraq.app.core.network.NetworkModule
import com.vedraq.app.domain.repository.IncidentRepository
import com.vedraq.app.domain.repository.UserRepository
import com.vedraq.app.presentation.components.VedraqBottomBar
import com.vedraq.app.presentation.components.VedraqTopBar
import com.vedraq.app.presentation.navigation.VedraqDestinations
import com.vedraq.app.ui.theme.VedraqAmber
import com.vedraq.app.ui.theme.VedraqGreen
import com.vedraq.app.ui.theme.VedraqRed
import kotlinx.coroutines.launch

@Composable
fun ProfileScreen(
    userRepository: UserRepository,
    incidentRepository: IncidentRepository? = null,
    onNavigateBack: () -> Unit,
    onNavigateToRoute: (String) -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val user by userRepository.getCurrentUser().collectAsState(initial = null)
    val incidents by (incidentRepository?.getLocalIncidents()?.collectAsState(initial = emptyList())
        ?: remember { mutableStateOf(emptyList()) })

    val pendingCount = incidents.count { !it.isSyncedWithCore }
    val currentBaseUrl by NetworkConfig.baseUrlState.collectAsState()

    var isEditingUrl by remember { mutableStateOf(false) }
    var editedUrlText by remember(currentBaseUrl) { mutableStateOf(currentBaseUrl) }
    var pingStatusText by remember { mutableStateOf<String?>(null) }
    var isPinging by remember { mutableStateOf(false) }
    var isPingSuccess by remember { mutableStateOf<Boolean?>(null) }

    var isSyncing by remember { mutableStateOf(false) }
    var syncResultText by remember { mutableStateOf<String?>(null) }

    Scaffold(
        topBar = {
            VedraqTopBar(
                title = "Responder Profile",
                canNavigateBack = true,
                onNavigateBack = onNavigateBack,
                showSystemStatus = true
            )
        },
        bottomBar = {
            VedraqBottomBar(
                currentRoute = VedraqDestinations.PROFILE,
                onNavigateToRoute = onNavigateToRoute
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState())
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // User Profile Card
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        contentAlignment = Alignment.Center,
                        modifier = Modifier
                            .size(56.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f))
                            .border(2.dp, MaterialTheme.colorScheme.primary, CircleShape)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Person,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(32.dp)
                        )
                    }

                    Spacer(modifier = Modifier.width(14.dp))

                    Column {
                        Text(
                            text = user?.fullName ?: "Alex Mercer",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            text = user?.role?.name ?: "FIRST_RESPONDER",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary,
                            letterSpacing = 0.8.sp
                        )
                        Text(
                            text = user?.email ?: "a.mercer@vedraq-response.net",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Emergency Medical & Responder Info
            Text(
                text = "RESPONDER & MEDICAL CREDENTIALS",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))

            ProfileDetailRow(
                icon = Icons.Default.Badge,
                label = "Operational Badge ID",
                value = user?.responderBadgeId ?: "RESP-ALPHA-04"
            )
            ProfileDetailRow(
                icon = Icons.Default.Bloodtype,
                label = "Blood Type",
                value = user?.bloodType ?: "O+"
            )
            ProfileDetailRow(
                icon = Icons.Default.Phone,
                label = "Contact Phone",
                value = user?.phoneNumber ?: "+1 (555) 019-2834"
            )

            Spacer(modifier = Modifier.height(20.dp))

            // VEDRAQ Core Gateway Config
            Text(
                text = "VEDRAQ CORE GATEWAY CONFIGURATION",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))

            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Target Core Server URL:",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        IconButton(
                            onClick = { isEditingUrl = !isEditingUrl },
                            modifier = Modifier.size(24.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Edit,
                                contentDescription = "Edit Base URL",
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }

                    if (isEditingUrl) {
                        Spacer(modifier = Modifier.height(6.dp))
                        OutlinedTextField(
                            value = editedUrlText,
                            onValueChange = { editedUrlText = it },
                            label = { Text("Core Base URL (e.g. http://192.168.1.100:8001/)") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(
                                onClick = {
                                    NetworkConfig.setBaseUrl(editedUrlText)
                                    isEditingUrl = false
                                },
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text("Save URL", fontSize = 12.sp)
                            }
                            OutlinedButton(
                                onClick = {
                                    NetworkConfig.resetToDefault()
                                    isEditingUrl = false
                                },
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text("Reset Default", fontSize = 12.sp)
                            }
                        }
                    } else {
                        Text(
                            text = currentBaseUrl,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        OutlinedButton(
                            onClick = {
                                isPinging = true
                                pingStatusText = "Pinging VEDRAQ Core..."
                                isPingSuccess = null
                                coroutineScope.launch {
                                    val result = NetworkModule.checkCoreHealth()
                                    isPinging = false
                                    when (result) {
                                        is ApiResult.Success -> {
                                            isPingSuccess = true
                                            pingStatusText = "Core Online (Service: ${result.data["service"]}, Routing: ${result.data["routing_engine"]})"
                                        }
                                        is ApiResult.Error -> {
                                            isPingSuccess = false
                                            pingStatusText = "Core Offline: ${result.message}"
                                        }
                                        else -> Unit
                                    }
                                }
                            },
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            if (isPinging) {
                                CircularProgressIndicator(modifier = Modifier.size(14.dp), strokeWidth = 2.dp)
                                Spacer(modifier = Modifier.width(6.dp))
                            } else {
                                Icon(Icons.Default.Dns, contentDescription = null, modifier = Modifier.size(14.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                            }
                            Text("Test Core Connection", fontSize = 12.sp)
                        }

                        if (isPingSuccess != null) {
                            Text(
                                text = if (isPingSuccess == true) "ONLINE" else "OFFLINE",
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                color = if (isPingSuccess == true) VedraqGreen else VedraqRed
                            )
                        }
                    }

                    if (pingStatusText != null) {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = pingStatusText!!,
                            fontSize = 11.sp,
                            color = if (isPingSuccess == true) VedraqGreen else VedraqRed,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Offline Cache & Data Management
            Text(
                text = "OFFLINE STORAGE & QUEUE",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))

            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Cached Reports Queue", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
                        Text(
                            text = if (pendingCount > 0) "$pendingCount Pending Sync" else "${incidents.size} Total (Synced)",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (pendingCount > 0) VedraqAmber else VedraqGreen
                        )
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Varanasi Scenario Baseline", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
                        Text("Active (Port 8001)", fontSize = 13.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                    }

                    if (pendingCount > 0 || incidentRepository != null) {
                        Spacer(modifier = Modifier.height(10.dp))
                        Button(
                            onClick = {
                                isSyncing = true
                                syncResultText = "Synchronizing with VEDRAQ Core..."
                                coroutineScope.launch {
                                    val result = incidentRepository?.syncPendingIncidents()
                                    isSyncing = false
                                    syncResultText = when (result) {
                                        is com.vedraq.app.core.util.Resource.Success -> "Synced ${result.data} pending records to Core successfully!"
                                        is com.vedraq.app.core.util.Resource.Error -> "Sync failed: ${result.message}"
                                        null -> "No repository available"
                                        else -> "Sync completed"
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                        ) {
                            if (isSyncing) {
                                CircularProgressIndicator(modifier = Modifier.size(16.dp), color = Color.White, strokeWidth = 2.dp)
                                Spacer(modifier = Modifier.width(8.dp))
                            } else {
                                Icon(Icons.Default.Sync, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                            }
                            Text("SYNC OFFLINE QUEUE NOW", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }

                        if (syncResultText != null) {
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = syncResultText!!,
                                fontSize = 11.sp,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            OutlinedButton(
                onClick = { /* Simulated logout */ },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(Icons.Default.Lock, contentDescription = null, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("DISCONNECT SESSION", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.error)
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun ProfileDetailRow(icon: ImageVector, label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.width(10.dp))
            Text(
                text = label,
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        Text(
            text = value,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}
