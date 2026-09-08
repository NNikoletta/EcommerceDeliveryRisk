import json
import shutil
import pandas as pd
from datetime import datetime, timezone
from kaggle.api.kaggle_api_extended import KaggleApi  # noinspection PyUnresolvedReferences
from dataclasses import asdict
from pathlib import Path

from ecommercedeliveryrisk.config import project_root
from ecommercedeliveryrisk.config import  (raw_data_dir, KAGGLE_DATASET, ExpectedFiles,
                                           manifests_data_dir, DownloadResult)
from ecommercedeliveryrisk.utils import ensure_dir
from ecommercedeliveryrisk.checksums import calculate_local_sha256
from ecommercedeliveryrisk.validate_data import validate_raw_data


def download_kaggle_dataset(data_dir, dataset_version=None) -> DownloadResult:
    api = KaggleApi()
    api.authenticate()

    time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if dataset_version is None:
        dataset_version = json.loads(api.dataset_status(dataset=KAGGLE_DATASET, format='json(current_version_number)'))
        dataset_version = dataset_version['current_version_number']
        pinned_dataset = f"{KAGGLE_DATASET}/{dataset_version}"
    else:
        pinned_dataset = f"{KAGGLE_DATASET}/{dataset_version}"
    api.dataset_download_files(dataset=pinned_dataset, path=data_dir, unzip=True)
    all_csv_metadata = api.dataset_list_files(pinned_dataset).to_dict()['datasetFiles']

    download_results = DownloadResult(download_date=time,
                                       dataset_metadata=all_csv_metadata,
                                       dataset_version=dataset_version)
    return download_results

def download_raw_data(input_raw_data_dir = None, replace_existing: bool = False, manifest_name: str='benchmark_raw_data_manifest.json') -> dict | None:
    if input_raw_data_dir is None:
        input_raw_data_dir = raw_data_dir

    ensure_dir(input_raw_data_dir)

    if not any(input_raw_data_dir.iterdir()):
        if Path(str(manifests_data_dir) + "/benchmark_raw_data_manifest.json").is_file():
            print("Benchmark manifest found, downloading dataset accordingly.")
            with (manifests_data_dir / "benchmark_raw_data_manifest.json").open("r") as json_file:
                benchmark = json.load(json_file)
                download_results = download_kaggle_dataset(data_dir=input_raw_data_dir, dataset_version=benchmark['dataset_metadata']['dataset_version'])
        else:
            print("Benchmark is not available, downloading dataset and creating benchmark.")
            download_results = download_kaggle_dataset(data_dir=input_raw_data_dir)
        print(f"Kaggle's '{KAGGLE_DATASET}' dataset has been downloaded successfully.")
    else:
        if replace_existing:
            print(f"Directory is not empty and will be overwritten.")
            if (manifests_data_dir/"benchmark_raw_data_manifest.json").is_file():
                with (manifests_data_dir/"benchmark_raw_data_manifest.json").open("r") as json_file:
                    benchmark = json.load(json_file)
                tmp_raw_data_dir = input_raw_data_dir / "_tmp"
                ensure_dir(tmp_raw_data_dir)
                download_results = download_kaggle_dataset(data_dir=tmp_raw_data_dir, dataset_version=benchmark['dataset_metadata']['dataset_version'])
                validate_raw_data(tmp_raw_data_dir)
                for file in input_raw_data_dir.iterdir():
                    if file.is_file():
                        file.unlink()

                for file in tmp_raw_data_dir.iterdir():
                    move_to_path = input_raw_data_dir / file.name
                    file.rename(move_to_path)

                shutil.rmtree(tmp_raw_data_dir)
            else:
                for file in input_raw_data_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                print("Benchmark is not available, downloading dataset and creating benchmark.")
                download_results = download_kaggle_dataset(data_dir=input_raw_data_dir,)
            print(f"Kaggle's '{KAGGLE_DATASET}' dataset has been replaced successfully.")
        else:
            print(f"Directory is not empty and will not be overwritten.")
            return None

    manifest = create_manifest(dataset_metadata=download_results.dataset_metadata,
                               dataset_version=download_results.dataset_version,
                               download_date=download_results.download_date,
                               input_raw_data_dir=input_raw_data_dir)
    save_manifest(manifest_name=manifest_name, manifest=manifest)
    return None


def create_manifest(dataset_metadata: list[dict], dataset_version: float|int, download_date: str, input_raw_data_dir=None) -> dict:
    if input_raw_data_dir is None:
        input_raw_data_dir = raw_data_dir
    manifest = dict()
    manifest['dataset_metadata'] = {'dataset_name': KAGGLE_DATASET,
                                    'dataset_version': dataset_version}
    expected_files = asdict(ExpectedFiles())
    for file_id, file_name in expected_files.items():
        file_path = input_raw_data_dir / file_name
        size_byte = None
        creation_date = None
        if file_path.is_file():
            expected_columns = pd.read_csv(file_path, nrows=0).columns.tolist()
            column_count = len(expected_columns)
            row_count = pd.read_csv(file_path, usecols=[0]).shape[0]
            for metadata in dataset_metadata:
                if metadata['name'] == file_name:
                    creation_date = metadata['creationDate']
                    if metadata['totalBytes'] == file_path.stat().st_size:
                        size_byte = file_path.stat().st_size
                    else:
                        raise ValueError(
                            f"The downloaded {file_name} file size does not match the expected file size.\n"
                            f"Expected size: {metadata['totalBytes']}\n byte."
                            f"Found size: {file_path.stat().st_size} byte")

            if size_byte is None:
                raise ValueError(f"Kaggle metadata is missing.\n"
                                 f"The expected file size for {file_name} file was not available to extract.")
            if creation_date is None:
                raise ValueError(f"Kaggle metadata is missing.\n"
                                 f"The creation date of the {file_name} file was not available to extract.")
            manifest[file_id] = {'file_name': file_name,
                                 'dataset': KAGGLE_DATASET,
                                 'dataset_version': dataset_version,
                                 'file_path': str(file_path.relative_to(project_root).as_posix()),
                                 'sha256': calculate_local_sha256(file_path),
                                 'size_byte': size_byte,
                                 'download_date': download_date,
                                 'dataset_created': creation_date,
                                 'column_count': column_count,
                                 'row_count': row_count,
                                 'expected_columns': expected_columns}
        else:
            raise FileNotFoundError(f"File {file_name} not found.")
    return manifest


def save_manifest(manifest_name: str, manifest: dict, input_manifest_data_dir=None) -> None:
    if input_manifest_data_dir is None:
        input_manifest_data_dir = manifests_data_dir
    ensure_dir(input_manifest_data_dir)
    file_path = input_manifest_data_dir / manifest_name

    if file_path.is_file():
        print(f"Manifest under the name: '{manifest_name}' already exists; new manifest will be saved as 'tmp_raw_data_manifest.json'.")
        manifest_name = "tmp_raw_data_manifest.json"
        file_path = input_manifest_data_dir / manifest_name
        if file_path.is_file():
            print(f"Temporary manifest already exists and will be overwritten with the newly created manifest.")
            file_path.unlink()
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(manifest, json_file, indent=2)
        print("Manifest has been saved successfully.")
    else:
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(manifest, json_file, indent=2)
        print("Manifest has been saved successfully.")
    return None

