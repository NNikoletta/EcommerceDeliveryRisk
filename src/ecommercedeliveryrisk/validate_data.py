import json
import pandas as pd
from dataclasses import asdict
from pathlib import Path

from ecommercedeliveryrisk.config import ExpectedFiles
from ecommercedeliveryrisk.checksums import calculate_local_sha256


def validate_raw_data(data_dir, manifests_dir) -> None:
    manifest = 'benchmark_raw_data_manifest.json'

    config = asdict(ExpectedFiles())
    expected_file_count = len(list([i for i in config.keys()]))

    if not data_dir.exists():
        raise FileNotFoundError(f"The file directory '{data_dir}' does not exist.")

    if not any(data_dir.iterdir()):
        raise FileNotFoundError(f"The file directory '{data_dir}' does not contain any files.")

    file_count = len(list(data_dir.iterdir()))

    if file_count != expected_file_count:
        raise FileNotFoundError(f"Found {file_count} files in {data_dir}.\n"
                                f"Expected file count is {expected_file_count}.")

    for key, file_name in config.items():
        file_path = data_dir / file_name
        if not file_path.is_file():
            raise FileNotFoundError(f"{file_name} is not a file.")

    manifest_path = Path(manifests_dir / manifest)
    with manifest_path.open("r") as json_file:
        manifest_data = json.load(json_file)

    for key, file_name in config.items():
        file_path = data_dir / file_name
        if file_path.name != manifest_data[key]['file_name']:
            raise FileNotFoundError(f"File name does not match the expected file name.\n"
                                    f"Expected {manifest_data[key]['file_name']}\n"
                                    f"Found {file_name}.")

        if file_path.stat().st_size != manifest_data[key]['size_byte']:
            raise ValueError(f"The size of the '{file_name}' file does not match the expected size.\n"
                             f"Expected size is {manifest_data[key]['size_byte']} bytes.\n"
                             f"Found size {file_path.stat().st_size} bytes.")

        found_row_count = pd.read_csv(file_path, usecols=[0]).shape[0]
        if found_row_count != manifest_data[key]['row_count']:
            raise ValueError(f"The number of rows of the '{file_name}' file does not match the expected number of rows.\n"
                             f"Expected {manifest_data[key]['row_count']} rows.\n"
                             f"Found {found_row_count} rows.\n")

        found_column_count = len(pd.read_csv(file_path, nrows=0).columns.tolist())
        if found_column_count != manifest_data[key]['column_count']:
            raise ValueError(f"The number of columns of the '{file_name}' file does not match the expected number of columns.\n"
                             f"Expected {manifest_data[key]['column_count']} columns.\n"
                             f"Found {found_column_count} columns.\n")

        if calculate_local_sha256(file_path) != manifest_data[key]['sha256']:
            raise ValueError("The SHA-256 hash doesn't match the expected value.")

    print("Datasets successfully validated.")

def compare_manifests(manifests_dir):
    benchmark_manifest = 'benchmark_raw_data_manifest.json'
    tmp_manifest = 'tmp_raw_data_manifest.json'

    benchmark_manifest_path = manifests_dir / benchmark_manifest
    tmp_manifest_path = manifests_dir / tmp_manifest

    if tmp_manifest_path.is_file() and benchmark_manifest_path.is_file():
        with benchmark_manifest_path.open("r") as json_file:
            benchmark_manifest_data = json.load(json_file)
        with tmp_manifest_path.open("r") as json_file:
            tmp_manifest_data = json.load(json_file)

        if tmp_manifest_data.keys() != benchmark_manifest_data.keys():
            raise ValueError("The manifest data does not match the benchmark data.\n")

        for benchmark_file_id, benchmark_file_manifest in benchmark_manifest_data.items():
            tmp_file_manifest = tmp_manifest_data[benchmark_file_id]

            if benchmark_file_manifest.keys() != tmp_file_manifest.keys():
                raise ValueError("The manifest data does not match the benchmark data.\n")

            for benchmark_key, benchmark_value in benchmark_file_manifest.items():
                if benchmark_key != 'download_date' and benchmark_key != 'file_path':
                    if benchmark_value != tmp_file_manifest[benchmark_key]:
                        raise ValueError(f"The manifest data does not match the benchmark data.\n"
                                         f"Expected key-value pair: {benchmark_key}-{benchmark_value}\n"
                                         f"Found key-value pair: {benchmark_key}-{tmp_file_manifest[benchmark_key]}\n")
    else:
        print("The required files were not found.\n"
              "Comparison cannot be made.")

