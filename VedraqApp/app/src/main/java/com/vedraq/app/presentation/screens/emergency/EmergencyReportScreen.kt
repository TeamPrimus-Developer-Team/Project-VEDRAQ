package com.vedraq.app.presentation.screens.emergency

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Report
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vedraq.app.domain.model.CoreLocations
import com.vedraq.app.domain.model.DisasterType
import com.vedraq.app.domain.model.SeverityLevel
import com.vedraq.app.presentation.components.VedraqTopBar
import com.vedraq.app.ui.theme.VedraqAmber
import com.vedraq.app.ui.theme.VedraqGreen
import com.vedraq.app.ui.theme.VedraqRed

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun EmergencyReportScreen(
    viewModel: EmergencyReportViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(uiState.submissionState) {
        when (val state = uiState.submissionState) {
            is EmergencyReportSubmissionState.ValidationError -> {
                snackbarHostState.showSnackbar(state.message)
            }
            else -> Unit
        }
    }

    Scaffold(
        topBar = {
            VedraqTopBar(
                title = "Emergency Incident Report",
                canNavigateBack = true,
                onNavigateBack = onNavigateBack,
                showSystemStatus = false
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState())
        ) {
            Spacer(modifier = Modifier.height(12.dp))

            // State-Specific Header Banner
            when (val state = uiState.submissionState) {
                is EmergencyReportSubmissionState.SubmittedToCore -> {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = VedraqGreen.copy(alpha = 0.15f)),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.5.dp, VedraqGreen, RoundedCornerShape(12.dp))
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.CheckCircle, contentDescription = null, tint = VedraqGreen, modifier = Modifier.size(24.dp))
                                Spacer(modifier = Modifier.width(10.dp))
                                Text(
                                    text = "DISPATCHED TO VEDRAQ CORE",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 14.sp,
                                    color = VedraqGreen,
                                    letterSpacing = 0.5.sp
                                )
                            }
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "Authoritative Server ID:",
                                fontSize = 11.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                text = state.serverIncidentId,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Black,
                                fontFamily = FontFamily.Monospace,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Incident has been registered in the Core store and is live on the tactical dashboard.",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            state.incident.address?.let {
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = "Incident Location: $it",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                            state.incident.nearestZoneName?.let {
                                val dist = state.incident.nearestZoneDistanceKm?.let { d -> " (${String.format(java.util.Locale.US, "%.1f", d)} km)" } ?: ""
                                Spacer(modifier = Modifier.height(2.dp))
                                Text(
                                    text = "Nearest Tactical Zone: $it$dist",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = VedraqGreen
                                )
                            }
                            Spacer(modifier = Modifier.height(12.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(
                                    onClick = onNavigateBack,
                                    colors = ButtonDefaults.buttonColors(containerColor = VedraqGreen),
                                    shape = RoundedCornerShape(8.dp),
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Text("RETURN TO OPS", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                                }
                                OutlinedButton(
                                    onClick = { viewModel.resetForm() },
                                    shape = RoundedCornerShape(8.dp),
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Text("NEW REPORT", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }

                is EmergencyReportSubmissionState.NetworkError -> {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = VedraqAmber.copy(alpha = 0.15f)),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.5.dp, VedraqAmber, RoundedCornerShape(12.dp))
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.WifiOff, contentDescription = null, tint = VedraqAmber, modifier = Modifier.size(22.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = "NETWORK UNREACHABLE — QUEUED LOCALLY",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    color = VedraqAmber
                                )
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = "Could not reach Core backend at http://10.0.2.2:8000. Report stored safely in local offline cache.",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }

                is EmergencyReportSubmissionState.ServerError -> {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = VedraqRed.copy(alpha = 0.15f)),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .border(1.5.dp, VedraqRed, RoundedCornerShape(12.dp))
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.ErrorOutline, contentDescription = null, tint = VedraqRed, modifier = Modifier.size(22.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = "CORE SERVER ERROR (${state.code})",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    color = VedraqRed
                                )
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = state.message,
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }

                else -> {
                    // System info card
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.Top
                        ) {
                            Icon(Icons.Default.Info, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(20.dp))
                            Spacer(modifier = Modifier.width(10.dp))
                            Text(
                                text = "Connected to VEDRAQ Core (http://10.0.2.2:8000). Reports receive server-authoritative incident IDs and update dashboard instantly.",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                lineHeight = 16.sp
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }
            }

            // Disaster Category Selector
            Text(
                text = "HAZARD / DISASTER CATEGORY",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))

            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                DisasterType.values().forEach { type ->
                    FilterChip(
                        selected = uiState.disasterType == type,
                        onClick = { viewModel.onDisasterTypeChange(type) },
                        label = { Text(type.displayName, fontSize = 12.sp) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = MaterialTheme.colorScheme.primary,
                            selectedLabelColor = MaterialTheme.colorScheme.onPrimary
                        )
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Severity Level Selector
            Text(
                text = "SEVERITY ASSESSMENT",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf(SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MODERATE, SeverityLevel.LOW).forEach { sev ->
                    Box(
                        contentAlignment = Alignment.Center,
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(8.dp))
                            .background(
                                if (uiState.severity == sev) {
                                    when (sev) {
                                        SeverityLevel.CRITICAL -> VedraqRed
                                        SeverityLevel.HIGH -> VedraqAmber
                                        SeverityLevel.MODERATE -> MaterialTheme.colorScheme.secondary
                                        else -> Color.Gray
                                    }
                                } else {
                                    MaterialTheme.colorScheme.surfaceVariant
                                }
                            )
                            .clickable { viewModel.onSeverityChange(sev) }
                            .padding(vertical = 10.dp)
                    ) {
                        Text(
                            text = sev.name,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (uiState.severity == sev) Color.White else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Title Field
            OutlinedTextField(
                value = uiState.title,
                onValueChange = { viewModel.onTitleChange(it) },
                label = { Text("Incident Title / Summary *") },
                placeholder = { Text("e.g. Flash Flood on Riverbank Road") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Description Field
            OutlinedTextField(
                value = uiState.description,
                onValueChange = { viewModel.onDescriptionChange(it) },
                label = { Text("Detailed Observations / Immediate Danger") },
                placeholder = { Text("Describe road conditions, stranded citizens, water levels...") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp),
                shape = RoundedCornerShape(12.dp),
                maxLines = 5
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Authoritative Scenario City / Location Selection
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "OPERATIONAL CITY / SCENARIO LOCATION",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                if (uiState.isCoreOnline != null) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(if (uiState.isCoreOnline == true) VedraqGreen else VedraqAmber)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = if (uiState.isCoreOnline == true) "CORE ONLINE" else "CORE OFFLINE",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (uiState.isCoreOnline == true) VedraqGreen else VedraqAmber
                        )
                    }
                }
            }
            Spacer(modifier = Modifier.height(8.dp))

            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                val locations = if (uiState.availableLocations.isNotEmpty()) {
                    uiState.availableLocations
                } else {
                    CoreLocations.filterByScenario(CoreLocations.ALL, "varanasi")
                }
                locations.forEach { loc ->
                    FilterChip(
                        selected = uiState.selectedCity == loc.name,
                        onClick = { viewModel.onSelectLocation(loc) },
                        label = { Text(loc.name, fontSize = 12.sp) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = MaterialTheme.colorScheme.primary,
                            selectedLabelColor = MaterialTheme.colorScheme.onPrimary
                        )
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Location Box with dynamic GPS detection & refresh
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant)
                    .padding(14.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(
                        imageVector = if (uiState.isGpsAcquired) Icons.Default.LocationOn else Icons.Default.MyLocation,
                        contentDescription = null,
                        tint = if (uiState.isGpsAcquired) VedraqGreen else VedraqAmber,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = if (uiState.isGpsAcquired) "INCIDENT COORDINATES (GPS ACQUIRED)" else "INCIDENT COORDINATES (SEARCHING)",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (uiState.isGpsAcquired) VedraqGreen else VedraqAmber
                        )
                        Text(
                            text = uiState.locationStatus,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                    IconButton(
                        onClick = { viewModel.acquireLocation() },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Refresh GPS",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Address / Landmark Field
            OutlinedTextField(
                value = uiState.address,
                onValueChange = { viewModel.onAddressChange(it) },
                label = { Text("Address / Landmark (Optional)") },
                placeholder = { Text("e.g. Near Ganges Ghat, Sector 4") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Estimated Citizens Affected Field
            OutlinedTextField(
                value = uiState.peopleAffectedEstimate?.toString() ?: "",
                onValueChange = { str ->
                    val num = str.filter { it.isDigit() }.toIntOrNull()
                    viewModel.onPeopleAffectedChange(num)
                },
                label = { Text("Estimated Citizens Affected (Optional)") },
                placeholder = { Text("e.g. 50") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Submit Button
            val isSubmitting = uiState.submissionState is EmergencyReportSubmissionState.Submitting

            Button(
                onClick = { viewModel.submitReport() },
                enabled = !isSubmitting,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = VedraqRed)
            ) {
                if (isSubmitting) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = Color.White,
                        strokeWidth = 2.5.dp
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    Text(
                        text = "DISPATCHING TO VEDRAQ CORE...",
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                } else {
                    Icon(Icons.Default.Report, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "TRANSMIT EMERGENCY REPORT",
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}
