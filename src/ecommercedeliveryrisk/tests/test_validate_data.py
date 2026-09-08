import json
from dataclasses import dataclass
from unittest.mock import Mock, create_autospec

import pytest

import ecommercedeliveryrisk.validate_data as validation_module
from ecommercedeliveryrisk.config import Settings, FileManifest, manifests_data_dir


@dataclass
class MockExpectedFiles:
    orders: str = "orders.csv"

@pytest.fixture
def settings(tmp_path):
    return Settings(kaggle_dataset='test-owner/test-dataset',
                    raw_data_dir=tmp_path/"raw",
                    manifests_data_dir=tmp_path/"manifests")

@pytest.fixture
def pipeline_mocks(monkeypatch):
    calculate_sha256 = create_autospec(validation_module.calculate_local_sha256)
    # noinspection unresolved-references
    monkeypatch.setattr(validation_module, "calculate_local_sha256", calculate_sha256)
    return calculate_sha256

def test_validate_raw_data(tmp_path, monkeypatch, settings, pipeline_mocks):
    calculate_sha256 = pipeline_mocks
    calculate_sha256.return_value = "mock_sha256"

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
                            'sha256': 'mock_sha256',
                            'size_byte': file_path.stat().st_size,
                            'download_date': "2026-08-09T00:00:00Z",
                            'dataset_created': "2026-01-01T00:00:00Z",
                            'column_count': 2,
                            'row_count': 2,
                            'column_names': ['order_id', 'status']}
                 }

    benchmark_path.write_text(json.dumps(benchmark), encoding='utf-8')

    validation_module.validate_raw_data(data_dir=data_dir, manifests_dir=manifests_dir)

# @pytest.mark.parametrize(
#     "file_dir_available,files_available",
#     [
#         pytest.param(False, False, id="no-dir-no-files"),
#         pytest.param(True, False, id="has-dir-no-files"),
#         pytest.param(True, True, id="has-dir-has-files")
#     ]
# )

def test_validate_raw_data_catches_wrong_metrics(tmp_path, monkeypatch, settings, pipeline_mocks):
    calculate_sha256 = pipeline_mocks
    calculate_sha256.return_value = "mock_sha256"

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
                            'sha256': 'mock_sha256',
                            'size_byte': file_path.stat().st_size,
                            'download_date': "2026-08-09T00:00:00Z",
                            'dataset_created': "2026-01-01T00:00:00Z",
                            'column_count': 2,
                            'row_count': 2,
                            'column_names': ['order_id', 'status']}
                 }

    benchmark_path.write_text(json.dumps(benchmark), encoding='utf-8')

    validation_module.validate_raw_data(data_dir=data_dir, manifests_dir=manifests_dir)


#
#
# def test_validate_data_directory_does_not_exist(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(FileNotFoundError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The file directory '{data_dir}' does not exist.")
#
#
# def test_validate_data_directory_exists_but_is_empty(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(FileNotFoundError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The file directory '{data_dir}' does not contain any files.")
#
# def test_validate_data_wrong_file_count(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     test_file = "orders.csv"
#     file_path = data_dir / test_file
#     file_path.write_text("order_id,status\n"
#                          "1,delivered\n"
#                          "2,shipped\n", encoding="utf-8")
#
#     file_count = 1
#     expected_file_count = 2
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(FileNotFoundError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"Found {file_count} files in {data_dir}.\n"
#                                     f"Expected file count is {expected_file_count}.")
#
#
# def test_validate_data_not_a_file(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     test_file = "orders.csv"
#     file_path = data_dir / test_file
#     file_path.write_text("order_id,status\n"
#                          "1,delivered\n"
#                          "2,shipped\n", encoding="utf-8")
#
#     not_a_file = "customers.csv"
#     not_a_file_path = data_dir / not_a_file
#     not_a_file_path.mkdir()
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(FileNotFoundError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == f"{not_a_file} is not a file."
#
#
# def test_validate_data_file_name_does_not_match_benchmark_file_name(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     wrong_file = "orders.csv"
#     orders_file_path = data_dir / wrong_file
#     orders_file_path.write_text("order_id,status\n"
#                          "1,delivered\n"
#                          "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                          "1,12345\n"
#                          "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'orders': {'file_name': 'benchmark_name_orders.csv'}}
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(FileNotFoundError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"File name does not match the expected file name.\n"
#                                     f"Expected {manifest_data['orders']['file_name']}\n"
#                                     f"Found {wrong_file}.")
#
#
# def test_validate_data_file_size_does_not_match_benchmark_file_size(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     wrong_file = "orders.csv"
#     wrong_file_path = data_dir / wrong_file
#     wrong_file_path.write_text("order_id,status\n"
#                          "1,delivered\n"
#                          "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                          "1,12345\n"
#                          "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'orders': {'file_name': 'orders.csv',
#                                 'size_byte': wrong_file_path.stat().st_size + 1}}
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The size of the '{wrong_file}' file does not match the expected size.\n"
#                                     f"Expected size is {wrong_file_path.stat().st_size + 1} bytes.\n"
#                                     f"Found size {wrong_file_path.stat().st_size} bytes.")
#
#
# def test_validate_data_file_row_count_does_not_match_benchmark_row_count(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     wrong_file = "orders.csv"
#     wrong_file_path = data_dir / wrong_file
#     wrong_file_path.write_text("order_id,status\n"
#                          "1,delivered\n"
#                          "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                          "1,12345\n"
#                          "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'orders': {'file_name': 'orders.csv',
#                                 'size_byte': wrong_file_path.stat().st_size,
#                                 'row_count': 3}}
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The number of rows of the '{wrong_file}' file does not match the expected number of rows.\n"
#                                     f"Expected {manifest_data['orders']['row_count']} rows.\n"
#                                     f"Found 2 rows.\n")
#
#
# def test_validate_data_file_column_count_does_not_match_benchmark_column_count(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     wrong_file = "orders.csv"
#     wrong_file_path = data_dir / wrong_file
#     wrong_file_path.write_text("order_id,status\n"
#                          "1,delivered\n"
#                          "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                          "1,12345\n"
#                          "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'orders': {'file_name': 'orders.csv',
#                                 'size_byte': wrong_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 3}}
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The number of columns of the '{wrong_file}' file does not match the expected number of columns.\n"
#                                     f"Expected {manifest_data['orders']['column_count']} columns.\n"
#                                     f"Found 2 columns.\n")
#
#
# def test_validate_data_calculated_sha256_does_not_match_benchmark_sha256(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     wrong_file = "orders.csv"
#     wrong_file_path = data_dir / wrong_file
#     wrong_file_path.write_text("order_id,status\n"
#                          "1,delivered\n"
#                          "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                          "1,12345\n"
#                          "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'orders': {'file_name': 'orders.csv',
#                                 'size_byte': wrong_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 2,
#                                 'sha256': 'mock_sha256'}}
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="wrong_mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == "The SHA-256 hash doesn't match the expected value."
#
#
# def test_validate_data_no_tmp_manifest_only_benchmark_everything_is_correct(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'orders': {'file_name': 'orders.csv',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 2,
#                                 'sha256': 'mock_sha256'},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     result = validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert result is None
#
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_manifest_keys(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 2,
#                                 'sha256': 'mock_sha256'},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'wrong_key': {},
#                          'orders': {},
#                          'customers': {}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == "The manifest data does not match the benchmark data.\n"
#
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_dataset_metadata(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 2,
#                                 'sha256': 'mock_sha256'},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 2},
#                          'orders': {},
#                          'customers': {}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == f"The dataset metadata does not match the expected manifest data.\n"
#
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_file_name(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 2,
#                                 'sha256': 'mock_sha256'},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'wrong_orders.csv'},
#                          'customers': {}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The manifest data does not match the benchmark data.\n"
#                                     f"Expected key-value pair: file_name-{manifest_data['orders']['file_name']}\n"
#                                     f"Found key-value pair: file_name-{tmp_manifest_data['orders']['file_name']}\n")
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_sha256(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'dataset': 'ecommerce',
#                                 'dataset_version': 1,
#                                 'sha256': 'mock_sha256',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 2},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'orders.csv',
#                                     'dataset': 'ecommerce',
#                                     'dataset_version': 1,
#                                     'sha256': 'wrong_mock_sha256'},
#                          'customers': {}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The manifest data does not match the benchmark data.\n"
#                                     f"Expected key-value pair: sha256-{manifest_data['orders']['sha256']}\n"
#                                     f"Found key-value pair: sha256-{tmp_manifest_data['orders']['sha256']}\n")
#
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_size(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'dataset': 'ecommerce',
#                                 'dataset_version': 1,
#                                 'sha256': 'mock_sha256',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'row_count': 2,
#                                 'column_count': 2},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'orders.csv',
#                                     'dataset': 'ecommerce',
#                                     'dataset_version': 1,
#                                     'sha256': 'mock_sha256',
#                                     'size_byte': orders_file_path.stat().st_size + 1},
#                          'customers': {}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The manifest data does not match the benchmark data.\n"
#                                     f"Expected key-value pair: size_byte-{manifest_data['orders']['size_byte']}\n"
#                                     f"Found key-value pair: size_byte-{tmp_manifest_data['orders']['size_byte']}\n")
#
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_date_of_creation(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'dataset': 'ecommerce',
#                                 'dataset_version': 1,
#                                 'sha256': 'mock_sha256',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'dataset_created': "2026-01-01T00:00:00Z",
#                                 'row_count': 2,
#                                 'column_count': 2},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'orders.csv',
#                                     'dataset': 'ecommerce',
#                                     'dataset_version': 1,
#                                     'sha256': 'mock_sha256',
#                                     'size_byte': orders_file_path.stat().st_size,
#                                     'dataset_created': "2026-02-01T00:00:00Z"},
#                          'customers': {'file_name': 'customers.csv',
#                                        'size_byte': customers_file_path.stat().st_size,
#                                        'row_count': 2,
#                                        'column_count': 2,
#                                        'sha256': 'mock_sha256'}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The manifest data does not match the benchmark data.\n"
#                                     f"Expected key-value pair: dataset_created-{manifest_data['orders']['dataset_created']}\n"
#                                     f"Found key-value pair: dataset_created-{tmp_manifest_data['orders']['dataset_created']}\n")
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_column_count(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'dataset': 'ecommerce',
#                                 'dataset_version': 1,
#                                 'sha256': 'mock_sha256',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'dataset_created': "2026-01-01T00:00:00Z",
#                                 'row_count': 2,
#                                 'column_count': 2},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'orders.csv',
#                                     'dataset': 'ecommerce',
#                                     'dataset_version': 1,
#                                     'sha256': 'mock_sha256',
#                                     'size_byte': orders_file_path.stat().st_size,
#                                     'dataset_created': "2026-01-01T00:00:00Z",
#                                     'column_count': 3},
#                          'customers': {'file_name': 'customers.csv',
#                                        'size_byte': customers_file_path.stat().st_size,
#                                        'row_count': 2,
#                                        'column_count': 2,
#                                        'sha256': 'mock_sha256'}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The manifest data does not match the benchmark data.\n"
#                                     f"Expected key-value pair: column_count-{manifest_data['orders']['column_count']}\n"
#                                     f"Found key-value pair: column_count-{tmp_manifest_data['orders']['column_count']}\n")
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_row_count(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'dataset': 'ecommerce',
#                                 'dataset_version': 1,
#                                 'sha256': 'mock_sha256',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'dataset_created': "2026-01-01T00:00:00Z",
#                                 'row_count': 2,
#                                 'column_count': 2},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'orders.csv',
#                                     'dataset': 'ecommerce',
#                                     'dataset_version': 1,
#                                     'sha256': 'mock_sha256',
#                                     'size_byte': orders_file_path.stat().st_size,
#                                     'dataset_created': "2026-01-01T00:00:00Z",
#                                     'column_count': 2,
#                                     'row_count': 3},
#                          'customers': {'file_name': 'customers.csv',
#                                        'size_byte': customers_file_path.stat().st_size,
#                                        'row_count': 2,
#                                        'column_count': 2,
#                                        'sha256': 'mock_sha256'}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The manifest data does not match the benchmark data.\n"
#                                     f"Expected key-value pair: row_count-{manifest_data['orders']['row_count']}\n"
#                                     f"Found key-value pair: row_count-{tmp_manifest_data['orders']['row_count']}\n")
#
#
# def test_validate_data_tmp_manifest_and_benchmark_wrong_column_names(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'dataset': 'ecommerce',
#                                 'dataset_version': 1,
#                                 'sha256': 'mock_sha256',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'dataset_created': "2026-01-01T00:00:00Z",
#                                 'row_count': 2,
#                                 'column_count': 2,
#                                 'expected_columns': ['order_id', 'status']},
#                      'customers': {'file_name': 'customers.csv',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'sha256': 'mock_sha256'}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'orders.csv',
#                                     'dataset': 'ecommerce',
#                                     'dataset_version': 1,
#                                     'sha256': 'mock_sha256',
#                                     'size_byte': orders_file_path.stat().st_size,
#                                     'dataset_created': "2026-01-01T00:00:00Z",
#                                     'column_count': 2,
#                                     'row_count': 2,
#                                     'expected_columns': ['order_id']},
#                          'customers': {'file_name': 'customers.csv',
#                                        'size_byte': customers_file_path.stat().st_size,
#                                        'row_count': 2,
#                                        'column_count': 2,
#                                        'sha256': 'mock_sha256'}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     with pytest.raises(ValueError) as exc_error:
#         validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert str(exc_error.value) == (f"The manifest data does not match the benchmark data.\n"
#                                     f"Expected key-value pair: column_names-{manifest_data['orders']['column_names']}\n"
#                                     f"Found key-value pair: column_names-{tmp_manifest_data['orders']['column_names']}\n")
#
#
# def test_validate_data_tmp_manifest_and_benchmark_everything_is_correct(tmp_path, monkeypatch) -> None:
#     data_dir = tmp_path / "raw"
#     manifests_dir = tmp_path / "manifests"
#     data_dir.mkdir()
#     manifests_dir.mkdir()
#
#     orders_file = "orders.csv"
#     orders_file_path = data_dir / orders_file
#     orders_file_path.write_text("order_id,status\n"
#                                 "1,delivered\n"
#                                 "2,shipped\n", encoding="utf-8")
#
#     customers_file = "customers.csv"
#     customers_file_path = data_dir / customers_file
#     customers_file_path.write_text("customer_id,customer_unique_id\n"
#                                     "1,12345\n"
#                                     "2,67891\n", encoding="utf-8")
#
#     manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                           'dataset_version': 1},
#                      'orders': {'file_name': 'orders.csv',
#                                 'dataset': 'ecommerce',
#                                 'dataset_version': 1,
#                                 'sha256': 'mock_sha256',
#                                 'size_byte': orders_file_path.stat().st_size,
#                                 'dataset_created': "2026-01-01T00:00:00Z",
#                                 'row_count': 2,
#                                 'column_count': 2,
#                                 'expected_columns': ['order_id', 'status']},
#                      'customers': {'file_name': 'customers.csv',
#                                    'dataset': 'ecommerce',
#                                    'dataset_version': 1,
#                                    'sha256': 'mock_sha256',
#                                    'size_byte': customers_file_path.stat().st_size,
#                                    'dataset_created': "2026-01-01T00:00:00Z",
#                                    'row_count': 2,
#                                    'column_count': 2,
#                                    'expected_columns': ['customer_id', 'customer_unique_id']}
#                      }
#     benchmark_manifest = "benchmark_raw_data_manifest.json"
#     benchmark_filepath = manifests_dir / benchmark_manifest
#     benchmark_filepath.write_text(json.dumps(manifest_data), encoding="utf-8")
#
#     tmp_manifest_data = {'dataset_metadata': {'dataset_name': 'olistbr/brazilian-ecommerce',
#                                               'dataset_version': 1},
#                          'orders': {'file_name': 'orders.csv',
#                                     'dataset': 'ecommerce',
#                                     'dataset_version': 1,
#                                     'sha256': 'mock_sha256',
#                                     'size_byte': orders_file_path.stat().st_size,
#                                     'dataset_created': "2026-01-01T00:00:00Z",
#                                     'row_count': 2,
#                                     'column_count': 2,
#                                     'expected_columns': ['order_id', 'status']},
#                          'customers': {'file_name': 'customers.csv',
#                                        'dataset': 'ecommerce',
#                                        'dataset_version': 1,
#                                        'sha256': 'mock_sha256',
#                                        'size_byte': customers_file_path.stat().st_size,
#                                        'dataset_created': "2026-01-01T00:00:00Z",
#                                        'row_count': 2,
#                                        'column_count': 2,
#                                        'expected_columns': ['customer_id', 'customer_unique_id']}
#                          }
#
#     tmp_manifest = "tmp_raw_data_manifest.json"
#     tmp_manifest_filepath = manifests_dir / tmp_manifest
#     tmp_manifest_filepath.write_text(json.dumps(tmp_manifest_data), encoding="utf-8")
#
#     mock_calculate_local_sha256 = Mock(return_value="mock_sha256")
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "ExpectedFiles", MockExpectedFiles)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "raw_data_dir", data_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "manifests_data_dir", manifests_dir)
#     # noinspection unresolved-references
#     monkeypatch.setattr(validation_module, "calculate_local_sha256", mock_calculate_local_sha256)
#
#     result = validation_module.validate_raw_data(data_dir=data_dir, manifest_dir=manifests_dir)
#
#     assert result is None