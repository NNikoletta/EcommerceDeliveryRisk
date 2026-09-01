import json
from datetime import datetime, timezone
from kaggle.api.kaggle_api_extended import KaggleApi
from dataclasses import asdict

from ecommercedeliveryrisk.config import project_root
from ecommercedeliveryrisk.config import raw_data_dir, KAGGLE_DATASET, ExpectedFiles, manifests_data_dir
from ecommercedeliveryrisk.utils import ensure_dir
from ecommercedeliveryrisk.checksums import calculate_local_sha256


def download_raw_data(replace_existing: bool = False, manifest_name: str='raw_data_manifest.json') -> dict | None:
    expected_files = asdict(ExpectedFiles())
    manifest = {}
    ensure_dir(raw_data_dir)

    api = KaggleApi()
    api.authenticate()

    if not any(raw_data_dir.iterdir()):
        download_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        api.dataset_download_files(dataset=KAGGLE_DATASET, path=raw_data_dir, unzip=True)
        dataset_metadata = api.dataset_list_files(KAGGLE_DATASET).to_dict()['datasetFiles']
        print(f"Kaggle's '{KAGGLE_DATASET}' dataset has been downloaded successfully.")
    else:
        if replace_existing:
            print(f"Directory is not empty and will be overwritten.")
            for file in raw_data_dir.iterdir():
                if file.is_file():
                    file.unlink()
            download_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            api.dataset_download_files(dataset=KAGGLE_DATASET, path=raw_data_dir, unzip=True)
            dataset_metadata = api.dataset_list_files(KAGGLE_DATASET).to_dict()['datasetFiles']
            print(f"Kaggle's '{KAGGLE_DATASET}' dataset has been replaced successfully.")
        else:
            print(f"Directory is not empty and will not be overwritten.")
            return None

    for file_id, file_name in expected_files.items():
        file_path = raw_data_dir / file_name
        if file_path.is_file():
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
                                 'file_path': str(file_path.relative_to(project_root).as_posix()),
                                 'sha256': calculate_local_sha256(file_path),
                                 'size_byte': size_byte,
                                 'download_time': download_time,
                                 'dataset_created': creation_date}

    save_manifest(manifest_name=manifest_name, manifest=manifest)
    return None


def save_manifest(manifest_name: str, manifest: dict) -> None:
    ensure_dir(manifests_data_dir)
    file_path = manifests_data_dir / manifest_name

    if file_path.is_file():
        print(f"Manifest under the name: '{manifest_name}' already exists.")
        return None
    else:
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(manifest, json_file, indent=2)
        print("Manifest has been saved successfully.")

    return None


