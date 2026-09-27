package com.vedraq.app.core.util

/**
 * Single-shot UI event interface for snackbars, navigation signals, and dialog alerts.
 */
sealed interface UiEvent {
    data class ShowSnackbar(val message: String) : UiEvent
    data class Navigate(val route: String) : UiEvent
    object NavigateUp : UiEvent
    data class TriggerEmergencyAlert(val title: String, val message: String) : UiEvent
}
