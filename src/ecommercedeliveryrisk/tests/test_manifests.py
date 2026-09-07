import json
from dataclasses import dataclass
from unittest.mock import Mock

import pytest

import ecommercedeliveryrisk.download_data as download_module


@dataclass
class MockExpectedFiles:
    orders: str = "orders.csv"


def test_create_manifest(tmp_path, monkeypatch) -> None:
    test_raw_dir = tmp_path / "raw"
    test_raw_dir.mkdir()

    test_file = test_raw_dir / "orders.csv"
    test_file.write_text("order_id,status\n"
                         "1,delivered\n"
                         "2,shipped\n", encoding="utf-8")

    download_time = "2026-09-07T12:00:00.000000Z"

    dataset_metadata = [{'name': 'orders.csv',
                         'creationDate': "2026-01-01T00:00:00Z",
                         'totalBytes': test_file.stat().st_size}]

    mock_calculate_local_sha256 = Mock(return_value="mock_sha256")

    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "ExpectedFiles", MockExpectedFiles)

    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "project_root", tmp_path)

    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "calculate_local_sha256", mock_calculate_local_sha256)

    manifest = download_module.create_manifest(dataset_metadata=dataset_metadata,
                                                version_number=1,
                                                download_time=download_time,
                                                input_raw_data_dir=test_raw_dir)

    expected_manifest = {'dataset_metadata': {'dataset_name': download_module.KAGGLE_DATASET,
                                              'dataset_version': 1},
                         'orders' : {'file_name': 'orders.csv',
                                     'dataset': download_module.KAGGLE_DATASET,
                                     'dataset_version': 1,
                                     'file_path': 'raw/orders.csv',
                                     'sha256': 'mock_sha256',
                                     'size_byte': test_file.stat().st_size,
                                     'download_time': download_time,
                                     'dataset_created': '2026-01-01T00:00:00Z',
                                     'column_count': 2,
                                     'row_count': 2,
                                     'expected_columns': ['order_id', 'status']}
                         }

    assert manifest == expected_manifest

    mock_calculate_local_sha256.assert_called_once_with(test_file)


def test_create_manifest_raise_error_if_file_size_is_wrong(tmp_path, monkeypatch) -> None:
    test_raw_dir = tmp_path / "raw"
    test_raw_dir.mkdir()

    test_file = test_raw_dir / "orders.csv"
    test_file.write_text("order_id,status\n"
                         "1,delivered\n"
                         "2,shipped\n", encoding="utf-8")

    dataset_metadata = [{'name': 'orders.csv',
                         'creationDate': "2026-01-01T00:00:00Z",
                         'totalBytes': test_file.stat().st_size + 1}]

    download_time = "2026-09-07T12:00:00.000000Z"

    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "ExpectedFiles", MockExpectedFiles)

    with pytest.raises(ValueError, match="file size does not match"):
        download_module.create_manifest(dataset_metadata=dataset_metadata, version_number=1,
                                        download_time=download_time, input_raw_data_dir=test_raw_dir)


def test_save_manifest_creates_directory_and_file(tmp_path) -> None:
    test_manifest_dir = tmp_path / "manifests"

    manifest = {'dataset_metadata': {'dataset_version': 1}}

    download_module.save_manifest(manifest_name="benchmark_raw_data_manifest.json",
                                  manifest=manifest,
                                  input_manifest_data_dir=test_manifest_dir)

    saved_file = test_manifest_dir / "benchmark_raw_data_manifest.json"

    assert test_manifest_dir.is_dir()
    assert saved_file.is_file()

    saved_content = json.loads(saved_file.read_text(encoding="utf-8"))

    assert saved_content == manifest

def test_save_manifest_preserves_existing_manifest(tmp_path) -> None:
    test_manifest_dir = tmp_path / "manifests"
    test_manifest_dir.mkdir()

    benchmark_path = test_manifest_dir / "benchmark_raw_data_manifest.json"

    original_manifest = {'dataset_metadata': {'dataset_version': 1}}

    new_manifest = {'dataset_metadata': {'dataset_version': 2}}

    benchmark_path.write_text(json.dumps(original_manifest), encoding="utf-8")

    download_module.save_manifest(manifest_name="benchmark_raw_data_manifest.json",
                                  manifest=new_manifest,
                                  input_manifest_data_dir=test_manifest_dir)

    temporary_manifest_path = test_manifest_dir / "tmp_raw_data_manifest.json"

    saved_benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))

    assert saved_benchmark == original_manifest

    assert temporary_manifest_path.is_file()

    saved_temporary_manifest = json.loads(temporary_manifest_path.read_text(encoding="utf-8"))

    assert saved_temporary_manifest == new_manifest


def test_save_manifest_overwrites_existing_manifest(tmp_path) -> None:
    test_manifest_dir = tmp_path / "manifests"
    test_manifest_dir.mkdir()

    benchmark_path = test_manifest_dir / "benchmark_raw_data_manifest.json"

    original_manifest = {'dataset_metadata': {'dataset_version': 1}}

    benchmark_path.write_text(json.dumps(original_manifest), encoding="utf-8")

    temporary_manifest_path = test_manifest_dir / "tmp_raw_data_manifest.json"

    tmp_manifest = {'dataset_metadata': {'dataset_version': 2}}

    temporary_manifest_path.write_text(json.dumps(tmp_manifest), encoding="utf-8")

    new_tmp_manifest = {'dataset_metadata': {'dataset_version': 3}}

    download_module.save_manifest(manifest_name="benchmark_raw_data_manifest.json",
                                  manifest=new_tmp_manifest,
                                  input_manifest_data_dir=test_manifest_dir)

    saved_benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))

    assert saved_benchmark == original_manifest

    assert temporary_manifest_path.is_file()

    saved_temporary_manifest = json.loads(temporary_manifest_path.read_text(encoding="utf-8"))

    assert saved_temporary_manifest == new_tmp_manifest








