package com.vedraq.app.presentation.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.vedraq.app.core.location.LocationClient
import com.vedraq.app.domain.repository.AlertRepository
import com.vedraq.app.domain.repository.IncidentRepository
import com.vedraq.app.domain.repository.LocationRepository
import com.vedraq.app.domain.repository.SosRepository
import com.vedraq.app.domain.repository.UserRepository
import com.vedraq.app.domain.usecase.SubmitIncidentUseCase
import com.vedraq.app.presentation.screens.alerts.AlertsScreen
import com.vedraq.app.presentation.screens.emergency.EmergencyReportScreen
import com.vedraq.app.presentation.screens.emergency.EmergencyReportViewModel
import com.vedraq.app.presentation.screens.home.HomeScreen
import com.vedraq.app.presentation.screens.login.LoginScreen
import com.vedraq.app.presentation.screens.map.MapScreen
import com.vedraq.app.presentation.screens.map.MapViewModel
import com.vedraq.app.presentation.screens.profile.ProfileScreen
import com.vedraq.app.presentation.screens.sos.SosScreen
import com.vedraq.app.presentation.screens.splash.SplashScreen

@Composable
fun VedraqNavHost(
    navController: NavHostController,
    incidentRepository: IncidentRepository,
    alertRepository: AlertRepository,
    sosRepository: SosRepository,
    userRepository: UserRepository,
    locationRepository: LocationRepository,
    locationClient: LocationClient? = null,
    modifier: Modifier = Modifier,
    startDestination: String = VedraqDestinations.SPLASH
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier
    ) {
        composable(VedraqDestinations.SPLASH) {
            SplashScreen(
                onNavigateToHome = {
                    navController.navigate(VedraqDestinations.HOME) {
                        popUpTo(VedraqDestinations.SPLASH) { inclusive = true }
                    }
                },
                onNavigateToLogin = {
                    navController.navigate(VedraqDestinations.LOGIN)
                }
            )
        }

        composable(VedraqDestinations.LOGIN) {
            LoginScreen(
                onNavigateToHome = {
                    navController.navigate(VedraqDestinations.HOME) {
                        popUpTo(VedraqDestinations.LOGIN) { inclusive = true }
                    }
                },
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        composable(VedraqDestinations.HOME) {
            HomeScreen(
                incidentRepository = incidentRepository,
                onNavigateToEmergencyReport = { navController.navigate(VedraqDestinations.EMERGENCY_REPORT) },
                onNavigateToSos = { navController.navigate(VedraqDestinations.SOS) },
                onNavigateToAlerts = { navController.navigate(VedraqDestinations.ALERTS) },
                onNavigateToMap = { navController.navigate(VedraqDestinations.MAP) },
                onNavigateToProfile = { navController.navigate(VedraqDestinations.PROFILE) },
                onNavigateToRoute = { route ->
                    navController.navigate(route) {
                        popUpTo(VedraqDestinations.HOME) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }

        composable(VedraqDestinations.EMERGENCY_REPORT) {
            val emergencyViewModel = viewModel<EmergencyReportViewModel>(
                factory = object : ViewModelProvider.Factory {
                    @Suppress("UNCHECKED_CAST")
                    override fun <T : ViewModel> create(modelClass: Class<T>): T {
                        return EmergencyReportViewModel(
                            submitIncidentUseCase = SubmitIncidentUseCase(incidentRepository),
                            locationClient = locationClient,
                            locationRepository = locationRepository
                        ) as T
                    }
                }
            )
            EmergencyReportScreen(
                viewModel = emergencyViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(VedraqDestinations.SOS) {
            SosScreen(
                sosRepository = sosRepository,
                locationClient = locationClient,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToRoute = { route ->
                    navController.navigate(route) {
                        popUpTo(VedraqDestinations.HOME) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }

        composable(VedraqDestinations.ALERTS) {
            AlertsScreen(
                alertRepository = alertRepository,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToRoute = { route ->
                    navController.navigate(route) {
                        popUpTo(VedraqDestinations.HOME) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }

        composable(VedraqDestinations.MAP) {
            val mapViewModel = viewModel<MapViewModel>(
                factory = object : ViewModelProvider.Factory {
                    @Suppress("UNCHECKED_CAST")
                    override fun <T : ViewModel> create(modelClass: Class<T>): T {
                        return MapViewModel(
                            locationRepository = locationRepository,
                            locationClient = locationClient
                        ) as T
                    }
                }
            )
            MapScreen(
                viewModel = mapViewModel,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToRoute = { route ->
                    navController.navigate(route) {
                        popUpTo(VedraqDestinations.HOME) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }

        composable(VedraqDestinations.PROFILE) {
            ProfileScreen(
                userRepository = userRepository,
                incidentRepository = incidentRepository,
                onNavigateBack = { navController.popBackStack() },
                onNavigateToRoute = { route ->
                    navController.navigate(route) {
                        popUpTo(VedraqDestinations.HOME) { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }
    }
}
