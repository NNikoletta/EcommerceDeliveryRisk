import logging

import numpy as np
import xgboost as xgb
from sklearn.metrics import accuracy_score, log_loss

from ecommercedeliveryrisk.config import XGBoostConfig

logger = logging.getLogger(__name__)


class XGBoostModel:
    def __init__(self, config: XGBoostConfig):
        self.learning_rate = config.learning_rate
        self.n_estimators = config.n_estimators
        self.max_depth = config.max_depth
        self.gamma = config.gamma
        self.random_state = config.random_state
        self.min_child_weight = config.min_child_weight
        self.ratio = config.ratio
        self.enable_categorical = config.enable_categorical
        self.model = xgb.XGBClassifier()
        self.build_model()

    def build_model(self) -> None:
        self.model = xgb.XGBClassifier(
            objective="binary:logistic",
            learning_rate=self.learning_rate,
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            gamma=self.gamma,
            random_state=self.random_state,
            min_child_weight=self.min_child_weight,
            scale_pos_weight=self.ratio,
            enable_categorical=self.enable_categorical,
            eval_metric=["logloss"],
        )

    def train(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        x_valid: np.ndarray | None = None,
        y_valid: np.ndarray | None = None,
    ) -> None:
        if x_valid is None and y_valid is None:
            self.model.fit(x_train, y_train)
        else:
            self.model.fit(x_train, y_train, eval_set=[(x_valid, y_valid)])

    def predict(self, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        predicted_classes = self.model.predict(x_test)
        predicted_probabilities = self.model.predict_proba(x_test)[:, 1]
        return predicted_classes, predicted_probabilities

    def evaluate(
        self, y_test: np.ndarray, predicted_classes: np.ndarray, predicted_probabilities: np.ndarray
    ) -> dict[str, float]:
        acc = accuracy_score(y_test, predicted_classes)
        loss = log_loss(y_test, predicted_probabilities)
        logger.info(f"Loss: {round(loss, ndigits=3)}, Accuracy: {round(acc * 100, ndigits=3)}%")
        return {"loss": loss, "accuracy": acc}
