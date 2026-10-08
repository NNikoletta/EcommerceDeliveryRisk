from ecommercedeliveryrisk.config import SplitConfig
from ecommercedeliveryrisk.get_model_data import load_dataset
from ecommercedeliveryrisk.prepare_data import create_evaluation_split, save_split


def model_pipeline(model_name):
    split_config = SplitConfig(
        split_id="fixed_pipeline_test_split",
        split_seed=8102026,
        test_fraction=0.1,
        validation_fraction=0.1,
    )
    features, targets = load_dataset(model_name=model_name)
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
    print(features.shape)
