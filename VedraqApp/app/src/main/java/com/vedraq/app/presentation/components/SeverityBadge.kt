package com.vedraq.app.presentation.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.vedraq.app.domain.model.SeverityLevel
import com.vedraq.app.ui.theme.VedraqAmber
import com.vedraq.app.ui.theme.VedraqBlue
import com.vedraq.app.ui.theme.VedraqGreen
import com.vedraq.app.ui.theme.VedraqRed

@Composable
fun SeverityBadge(
    severity: SeverityLevel,
    modifier: Modifier = Modifier
) {
    val (backgroundColor, textColor, borderColor) = when (severity) {
        SeverityLevel.CRITICAL -> Triple(
            VedraqRed.copy(alpha = 0.15f),
            VedraqRed,
            VedraqRed.copy(alpha = 0.6f)
        )
        SeverityLevel.HIGH -> Triple(
            VedraqAmber.copy(alpha = 0.15f),
            VedraqAmber,
            VedraqAmber.copy(alpha = 0.6f)
        )
        SeverityLevel.MODERATE -> Triple(
            VedraqBlue.copy(alpha = 0.15f),
            VedraqBlue,
            VedraqBlue.copy(alpha = 0.5f)
        )
        SeverityLevel.LOW -> Triple(
            Color.Gray.copy(alpha = 0.15f),
            Color.Gray,
            Color.Gray.copy(alpha = 0.4f)
        )
        SeverityLevel.SAFE -> Triple(
            VedraqGreen.copy(alpha = 0.15f),
            VedraqGreen,
            VedraqGreen.copy(alpha = 0.6f)
        )
    }

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(6.dp))
            .background(backgroundColor)
            .border(width = 1.dp, color = borderColor, shape = RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 3.dp)
    ) {
        Text(
            text = severity.name,
            color = textColor,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.8.sp
        )
    }
}
