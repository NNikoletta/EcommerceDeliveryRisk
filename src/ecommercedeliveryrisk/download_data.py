import json
import shutil
import pandas as pd
from datetime import datetime, timezone
from kaggle.api.kaggle_api_extended import KaggleApi
from dataclasses import asdict

from ecommercedeliveryrisk.config import project_root
from ecommercedeliveryrisk.config import raw_data_dir, KAGGLE_DATASET, ExpectedFiles, manifests_data_dir
from ecommercedeliveryrisk.utils import ensure_dir
from ecommercedeliveryrisk.checksums import calculate_local_sha256
from ecommercedeliveryrisk.validate_data import validate_raw_data


def download_raw_data(replace_existing: bool = False, manifest_name: str='benchmark_raw_data_manifest.json') -> dict | None:
    ensure_dir(raw_data_dir)

    api = KaggleApi()
    api.authenticate()

    def download(data_dir=raw_data_dir, version_data=None) -> tuple[str, dict, float|int]:
        time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if version_data is None:
            version_data = json.loads(api.dataset_status(dataset=KAGGLE_DATASET, format='json(current_version_number)'))
            version_data = version_data['current_version_number']
            pinned_dataset = f"{KAGGLE_DATASET}/{version_data}"
        else:
            pinned_dataset = f"{KAGGLE_DATASET}/{version_data}"
        api.dataset_download_files(dataset=pinned_dataset, path=data_dir, unzip=True)
        all_csv_metadata = api.dataset_list_files(pinned_dataset).to_dict()['datasetFiles']
        return time, all_csv_metadata, version_data

    if not any(raw_data_dir.iterdir()):
        if (manifests_data_dir / "benchmark_raw_data_manifest.json").is_file():
            print("Benchmark manifest found, downloading dataset accordingly.")
            with (manifests_data_dir / "benchmark_raw_data_manifest.json").open("r") as json_file:
                benchmark = json.load(json_file)
                download_time, dataset_metadata, version_number = download(benchmark['dataset_metadata']['dataset_version'])
        else:
            print("Benchmark is not available, downloading dataset and creating benchmark.")
            download_time, dataset_metadata, version_number = download()
        print(f"Kaggle's '{KAGGLE_DATASET}' dataset has been downloaded successfully.")
    else:
        if replace_existing:
            print(f"Directory is not empty and will be overwritten.")
            if (manifests_data_dir/"benchmark_raw_data_manifest.json").is_file():
                with (manifests_data_dir/"benchmark_raw_data_manifest.json").open("r") as json_file:
                    benchmark = json.load(json_file)
                tmp_raw_data_dir = raw_data_dir / "_tmp"
                ensure_dir(tmp_raw_data_dir)
                download_time, dataset_metadata, version_number = download(data_dir=tmp_raw_data_dir, version_data=benchmark['dataset_metadata']['dataset_version'])
                validate_raw_data(tmp_raw_data_dir)
                for file in raw_data_dir.iterdir():
                    if file.is_file():
                        file.unlink()

                for file in tmp_raw_data_dir.iterdir():
                    move_to_path = raw_data_dir / file.name
                    file.rename(move_to_path)

                shutil.rmtree(tmp_raw_data_dir)
            else:
                for file in raw_data_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                print("Benchmark is not available, downloading dataset and creating benchmark.")
                download_time, dataset_metadata, version_number = download()
            print(f"Kaggle's '{KAGGLE_DATASET}' dataset has been replaced successfully.")
        else:
            print(f"Directory is not empty and will not be overwritten.")
            return None

    manifest = create_manifest(dataset_metadata, version_number, download_time)
    save_manifest(manifest_name=manifest_name, manifest=manifest)
    return None


def create_manifest(dataset_metadata: dict, version_number: float|int, download_time: str) -> dict:
    manifest = dict()
    manifest['dataset_metadata'] = {'dataset_name': KAGGLE_DATASET,
                                    'dataset_version': version_number}
    expected_files = asdict(ExpectedFiles())
    for file_id, file_name in expected_files.items():
        file_path = raw_data_dir / file_name
        if file_path.is_file():
            column_count = len(pd.read_csv(file_path, nrows=0).columns.tolist())
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

            manifest[file_id] = {'file_name': file_name,
                                 'dataset': KAGGLE_DATASET,
                                 'dataset_version': version_number,
                                 'file_path': str(file_path.relative_to(project_root).as_posix()),
                                 'sha256': calculate_local_sha256(file_path),
                                 'size_byte': size_byte,
                                 'download_time': download_time,
                                 'dataset_created': creation_date,
                                 'column_count': column_count,
                                 'row_count': row_count}

    return manifest


def save_manifest(manifest_name: str, manifest: dict) -> None:
    ensure_dir(manifests_data_dir)
    file_path = manifests_data_dir / manifest_name

    if file_path.is_file():
        print(f"Manifest under the name: '{manifest_name}' already exists; new manifest will be saved as 'tmp_raw_data_manifest.json'.")
        manifest_name = "tmp_raw_data_manifest.json"
        file_path = manifests_data_dir / manifest_name
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

