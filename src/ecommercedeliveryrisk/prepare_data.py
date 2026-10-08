import json
import logging

import numpy as np
from sklearn.model_selection import train_test_split

from ecommercedeliveryrisk.config import SplitConfig, split_dir
from ecommercedeliveryrisk.utils import ensure_dir

logger = logging.getLogger(__name__)


def create_evaluation_split(targets: np.ndarray, config: SplitConfig):
    all_indices = np.arange(len(targets))
    training_pool_fraction = 1 - config.validation_fraction + config.test_fraction
    training_pool_size = round(len(targets) * training_pool_fraction)
    train_indices = all_indices[0 : training_pool_size - 1]
    test_pool_indices = np.setdiff1d(
        all_indices, train_indices
    )  # indices that are in all_indices but not in training_indices

    if config.validation_fraction != 0:
        relative_test_fraction = (
            1 / (config.validation_fraction + config.test_fraction) * config.test_fraction
        )

        test_indices, validation_indices = train_test_split(
            test_pool_indices,
            test_size=relative_test_fraction,
            random_state=config.split_seed,
            stratify=targets,
        )

        return train_indices, validation_indices, test_indices

    return train_indices, test_pool_indices


def save_split(
    targets: np.ndarray,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    config: SplitConfig,
    validation_indices: np.ndarray = None,
) -> None:
    validate_split(
        targets=targets,
        train_indices=train_indices,
        test_indices=test_indices,
        validation_indices=validation_indices,
    )
    logger.info("Begin saving split data.")
    ensure_dir(split_dir)

    indices_path = split_dir / f"{config.split_id}.npz"
    metadata_path = split_dir / f"{config.split_id}_metadata.json"

    if indices_path.exists() or metadata_path.exists():
        logger.info("Split data already exists and will not be overwritten: skipping.")
        return

    if validation_indices is not None:
        np.savez_compressed(
            str(indices_path),
            train_indices=train_indices,
            validation_indices=validation_indices,
            test_indices=test_indices,
        )
    else:
        np.savez_compressed(
            str(indices_path), train_indices=train_indices, test_indices=test_indices
        )

    def class_counts(indices):
        labels, counts = np.unique(targets[indices], return_counts=True)
        return {str(int(label)): int(count) for label, count in zip(labels, counts, strict=True)}

    metadata = {
        "split_id": config.split_id,
        "strategy": "chronological"
        if validation_indices is not None
        else "chronological_train_random_stratified_validation",
        "split_seed": config.split_seed if validation_indices is not None else None,
        "test_fraction": config.test_fraction,
        "validation_fraction": config.validation_fraction,
        "sample_counts": {
            "train": len(train_indices),
            "validation": len(validation_indices) if validation_indices is not None else 0,
            "test": class_counts(test_indices),
        },
    }

    with metadata_path.open("w", encoding="utf-8") as json_file:
        json.dump(metadata, json_file, indent=2)

    logger.info("Split metadata successfully saved.")


def validate_split(
    targets: np.ndarray,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    validation_indices: np.ndarray = None,
) -> None:

    logger.info("Begin validating split data.")

    if targets.ndim != 1:
        raise ValueError(
            f"'targets' must be a one-dimensional array, but its shape is {targets.shape}."
        )

    sample_count = targets.shape[0]

    if validation_indices is not None:
        splits = {"train": train_indices, "validation": validation_indices, "test": test_indices}
    else:
        splits = {"train": train_indices, "validation": test_indices}

    for split_name, indices in splits.items():
        if not isinstance(indices, np.ndarray):
            raise TypeError(
                f"{split_name}_indices must be a Numpy array, but its type is {type(indices)}."
            )

        if indices.ndim != 1:
            raise ValueError(f"{split_name}_indices must be a one-dimensional Numpy array.")

        if indices.size == 0:
            raise ValueError(f"{split_name}_indices is empty.")

        if not np.issubdtype(indices.dtype, np.integer):
            raise ValueError(f"{split_name}_indices must be integer values,")

        if np.any(indices < 0) or np.any(indices >= sample_count):
            raise ValueError(f"{split_name}_indices must be between 0 and {sample_count - 1}.")

        if np.unique(indices).size != indices.size:
            raise ValueError(f"{split_name}_indices must not contain duplicate values.")

    if validation_indices is not None:
        split_pairs = [("train", "validation"), ("train", "test"), ("validation", "test")]
    else:
        split_pairs = [("train", "test")]

    for first_set, second_set in split_pairs:
        overlap = np.intersect1d(splits[first_set], splits[second_set], assume_unique=True)
        if overlap.size > 0:
            raise ValueError(
                f"The {first_set} and {second_set} sets contain overlapping indices: {overlap}."
            )

    all_indices = np.concatenate(list(splits.values()))
    expected_indices = np.arange(sample_count)

    if not np.array_equal(np.sort(all_indices), expected_indices):
        missing_indices = np.setdiff1d(expected_indices, all_indices)
        raise ValueError(f"Unexpected index values.\nMissing index values: {missing_indices}.")

    expected_classes = np.unique(targets)

    for split_name, indices in splits.items():
        split_classes = np.unique(targets[indices])
        missing_classes = np.setdiff1d(expected_classes, split_classes)

        if missing_classes.size > 0:
            raise ValueError(
                f"The {split_name} split is missing classes: {missing_classes.tolist()}."
            )

    logger.info("Validation of the split completed successfully.")


def load_split(split_id: str, targets: np.ndarray, validation: bool = True):
    logger.info(f"Loading split {split_id}.")
    indices_path = split_dir / f"{split_id}.npz"

    if not indices_path.is_file():
        raise FileNotFoundError(f"The file at '{indices_path}' does not exist.")
    if validation:
        expected_arrays = {"train_indices", "validation_indices", "test_indices"}
    else:
        expected_arrays = {"train_indices", "test_indices"}

    with np.load(str(indices_path)) as split_data:
        missing_arrays = expected_arrays.difference(split_data.files)

        if missing_arrays:
            raise ValueError(f"Split is missing the following arrays: {missing_arrays}.")

        train_indices = split_data["train_indices"]
        if validation:
            validation_indices = split_data["validation_indices"]
        test_indices = split_data["test_indices"]

        logger.info("Split loaded successfully.")

    if validation:
        validate_split(targets, train_indices, test_indices, validation_indices)
        return train_indices, validation_indices, test_indices
    validate_split(targets, train_indices, test_indices)
    return train_indices, test_indices
