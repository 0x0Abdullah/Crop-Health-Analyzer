def get_confidence_badge_html(confidence_score: float) -> str:
    """Returns HTML badge styled based on confidence score."""
    percent = int(confidence_score * 100)
    if confidence_score >= 0.75:
        color = "#2e7d32" # High green
        label = f"High Confidence ({percent}%)"
    elif confidence_score >= 0.50:
        color = "#f57c00" # Orange moderate
        label = f"Moderate Confidence ({percent}%)"
    else:
        color = "#c62828" # Red low
        label = f"Low Confidence ({percent}%)"

    return f'<span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.85rem;">{label}</span>'

def get_severity_badge_html(severity: str) -> str:
    """Returns HTML badge for severity level."""
    sev = severity.capitalize()
    if sev == "High":
        color = "#d32f2f"
    elif sev == "Moderate":
        color = "#ed6c02"
    elif sev == "Low":
        color = "#0288d1"
    else:
        color = "#757575"

    return f'<span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.85rem;">Severity: {sev}</span>'
