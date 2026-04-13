from typing import Optional, Tuple

class RuleEngine:
    """
    Fallback Rule Engine to detect basic threshold violations if the ML model fails,
    returns (is_anomaly, classification, severity, description).
    """

    @staticmethod
    def evaluate(event: dict) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        temperature = event.get("temperature", 0.0)
        humidity = event.get("humidity", 0.0)
        pollution_level = event.get("pollution_level", 0.0)
        traffic_count = event.get("traffic_count", 0)

        # 1. Hardware/System Errors (Impossible values)
        if temperature > 100.0 or temperature < -50.0:
            return True, "system_error", "HIGH", "Temperature outside operational bounds"
        if humidity < 0.0 or humidity > 100.0:
            return True, "system_error", "HIGH", "Humidity outside operational bounds"

        # 2. Environmental Anomalies
        if temperature > 40.0 and humidity < 20.0:
            return True, "heatwave", "MEDIUM", "High temperature with low humidity detected"
        
        if pollution_level > 300.0:
            return True, "pollution_spike", "HIGH", "Critical pollution levels detected (PM2.5 > 300)"
        elif pollution_level > 150.0:
            return True, "pollution_warning", "LOW", "Elevated pollution detected (PM2.5 > 150)"

        # 3. Traffic Anomalies
        if traffic_count > 400 and pollution_level > 100.0:
            return True, "traffic_jam", "MEDIUM", "High traffic volume with elevated pollution"
        elif traffic_count > 500:
            return True, "traffic_jam", "LOW", "Heavy traffic volume detected"

        # Not an anomaly according to basic rules
        return False, None, None, None

rule_engine = RuleEngine()
