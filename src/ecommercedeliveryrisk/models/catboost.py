import logging

import numpy as np
import catboost as ctb
from sklearn.metrics import accuracy_score, log_loss

from ecommercedeliveryrisk.config import CatBoostConfig

logger = logging.getLogger(__name__)


class CatBoostModel:
    def __init__(self, config: CatBoostConfig):
        self.build_model()

    def build_model(self) -> None:
        self.model = ctb.CatBoostClassifier()

    def train(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_valid: np.ndarray | None = None,
        y_valid: np.ndarray | None = None,
    ) -> None:
        pass

    def predict(self, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        pass

    def evaluate(
        self, y_test: np.ndarray, predicted_classes: np.ndarray, predicted_probabilities: np.ndarray
    ) -> dict[str, float]:
        pass