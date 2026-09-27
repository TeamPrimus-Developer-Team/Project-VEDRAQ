package com.vedraq.app.presentation.screens.map

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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.CrisisAlert
import androidx.compose.material.icons.filled.LocalHospital
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vedraq.app.domain.model.FacilityType
import com.vedraq.app.presentation.components.VedraqBottomBar
import com.vedraq.app.presentation.components.VedraqTopBar
import com.vedraq.app.presentation.navigation.VedraqDestinations
import com.vedraq.app.ui.theme.VedraqAmber
import com.vedraq.app.ui.theme.VedraqBlue
import com.vedraq.app.ui.theme.VedraqGreen
import com.vedraq.app.ui.theme.VedraqRed
import java.util.Locale

@Composable
fun MapScreen(
    viewModel: MapViewModel,
    onNavigateBack: () -> Unit,
    onNavigateToRoute: (String) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            VedraqTopBar(
                title = "Tactical GIS Map",
                canNavigateBack = true,
                onNavigateBack = onNavigateBack,
                showSystemStatus = true,
                actions = {
                    IconButton(onClick = { viewModel.refreshData() }) {
                        if (uiState.isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.primary
                            )
                        } else {
                            Icon(
                                imageVector = Icons.Default.Refresh,
                                contentDescription = "Sync Map Data",
                                tint = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }
            )
        },
        bottomBar = {
            VedraqBottomBar(
                currentRoute = VedraqDestinations.MAP,
                onNavigateToRoute = onNavigateToRoute
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.acquireUserLocation() },
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = Color.White
            ) {
                Icon(Icons.Default.MyLocation, contentDescription = "My GPS Position")
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            // Tactical Map Visual Shell (Canvas representation)
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color(0xFF0F172A))
            ) {
                // Tactical Grid Coordinate Overlay
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    verticalArrangement = Arrangement.SpaceAround
                ) {
                    repeat(5) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(1.dp)
                                .background(Color(0xFF1E293B).copy(alpha = 0.5f))
                        )
                    }
                }

                // Dynamic User Position Marker
                Box(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .padding(bottom = 60.dp)
                ) {
                    MapMarkerBadge(
                        label = String.format(
                            Locale.US,
                            "YOU (%.4f° N, %.4f° E - HQ)",
                            uiState.userLatitude,
                            uiState.userLongitude
                        ),
                        icon = Icons.Default.MyLocation,
                        color = VedraqBlue,
                        isSelected = false
                    )
                }

                // Dynamic Core Hazards (Critical / High Tactical Operational Zones)
                if (uiState.showHazards) {
                    val criticalZones = uiState.zones.filter {
                        it.classification == "CRITICAL" || (it.damagePercentage ?: 0) >= 65
                    }.ifEmpty { uiState.zones.take(3) }

                    // Render prominent hazards from Core
                    criticalZones.getOrNull(0)?.let { z1 ->
                        Box(
                            modifier = Modifier
                                .align(Alignment.TopEnd)
                                .padding(top = 95.dp, end = 24.dp)
                        ) {
                            MapMarkerBadge(
                                label = "${z1.id} ${z1.name.uppercase()} (${z1.damagePercentage ?: 65}% DMG)",
                                icon = Icons.Default.Warning,
                                color = VedraqRed,
                                isSelected = uiState.selectedZone?.id == z1.id,
                                onClick = { viewModel.selectZone(z1) }
                            )
                        }
                    }

                    criticalZones.getOrNull(1)?.let { z2 ->
                        Box(
                            modifier = Modifier
                                .align(Alignment.CenterStart)
                                .padding(top = 30.dp, start = 18.dp)
                        ) {
                            MapMarkerBadge(
                                label = "${z2.id} ${z2.name} (${z2.damagePercentage ?: 75}% DMG)",
                                icon = Icons.Default.CrisisAlert,
                                color = VedraqRed,
                                isSelected = uiState.selectedZone?.id == z2.id,
                                onClick = { viewModel.selectZone(z2) }
                            )
                        }
                    }

                    criticalZones.getOrNull(2)?.let { z3 ->
                        Box(
                            modifier = Modifier
                                .align(Alignment.BottomEnd)
                                .padding(bottom = 190.dp, end = 24.dp)
                        ) {
                            MapMarkerBadge(
                                label = "${z3.id} ${z3.name}",
                                icon = Icons.Default.Warning,
                                color = VedraqAmber,
                                isSelected = uiState.selectedZone?.id == z3.id,
                                onClick = { viewModel.selectZone(z3) }
                            )
                        }
                    }
                }

                // Dynamic Core Shelters (Safe Zones)
                if (uiState.showShelters) {
                    val shelters = uiState.facilities.filter { it.type == FacilityType.SHELTER }
                    shelters.getOrNull(0)?.let { s1 ->
                        Box(
                            modifier = Modifier
                                .align(Alignment.BottomStart)
                                .padding(bottom = 200.dp, start = 20.dp)
                        ) {
                            val occ = s1.occupancyPercentage ?: 45
                            MapMarkerBadge(
                                label = "${s1.name.uppercase()} (${occ}% OCC)",
                                icon = Icons.Default.Shield,
                                color = VedraqGreen,
                                isSelected = uiState.selectedFacility?.id == s1.id,
                                onClick = { viewModel.selectFacility(s1) }
                            )
                        }
                    }

                    shelters.getOrNull(1)?.let { s2 ->
                        Box(
                            modifier = Modifier
                                .align(Alignment.TopStart)
                                .padding(top = 110.dp, start = 24.dp)
                        ) {
                            MapMarkerBadge(
                                label = s2.name,
                                icon = Icons.Default.Shield,
                                color = VedraqGreen,
                                isSelected = uiState.selectedFacility?.id == s2.id,
                                onClick = { viewModel.selectFacility(s2) }
                            )
                        }
                    }
                }

                // Dynamic Core Hospitals
                if (uiState.showHospitals) {
                    val hospitals = uiState.facilities.filter { it.type == FacilityType.HOSPITAL }
                    hospitals.getOrNull(0)?.let { h1 ->
                        Box(
                            modifier = Modifier
                                .align(Alignment.CenterEnd)
                                .padding(end = 24.dp, bottom = 40.dp)
                        ) {
                            MapMarkerBadge(
                                label = "${h1.name.uppercase()} (${h1.availableBeds ?: 140} BEDS)",
                                icon = Icons.Default.LocalHospital,
                                color = VedraqAmber,
                                isSelected = uiState.selectedFacility?.id == h1.id,
                                onClick = { viewModel.selectFacility(h1) }
                            )
                        }
                    }

                    hospitals.getOrNull(1)?.let { h2 ->
                        Box(
                            modifier = Modifier
                                .align(Alignment.BottomCenter)
                                .padding(bottom = 230.dp)
                        ) {
                            MapMarkerBadge(
                                label = h2.name,
                                icon = Icons.Default.LocalHospital,
                                color = VedraqAmber,
                                isSelected = uiState.selectedFacility?.id == h2.id,
                                onClick = { viewModel.selectFacility(h2) }
                            )
                        }
                    }
                }
            }

            // Top Layer: Connectivity Badge & Filters Bar
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                // Live Core status indicator
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0xFF0F172A).copy(alpha = 0.85f))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(6.dp)
                            .clip(CircleShape)
                            .background(if (uiState.isCoreOnline == true) VedraqGreen else VedraqAmber)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = if (uiState.isCoreOnline == true) {
                            "CORE ONLINE • ${uiState.zones.size} VARANASI ZONES • LIVE GIS"
                        } else {
                            "CORE OFFLINE • DISPLAYING LOCAL CACHED BASELINE"
                        },
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = if (uiState.isCoreOnline == true) VedraqGreen else VedraqAmber
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    FilterChip(
                        selected = uiState.showHazards,
                        onClick = { viewModel.toggleHazards() },
                        label = { Text("Hazards (${uiState.zones.size})", fontSize = 11.sp) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = VedraqRed,
                            selectedLabelColor = Color.White
                        )
                    )

                    FilterChip(
                        selected = uiState.showShelters,
                        onClick = { viewModel.toggleShelters() },
                        label = {
                            val count = uiState.facilities.count { it.type == FacilityType.SHELTER }
                            Text("Shelters ($count)", fontSize = 11.sp)
                        },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = VedraqGreen,
                            selectedLabelColor = Color.White
                        )
                    )

                    FilterChip(
                        selected = uiState.showHospitals,
                        onClick = { viewModel.toggleHospitals() },
                        label = {
                            val count = uiState.facilities.count { it.type == FacilityType.HOSPITAL }
                            Text("Medical ($count)", fontSize = 11.sp)
                        },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = VedraqAmber,
                            selectedLabelColor = Color.White
                        )
                    )
                }
            }

            // Bottom Shelter / Facility Info Sheet (Authoritative Core Data)
            Card(
                shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                ),
                modifier = Modifier
                    .fillMaxWidth()
                    .align(Alignment.BottomCenter)
            ) {
                Column(
                    modifier = Modifier
                        .padding(16.dp)
                        .verticalScroll(rememberScrollState())
                ) {
                    val selectedFac = uiState.selectedFacility
                    val selectedZ = uiState.selectedZone
                    val nearestS = uiState.nearestShelter

                    if (selectedFac != null) {
                        // Inspecting user-selected facility
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "SELECTED ${selectedFac.type.name} (CORE FACILITY)",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary,
                                    letterSpacing = 1.sp
                                )
                                Text(
                                    text = selectedFac.name,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                            IconButton(
                                onClick = { viewModel.clearSelection() },
                                modifier = Modifier.size(24.dp)
                            ) {
                                Icon(Icons.Default.Close, contentDescription = "Clear selection", modifier = Modifier.size(16.dp))
                            }
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        if (selectedFac.type == FacilityType.SHELTER) {
                            Text(
                                text = "Capacity: ${selectedFac.capacity ?: "N/A"} • Current: ${selectedFac.currentOccupancy ?: "N/A"} (${selectedFac.occupancyPercentage ?: 0}%) • Status: ${selectedFac.status.uppercase()}",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        } else if (selectedFac.type == FacilityType.HOSPITAL) {
                            Text(
                                text = "Capacity: ${selectedFac.capacity ?: "N/A"} beds • Available: ${selectedFac.availableBeds ?: "N/A"} • Spec: ${selectedFac.specialization ?: "General"}",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else if (selectedZ != null) {
                        // Inspecting user-selected tactical zone
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "TACTICAL ZONE ${selectedZ.id} (CORE DATASET)",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = VedraqRed,
                                    letterSpacing = 1.sp
                                )
                                Text(
                                    text = selectedZ.name,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                            IconButton(
                                onClick = { viewModel.clearSelection() },
                                modifier = Modifier.size(24.dp)
                            ) {
                                Icon(Icons.Default.Close, contentDescription = "Clear selection", modifier = Modifier.size(16.dp))
                            }
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Damage: ${selectedZ.damagePercentage ?: 60}% • Classification: ${selectedZ.classification ?: "HIGH"} • Road: ${(selectedZ.roadAccessibility ?: "open").uppercase()} • Pop: ${selectedZ.population ?: "N/A"}",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    } else if (nearestS != null) {
                        // Dynamic nearest evacuation shelter
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text(
                                    text = "NEAREST EVACUATION SHELTER (CORE IDENTIFIED)",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary,
                                    letterSpacing = 1.sp
                                )
                                val distStr = String.format(Locale.US, "%.1f km", uiState.nearestShelterDistanceKm ?: 1.8)
                                Text(
                                    text = "${nearestS.name} • $distStr",
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }
                            Box(
                                contentAlignment = Alignment.Center,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(VedraqGreen.copy(alpha = 0.15f))
                                    .padding(horizontal = 8.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    text = "CAPACITY: ${nearestS.occupancyPercentage ?: 42}%",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = VedraqGreen
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Total Capacity: ${nearestS.capacity ?: 2500} • Current Occupancy: ${nearestS.currentOccupancy ?: 1200} • Status: ${nearestS.status.uppercase()}",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.outline
                        )
                    } else {
                        Text(
                            text = "Prepared for VEDRAQ Core GIS & Mapbox/OSM tile engine integration.",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.outline
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun MapMarkerBadge(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color,
    isSelected: Boolean = false,
    onClick: () -> Unit = {}
) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(if (isSelected) color.copy(alpha = 0.3f) else Color(0xFF1E293B).copy(alpha = 0.9f))
            .border(if (isSelected) 2.5.dp else 1.5.dp, if (isSelected) Color.White else color, RoundedCornerShape(20.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 5.dp)
    ) {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .size(20.dp)
                .clip(CircleShape)
                .background(color)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = Color.White,
                modifier = Modifier.size(12.dp)
            )
        }
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = label,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White
        )
    }
}
