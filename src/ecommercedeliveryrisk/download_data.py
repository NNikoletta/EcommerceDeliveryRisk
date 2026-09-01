from dataclasses import asdict
from kaggle.api.kaggle_api_extended import KaggleApi

from src.ecommercedeliveryrisk.config import raw_data_dir, kaggle_dataset_name, ExpectedDatasets
from src.ecommercedeliveryrisk.utils import ensure_dir


def download_raw_data() -> None:
    ensure_dir(raw_data_dir)
    datasets = ExpectedDatasets()

    api = KaggleApi()
    api.authenticate()

    for _, dataset_name in asdict(datasets).items():
        file_path = raw_data_dir/dataset_name
        if file_path.is_file():
            print(f"File {dataset_name} already exists and will not be overwritten.")
        else:
            api.dataset_download_files(dataset=kaggle_dataset_name, path=raw_data_dir, unzip=True)
            print(f"File {dataset_name} downloaded successfully.")
