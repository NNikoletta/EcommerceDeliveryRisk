import json
from dataclasses import asdict
from pathlib import Path

from ecommercedeliveryrisk.config import raw_data_dir, manifests_data_dir, ExpectedFiles
from ecommercedeliveryrisk.checksums import calculate_local_sha256

def validate_raw_data() -> None:
    manifest = 'benchmark_raw_data_manifest.json'
    config = asdict(ExpectedFiles())
    expected_file_count = len(list([i for i in config.keys()]))

    if not raw_data_dir.exists():
        raise FileNotFoundError(f"The file directory '{raw_data_dir}' does not exist.")

    if not any(raw_data_dir.iterdir()):
        raise FileNotFoundError(f"The file directory '{raw_data_dir}' does not contain any files.")

    file_count = len(list(raw_data_dir.iterdir()))

    if file_count != expected_file_count:
        raise FileNotFoundError(f"Found {file_count} files in {raw_data_dir}.\n"
                                f"                   Expected file count is {expected_file_count}.")

    for key, file_name in config.items():
        file_path = raw_data_dir / file_name
        if not file_path.is_file():
            raise FileNotFoundError(f"{file_name} is not a file.")

    manifest_path = Path(manifests_data_dir / manifest)
    with manifest_path.open("r") as json_file:
        manifest_data = json.load(json_file)

    for key, file_name in config.items():
        file_path = raw_data_dir / file_name
        if manifest_data[key]['size_byte'] != file_path.stat().st_size:
            raise ValueError(f"The size of the '{file_name}' file does not match the expected size.\n"
                             f"Expected size is {manifest_data[key]['size_byte']} bytes.\n"
                             f"Found size {file_path.stat().st_size} bytes.")
        if manifest_data[key]['sha256'] != calculate_local_sha256(file_path):
            raise ValueError("The SHA-256 hash doesn't match the expected value.")

    print("Datasets successfully validated.")

