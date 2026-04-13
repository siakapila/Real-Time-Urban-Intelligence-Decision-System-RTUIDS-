import numpy as np
import logging
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

class MLAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100, 
            contamination=0.05, 
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        self._warmup_model()

    def _warmup_model(self):
        """
        In a real production environment, you would load a pre-trained model like:
        self.model = joblib.load('model.pkl')
        
        For this system, we will 'warm up' the model with some synthetic normal data 
        so it works out of the box without requiring historical data.
        """
        try:
            logger.info("Initializing ML Isolation Forest with synthetic baseline data...")
            # Generate synthetic 'normal' city data: 
            # [temperature, humidity, traffic_count, pollution_level]
            normal_data = np.array([
                [np.random.normal(25, 5), np.random.normal(50, 10), np.random.normal(50, 15), np.random.normal(20, 5)]
                for _ in range(1000)
            ])
            self.model.fit(normal_data)
            self.is_trained = True
            logger.info("ML Isolation Forest is ready.")
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {e}")
            self.is_trained = False

    def predict(self, event: dict) -> bool:
        """
        Returns True if anomaly detected, False otherwise.
        """
        if not self.is_trained:
            raise RuntimeError("ML Model is not trained or failed to load")
            
        features = np.array([[
            event.get("temperature", 0.0),
            event.get("humidity", 0.0),
            event.get("traffic_count", 0),
            event.get("pollution_level", 0.0)
        ]])
        
        # predict returns 1 for inliers, -1 for outliers
        prediction = self.model.predict(features)
        
        return prediction[0] == -1

ml_detector = MLAnomalyDetector()
