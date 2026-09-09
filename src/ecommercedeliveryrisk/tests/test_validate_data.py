import json
from copy import deepcopy
from dataclasses import dataclass

import pytest

import ecommercedeliveryrisk.validate_data as validation_module
from ecommercedeliveryrisk.checksums import calculate_local_sha256
from ecommercedeliveryrisk.config import Settings


@dataclass
class MockExpectedFiles:
    orders: str = "orders.csv"

@pytest.fixture
def valid_case(tmp_path, monkeypatch):
    settings = Settings(kaggle_dataset='test-owner/test-dataset',
                        raw_data_dir=tmp_path/"raw",
                        manifests_data_dir=tmp_path/"manifests")

    # noinspection unresolved-references
    monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)

    data_dir = settings.raw_data_dir
    data_dir.mkdir()

    file_path = data_dir / "orders.csv"
    file_path.write_text("order_id,status\n"
                         "1, placed\n"
                         "2, processed\n", encoding='utf-8')

    manifests_dir = settings.manifests_data_dir
    manifests_dir.mkdir()
    benchmark_path = manifests_dir / "benchmark_raw_data_manifest.json"
    benchmark = {'dataset_metadata': {'dataset_name': settings.kaggle_dataset,
                                      'dataset_version': 1},
                 'orders': {'file_name': 'orders.csv',
                            'dataset': settings.kaggle_dataset,
                            'dataset_version': 1,
                            'file_path': str(file_path.relative_to(tmp_path).as_posix()),
                            'sha256': calculate_local_sha256(file_path),
                            'size_byte': file_path.stat().st_size,
                            'download_date': "2026-08-09T00:00:00Z",
                            'dataset_created': "2026-01-01T00:00:00Z",
                            'column_count': 2,
                            'row_count': 2,
                            'column_names': ['order_id', 'status']}
                 }

    benchmark_path.write_text(json.dumps(benchmark), encoding='utf-8')
    return settings, benchmark, benchmark_path


def test_validate_data_with_valid_data(valid_case):
    settings, _, _ = valid_case

    validation_module.validate_data(settings.raw_data_dir, settings.manifests_data_dir)


def test_compare_manifests_with_valid_data(valid_case):
    settings, benchmark, benchmark_path = valid_case
    temporary_benchmark = deepcopy(benchmark)
    temporary_path = settings.manifests_data_dir / "tmp_raw_data_manifest.json"
    temporary_path.write_text(json.dumps(temporary_benchmark), encoding='utf-8')

    validation_module.compare_manifests(settings.manifests_data_dir)


@pytest.mark.parametrize(
    "key,wrong_value,error,message",
    [
        ("file_name", "wrong.csv", FileNotFoundError, "File name does not match"),
        ("size_byte", -1, ValueError, "size.*does not match"),
        ("row_count", 3, ValueError, "number of rows"),
        ("column_count", 3, ValueError, "number of columns"),
        ("sha256", "wrong_sha256", ValueError, "SHA-256")
    ]
)
def test_validate_data_with_wrong_file_metric(valid_case, key,
                                                  wrong_value, error,
                                                  message):
    settings, benchmark, benchmark_path = valid_case

    benchmark['orders'][key] = wrong_value
    benchmark_path.write_text(json.dumps(benchmark), encoding='utf-8')

    with pytest.raises(error, match=message):
        validation_module.validate_data(data_dir=settings.raw_data_dir,
                                            manifests_dir=settings.manifests_data_dir)


@pytest.mark.parametrize(
    "file_id,key,wrong_value,error,message",
    [
        ("dataset_metadata", "dataset_name", "wrong_dataset", ValueError, "The manifest data does not match the benchmark data.\n"),
        ("dataset_metadata", "dataset_version", -1, ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "file_name", "wrong.csv", ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "dataset", "wrong_dataset", ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "dataset_version", -1, ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "sha256", "wrong_sha256", ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "size_byte", -1, ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "dataset_created", "wrong_date", ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "column_count", 3, ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "row_count", 3, ValueError, "The manifest data does not match the benchmark data.\n"),
        ("orders", "column_names", ["wrong_id", "wrong_status"], ValueError, "The manifest data does not match the benchmark data.\n")
    ]
)
def test_compare_manifests_with_wrong_file_metric(valid_case,
                                                  file_id, key,
                                                  wrong_value, error,
                                                  message):
    settings, benchmark, benchmark_path = valid_case

    temporary_benchmark = deepcopy(benchmark)
    temporary_path = settings.manifests_data_dir / "tmp_raw_data_manifest.json"

    temporary_benchmark[file_id][key] = wrong_value
    temporary_path.write_text(json.dumps(temporary_benchmark), encoding='utf-8')

    with pytest.raises(error, match=message):
        validation_module.compare_manifests(manifests_dir=settings.manifests_data_dir)


#  Testing with wrong directories
@pytest.mark.parametrize(
    "directory_available,files_available",
    [
        pytest.param(False, False, id="no-dir-no-files"),
        pytest.param(True, False, id="yes-dir-no-files")
    ]
)
def test_validate_data(valid_case, directory_available, files_available):
    settings, _, _ = valid_case
    data_dir = settings.raw_data_dir
    if not directory_available:
        for file in settings.raw_data_dir.iterdir():
            file.unlink()
        settings.raw_data_dir.rmdir()
        with pytest.raises(FileNotFoundError, match=f"The file directory '.*' does not exist."):
            validation_module.validate_data(data_dir=data_dir,
                                            manifests_dir=settings.manifests_data_dir)

    if directory_available and not files_available:
        for file in settings.raw_data_dir.iterdir():
            file.unlink()
        with pytest.raises(FileNotFoundError, match=f"The file directory '.*' does not contain any files."):
            validation_module.validate_data(data_dir=settings.raw_data_dir,
                                            manifests_dir=settings.manifests_data_dir)

