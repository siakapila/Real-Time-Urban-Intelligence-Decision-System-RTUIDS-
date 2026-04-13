import logging
from typing import Tuple, Optional
from app.ml.anomaly_detector import ml_detector
from app.engines.rules import rule_engine

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    The Decision Engine attempts to detect anomalies using the ML Module. 
    If the ML module throws an exception or is unresponsive, it automatically 
    falls back to the Rule Engine.
    
    After detection, it handles the complex classification logic for ML outputs to 
    explain *why* it thought it was an anomaly.
    """

    @staticmethod
    def classify_ml_anomaly(event: dict) -> Tuple[str, str, str]:
        """
        Since Isolation Forests don't provide explicit classification (just outliers),
        we post-process the outlier using heuristics to assign classification and severity.
        """
        temperature = event.get("temperature", 0.0)
        pollution_level = event.get("pollution_level", 0.0)
        traffic_count = event.get("traffic_count", 0)

        if pollution_level > 100.0 and traffic_count > 200:
            return "traffic_pollution_nexus", "HIGH", "ML detected complex high traffic & pollution event"
        elif temperature > 38.0:
            return "climatic_anomaly", "MEDIUM", "ML detected atypical regional temperature variance"
        else:
            return "unknown_multivariate_anomaly", "LOW", "ML detected an obscure non-linear data pattern"

    def evaluate(self, event: dict) -> Tuple[bool, Optional[str], Optional[str], Optional[str], str]:
        """
        Returns: (is_anomaly, classification, severity, description, detected_by)
        """
        # Try ML First
        try:
            is_anomaly = ml_detector.predict(event)
            if is_anomaly:
                classification, severity, desc = self.classify_ml_anomaly(event)
                return True, classification, severity, desc, "ML_ISOLATION_FOREST"
            return False, None, None, None, "ML_ISOLATION_FOREST"
            
        except Exception as e:
            # CIRCUIT BREAKER: Fall back to rules
            logger.warning(f"ML evaluation failed ({e}), routing to Rule Engine circuit breaker.")
            is_anomaly, classification, severity, desc = rule_engine.evaluate(event)
            return is_anomaly, classification, severity, desc, "RULE_ENGINE_FALLBACK"

decision_engine = DecisionEngine()
