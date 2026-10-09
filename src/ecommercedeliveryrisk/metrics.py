import logging

from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


def calculate_metrics(y_test, predicted_classes, predicted_probabilities) -> dict[str, float]:
    f1 = f1_score(y_test, predicted_classes)
    recall = recall_score(y_test, predicted_classes)
    precision = precision_score(y_test, predicted_classes)
    avg_precision = average_precision_score(y_test, predicted_probabilities)
    roc_auc = roc_auc_score(y_test, predicted_probabilities)
    return {
        "f1": f1,
        "recall": recall,
        "precision": precision,
        "avg_precision": avg_precision,
        "roc_auc": roc_auc,
    }


def log_metrics(metrics: dict[str, float]) -> None:
    logger.info(f"F1 score: {round(metrics['f1'], ndigits=3)}")
    logger.info(
        f"Recall score: {round(metrics['recall'], ndigits=3)}"
    )  # out of all yes cases, how many did the model catch
    logger.info(
        f"Precision score: {round(metrics['precision'], ndigits=3)}"
    )  # when the model says yes, how often is it right
    logger.info(f"Average precision: {round(metrics['avg_precision'], ndigits=3)}")
    logger.info(f"ROC-AUC: {round(metrics['roc_auc'], ndigits=3)}")
