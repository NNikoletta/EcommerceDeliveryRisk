import json
import tempfile
import shutil
import logging
import pandas as pd
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
from enum import StrEnum

from ecommercedeliveryrisk.config import project_root
from ecommercedeliveryrisk.config import  ExpectedFiles, DownloadResult, Settings, FileManifest
from ecommercedeliveryrisk.utils import ensure_dir
from ecommercedeliveryrisk.checksums import calculate_local_sha256
from ecommercedeliveryrisk.validate_data import validate_data


logger = logging.getLogger(__name__)

class DownloadOutcome(StrEnum):
    DOWNLOADED = "downloaded"
    REPLACED = "replaced"
    RETAINED = "retained"

def download_raw_data(settings: Settings, replace_existing: bool = False, benchmark_manifest_name: str='benchmark_raw_data_manifest.json') -> DownloadOutcome:
    ensure_dir(settings.raw_data_dir)
    ensure_dir(settings.manifests_data_dir)

    if not any(settings.raw_data_dir.iterdir()):
        benchmark = load_manifest(manifests_dir=settings.manifests_data_dir,
                                  manifest_name=benchmark_manifest_name)
        if benchmark is not None:
            download_results = download_kaggle_dataset(settings=settings, dataset_version=benchmark['dataset_metadata']['dataset_version'])
        else:
            download_results = download_kaggle_dataset(settings=settings)

        outcome = DownloadOutcome.DOWNLOADED
    elif replace_existing:
        download_results = replace_raw_data(settings=settings,
                                            benchmark_manifest_name=benchmark_manifest_name)
        outcome = DownloadOutcome.REPLACED
    else:
        logger.info("Original raw data was retained.")
        return DownloadOutcome.RETAINED

    manifest = create_manifest(dataset_metadata=download_results.dataset_metadata,
                               dataset_version=download_results.dataset_version,
                               download_date=download_results.download_date,
                               settings=settings)
    save_manifest(manifest_name=benchmark_manifest_name, manifest=manifest, input_manifest_data_dir=settings.manifests_data_dir)

    logger.info("Raw-data operation completed: %s.", outcome.value)
    return outcome


def download_kaggle_dataset(settings: Settings, data_dir=None, dataset_version=None) -> DownloadResult:
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    if data_dir is None:
        data_dir = settings.raw_data_dir

    time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if dataset_version is None:
        dataset_version = json.loads(api.dataset_status(dataset=settings.kaggle_dataset, format='json(current_version_number)'))
        dataset_version = dataset_version['current_version_number']
        pinned_dataset = f"{settings.kaggle_dataset}/{dataset_version}"
    else:
        pinned_dataset = f"{settings.kaggle_dataset}/{dataset_version}"
    api.dataset_download_files(dataset=pinned_dataset, path=data_dir, unzip=True)
    all_csv_metadata = api.dataset_list_files(pinned_dataset).to_dict()['datasetFiles']

    download_results = DownloadResult(download_date=time,
                                      dataset_metadata=all_csv_metadata,
                                      dataset_version=dataset_version)

    return download_results


def load_manifest(manifests_dir, manifest_name) -> dict | None:
    if (manifests_dir / manifest_name).is_file():
        with (manifests_dir / manifest_name).open("r") as json_file:
            manifest = json.load(json_file)
        logger.info(f"{manifest_name} was loaded successfully.")
        return manifest
    else:
        logger.info(f"{manifest_name} was not found.")
        return None


def replace_raw_data(settings: Settings, benchmark_manifest_name: str):  # only replaces main Settings data
    benchmark = load_manifest(manifests_dir=settings.manifests_data_dir,
                              manifest_name=benchmark_manifest_name)
    if benchmark is not None:
        with tempfile.TemporaryDirectory(dir=settings.raw_data_dir.parent) as tmp_path:
            tmp_raw_data_dir = Path(tmp_path)
            download_results = download_kaggle_dataset(settings=settings,
                                                       data_dir=tmp_raw_data_dir,
                                                       dataset_version=benchmark['dataset_metadata']['dataset_version'])

            validate_data(data_dir=tmp_raw_data_dir,
                          manifests_dir=settings.manifests_data_dir,
                          benchmark_manifest_name=benchmark_manifest_name)

            shutil.rmtree(settings.raw_data_dir)
            shutil.move(tmp_raw_data_dir, settings.raw_data_dir)
    else:
        shutil.rmtree(settings.raw_data_dir)
        ensure_dir(settings.raw_data_dir)
        download_results = download_kaggle_dataset(settings=settings)

    logger.info("Dataset was replaced successfully.")
    return download_results


def create_manifest(dataset_metadata: list[dict], dataset_version: int, download_date: str, settings: Settings) -> dict:
    expected_files = asdict(ExpectedFiles())
    manifest = dict()
    manifest['dataset_metadata'] = {'dataset_name': settings.kaggle_dataset,
                                    'dataset_version': dataset_version}
    for file_id, file_name in expected_files.items():
        file_path = settings.raw_data_dir / file_name
        size_byte = None
        creation_date = None
        if file_path.is_file():
            column_names = pd.read_csv(file_path, nrows=0).columns.tolist()
            column_count = len(column_names)
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

            file_manifest: FileManifest = {'file_name': file_name,
                                           'dataset': settings.kaggle_dataset,
                                           'dataset_version': dataset_version,
                                           'file_path': str(file_path.relative_to(project_root).as_posix()),
                                           'sha256': calculate_local_sha256(file_path),
                                           'size_byte': size_byte,
                                           'download_date': download_date,
                                           'dataset_created': creation_date,
                                           'column_count': column_count,
                                           'row_count': row_count,
                                           'column_names': column_names}
            manifest[file_id] = file_manifest
        else:
            raise FileNotFoundError(f"File {file_name} not found.")

    logger.info("Manifest created successfully.")
    return manifest


def save_manifest(manifest_name: str, manifest: dict, input_manifest_data_dir) -> None:
    ensure_dir(input_manifest_data_dir)
    file_path = input_manifest_data_dir / manifest_name

    if file_path.is_file():
        logger.info(f"Manifest under the name: '{manifest_name}' already exists; new manifest will be saved as 'tmp_raw_data_manifest.json'.")
        manifest_name = "tmp_raw_data_manifest.json"
        file_path = input_manifest_data_dir / manifest_name
        if file_path.is_file():
            logger.info(f"Temporary manifest already exists and will be overwritten with the newly created manifest.")
            file_path.unlink()
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(manifest, json_file, indent=2)
        logger.info("Manifest has been saved successfully.")
    else:
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(manifest, json_file, indent=2)
        logger.info("Manifest has been saved successfully.")
    return None

