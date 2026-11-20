from models import Alert


NEXT_STEPS = {
    "critical": "Investigate immediately and take corrective action.",
    "warning": "Review the affected system and monitor the metric closely.",
    "info": "Review the metric and confirm whether any action is needed.",
}


def generate_explanation(alert: Alert) -> str: 
    """Generate a rule-based plain-language explanation for an alert. 
 
    Args: 
        alert: Alert whose metric, threshold, severity, source, and title are 
            used to create the explanation. 
 
    Returns: 
        A plain-language explanation with a recommended next step. 
 
    Raises: 
        AttributeError: If ``alert.severity`` is not a string. 
    """ 
    if alert.metric_value > alert.threshold: 
        threshold_event = "exceeded" 
    elif alert.metric_value < alert.threshold: 
        threshold_event = "fell below" 
    else: 
        threshold_event = "reached" 
 
    if alert.severity.lower() == "critical": 
        next_step = "Investigate immediately and take corrective action." 
    elif alert.severity.lower() == "warning":
        next_step = "Review the affected system and monitor the metric closely." 
    else: 
        next_step = "Review the metric and confirm whether any action is needed." 
 
    acknowledgement = "Not yet acknowledged" 
 
    return ( 
        f"This {alert.severity} alert from {alert.source} is titled " 
        f"\"{alert.title}\". The {alert.metric_name} metric {threshold_event} " 
        f"its threshold: the current value is {alert.metric_value}, compared " 
        f"with a threshold of {alert.threshold}. Recommended next step: " 
        f"{next_step} Acknowledged by: {acknowledgement}." 
    )