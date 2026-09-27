package com.vedraq.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation.compose.rememberNavController
import com.vedraq.app.core.location.AndroidLocationClient
import com.vedraq.app.core.network.NetworkConfig
import com.vedraq.app.core.network.NetworkConnectivityObserver
import com.vedraq.app.core.network.SyncManager
import com.vedraq.app.data.repository.AlertRepositoryImpl
import com.vedraq.app.data.repository.IncidentRepositoryImpl
import com.vedraq.app.data.repository.LocationRepositoryImpl
import com.vedraq.app.data.repository.SosRepositoryImpl
import com.vedraq.app.data.repository.UserRepositoryImpl
import com.vedraq.app.presentation.navigation.VedraqNavHost
import com.vedraq.app.ui.theme.VedraqTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        NetworkConfig.init(applicationContext)
        enableEdgeToEdge()
        setContent {
            VedraqTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val navController = rememberNavController()
                    val locationClient = remember { AndroidLocationClient(applicationContext) }
                    val incidentRepository = remember { IncidentRepositoryImpl() }
                    val alertRepository = remember { AlertRepositoryImpl() }
                    val locationRepository = remember { LocationRepositoryImpl() }
                    val sosRepository = remember { SosRepositoryImpl(incidentRepository = incidentRepository) }
                    val userRepository = remember { UserRepositoryImpl() }
                    val connectivityObserver = remember { NetworkConnectivityObserver(applicationContext) }

                    LaunchedEffect(Unit) {
                        locationRepository.refreshLocations()
                        locationRepository.refreshFacilities()
                        SyncManager(connectivityObserver, incidentRepository, alertRepository).startObserving()
                    }

                    VedraqNavHost(
                        navController = navController,
                        incidentRepository = incidentRepository,
                        alertRepository = alertRepository,
                        sosRepository = sosRepository,
                        userRepository = userRepository,
                        locationRepository = locationRepository,
                        locationClient = locationClient
                    )
                }
            }
        }
    }
}
