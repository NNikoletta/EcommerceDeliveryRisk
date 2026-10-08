from ecommercedeliveryrisk.config import SplitConfig, XGBoostConfig
from ecommercedeliveryrisk.get_model_data import load_dataset
from ecommercedeliveryrisk.metrics import calculate_metrics, log_metrics
from ecommercedeliveryrisk.models.xgboost import XGBoostModel
from ecommercedeliveryrisk.prepare_data import create_evaluation_split, load_split, save_split


def create_optimization_split(model_name: str):
    _, targets = load_dataset(model_name=model_name)
    split_config = SplitConfig(
        split_id="fixed_pipeline_test_split_v1",
        split_seed=8102026,
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
        split_id="fixed_final_eval_split_v1",
        split_seed=8102026,
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
    features, targets = load_dataset(model_name=model_name)
    train_indices, validation_indices, _ = load_split(
        split_id="fixed_pipeline_test_split_v1", targets=targets
    )

    x_train = features.iloc[train_indices].copy()
    x_valid = features.iloc[validation_indices].copy()
    # x_test = features.iloc[test_indices].copy()

    y_train = targets[train_indices]
    y_valid = targets[validation_indices]
    # y_test = targets[test_indices]

    xgboost_config = XGBoostConfig()

    model = XGBoostModel(config=xgboost_config)
    model.train(x_train=x_train, y_train=y_train)
    predicted_classes, predicted_probabilities = model.predict(x_test=x_valid)
    model.evaluate(
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


def final_evaluation_pipeline(model_name):
    features, targets = load_dataset(model_name=model_name)
    train_indices, test_indices = load_split(split_id="fixed_final_eval_split_v1", targets=targets)

    x_train = features.iloc[train_indices].copy()
    x_test = features.iloc[test_indices].copy()

    y_train = targets[train_indices]
    y_test = targets[test_indices]

    xgboost_config = XGBoostConfig()

    model = XGBoostModel(config=xgboost_config)
    model.train(x_train=x_train, y_train=y_train)
    predicted_classes, predicted_probabilities = model.predict(x_test=x_test)
    model.evaluate(
        y_test=y_test,
        predicted_classes=predicted_classes,
        predicted_probabilities=predicted_probabilities,
    )
    metrics = calculate_metrics(
        y_test=y_test,
        predicted_classes=predicted_classes,
        predicted_probabilities=predicted_probabilities,
    )
    log_metrics(metrics)
