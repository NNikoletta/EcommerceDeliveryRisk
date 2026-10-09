import os
from dataclasses import asdict

import mlflow
from mlflow import xgboost

from ecommercedeliveryrisk.config import SplitConfig, XGBoostConfig, project_root, split_dir
from ecommercedeliveryrisk.get_model_data import load_dataset
from ecommercedeliveryrisk.metrics import calculate_metrics, log_metrics
from ecommercedeliveryrisk.models.xgboost import XGBoostModel
from ecommercedeliveryrisk.prepare_data import create_evaluation_split, load_split, save_split


def create_optimization_split(model_name: str):
    _, targets = load_dataset(model_name=model_name)
    split_config = SplitConfig(
        split_id=f"{model_name}_chronological_v1",
        test_fraction=0.1,
        validation_fraction=0.1,
    )
    train_indices, validation_indices, test_indices = create_evaluation_split(
        targets=targets, config=split_config
    )
    save_split(
        targets=targets,
        train_indices=train_indices,
        validation_indices=validation_indices,
        test_indices=test_indices,
        config=split_config,
    )


def create_final_eval_split(model_name: str):
    _, targets = load_dataset(model_name=model_name)
    split_config = SplitConfig(
        split_id=f"{model_name}_final_eval_split_v1",
        test_fraction=0.1,
        validation_fraction=0,
    )
    train_indices, _, test_indices = create_evaluation_split(targets=targets, config=split_config)
    save_split(
        targets=targets,
        train_indices=train_indices,
        validation_indices=None,
        test_indices=test_indices,
        config=split_config,
    )


def optimization_pipeline(model_name):
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    mlflow.set_experiment(f"EcommerceDeliveryRisk-{model_name}")

    split_id = f"{model_name}_chronological_v1"
    features, targets = load_dataset(model_name=model_name)
    loaded_split = load_split(split_id=split_id, targets=targets, validation=True)

    if len(loaded_split) != 3:
        raise ValueError("The optimization split must contain three arrays.")

    train_indices, validation_indices, _ = loaded_split

    if validation_indices is None:
        raise ValueError("The optimization pipeline requires validation data.")

    x_train = features.iloc[train_indices].copy()
    x_valid = features.iloc[validation_indices].copy()

    y_train = targets[train_indices]
    y_valid = targets[validation_indices]

    # values, counts = np.unique(y_train, return_counts=True)
    # entry_count = dict(zip(values, counts))
    # negative_class = entry_count[0]
    # positive_class = entry_count[1]
    #
    # ratio = sqrt(negative_class/positive_class)
    xgboost_config = XGBoostConfig(max_delta_step=1, min_child_weight=10, threshold=0.5)

    with mlflow.start_run(run_name="xgboost_non_delivery_v1"):
        mlflow.set_tags({"task": model_name, "model_family": "xgboost", "run_role": "tuning"})

        mlflow.log_params(
            {
                **asdict(xgboost_config),
                "split_id": split_id,
                "decision_threshold": xgboost_config.threshold,
                "training_rows": len(y_train),
            }
        )

        for filename in (
            f"{split_id}.npz",
            f"{split_id}_metadata.json",
        ):
            mlflow.log_artifact(str(split_dir / filename), artifact_path="split")
        model = XGBoostModel(config=xgboost_config)
        model.train(x_train=x_train, y_train=y_train)
        predicted_classes, predicted_probabilities = model.predict(x_test=x_valid)
        basic_metrics = model.evaluate(
            y_test=y_valid,
            predicted_classes=predicted_classes,
            predicted_probabilities=predicted_probabilities,
        )
        metrics = calculate_metrics(
            y_test=y_valid,
            predicted_classes=predicted_classes,
            predicted_probabilities=predicted_probabilities,
        )
        log_metrics(metrics)

        mlflow.log_metrics(
            {
                f"validation_{name}": float(value)
                for name, value in (basic_metrics | metrics).items()
            }
        )
        mlflow.log_metric("validation_positive_rate", float(y_valid.mean()))
        mlflow.log_dict(
            {column: str(dtype) for column, dtype in x_train.dtypes.items()}, "feature_dtypes.json"
        )
        mlflow.log_dict(
            {
                str(probability): (str(label), str(true_label))
                for probability, label, true_label in zip(
                    predicted_probabilities, predicted_classes, y_train, strict=True
                )
            },
            "results.json",
        )
        xgboost.log_model(xgb_model=model.model, name="model", model_format="json")
        mlflow.log_artifact(str(project_root / "uv.lock"), artifact_path="environment")
        mlflow.log_artifact(
            str(project_root / "data" / "manifests" / "benchmark_raw_data_manifest.json"),
            artifact_path="data",
        )
        mlflow.log_artifacts(
            str(project_root / "src" / "ecommercedeliveryrisk"), artifact_path="source"
        )
