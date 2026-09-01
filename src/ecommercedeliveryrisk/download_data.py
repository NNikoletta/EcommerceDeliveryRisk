import json
from datetime import datetime
from kaggle.api.kaggle_api_extended import KaggleApi
from dataclasses import asdict

from ecommercedeliveryrisk.config import project_root
from src.ecommercedeliveryrisk.config import raw_data_dir, kaggle_dataset_name, ExpectedFiles, manifests_data_dir
from src.ecommercedeliveryrisk.utils import ensure_dir
from src.ecommercedeliveryrisk.checksums import calculate_local_sha256


def download_raw_data(replace_existing: bool = False, manifest_name: str='raw_data_manifest.json') -> dict | None:
    expected_files = asdict(ExpectedFiles())
    manifest = {}
    manifest_path = manifests_data_dir / manifest_name

    ensure_dir(raw_data_dir)
    ensure_dir(manifests_data_dir)

    api = KaggleApi()
    api.authenticate()

    if not any(raw_data_dir.iterdir()):
        download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        api.dataset_download_files(dataset=kaggle_dataset_name, path=raw_data_dir, unzip=True)
        dataset_metadata = api.dataset_list_files(kaggle_dataset_name).to_dict()['datasetFiles']
        print(f"Kaggle's '{kaggle_dataset_name}' dataset has been downloaded successfully.")
        if manifest_path.is_file():
            manifest_path.unlink()
    else:
        if replace_existing:
            print(f"Directory is not empty and will be overwritten.")
            for file in raw_data_dir.iterdir():
                if file.is_file():
                    file.unlink()
            download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            api.dataset_download_files(dataset=kaggle_dataset_name, path=raw_data_dir, unzip=True)
            dataset_metadata = api.dataset_list_files(kaggle_dataset_name).to_dict()['datasetFiles']
            print(f"Kaggle's '{kaggle_dataset_name}' dataset has been replaced successfully.")
            if manifest_path.is_file():
                manifest_path.unlink()
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
                                 'file_path': str(file_path.relative_to(project_root)),
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
        raise FileExistsError(
            f"Manifest under the name: '{manifest_name}' already exists."
        )
    else:
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(manifest, json_file, indent=2)
        print("Manifest has been saved successfully.")


