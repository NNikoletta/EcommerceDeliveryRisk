import json
from unittest.mock import Mock

import ecommercedeliveryrisk.download_data as download_module


def test_download_raw_data_directory_is_empty_no_benchmark(tmp_path, monkeypatch) -> None:
    # Creating testing directories for the raw data and for the manifests
    test_raw_dir = tmp_path / "raw"
    test_manifest_dir = tmp_path / "manifest"

    test_raw_dir.mkdir()
    test_manifest_dir.mkdir()

    # Creating a mock api that will replace the Kaggle api -> WILL NOT ACESS the internet
    mock_api = Mock()

    # Setting what the mock api's response is to the dataset_status call
    mock_api.dataset_status.return_value = json.dumps({"current_version_number": 1})

    # Creating a mock file that matches the return value of the api.dataset_list_files call
    mock_file_listing = Mock()
    mock_file_listing.to_dict.return_value = {"datasetFiles": []}

    mock_api.dataset_list_files.return_value = mock_file_listing

    # Replacing the real KaggleApi call with the mock api
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "KaggleApi", lambda: mock_api)

    # Replacing the directory for the manifests with the temporary test directory
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "manifests_data_dir", test_manifest_dir)

    #  Create_manifest call returning a mock dictionary and mock save_manifest call
    mock_manifest = {'dataset_metadata': {'dataset_version': 1}}
    mock_create_manifest = Mock(return_value=mock_manifest)
    mock_save_manifest = Mock()

    monkeypatch.setattr(download_module, "create_manifest", mock_create_manifest)
    monkeypatch.setattr(download_module, "save_manifest", mock_save_manifest)

    #  Calling the download with the temporary test directory for the raw data
    download_module.download_raw_data(input_raw_data_dir=test_raw_dir)

    expected_dataset = f"{download_module.KAGGLE_DATASET}/1"

    #  Asserts that all the expected function calls are made once and with the expected parameters
    mock_api.authenticate.assert_called_once_with()

    mock_api.dataset_status.assert_called_once_with(dataset=download_module.KAGGLE_DATASET, format="json(current_version_number)")

    mock_api.dataset_download_files.assert_called_once_with(dataset=expected_dataset, path=test_raw_dir, unzip=True)

    mock_api.dataset_list_files.assert_called_once_with(expected_dataset)

    mock_create_manifest.assert_called_once()

    mock_save_manifest.assert_called_once()


def test_download_raw_data_directory_is_empty_benchmark_exists(tmp_path, monkeypatch) -> None:
    # Creating testing directories for the raw data and for the manifests
    test_raw_dir = tmp_path / "raw"
    test_manifest_dir = tmp_path / "manifest"

    test_raw_dir.mkdir()
    test_manifest_dir.mkdir()

    mock_benchmark_path = test_manifest_dir / "benchmark_raw_data_manifest.json"
    with mock_benchmark_path.open("w") as json_file:
        json.dump({'dataset_metadata': {'dataset_version': 1}}, json_file, indent=2)

    # Creating a mock api that will replace the Kaggle api -> WILL NOT ACESS the internet
    mock_api = Mock()

    # Creating a mock file that matches the return value of the api.dataset_list_files call
    mock_file_listing = Mock()
    mock_file_listing.to_dict.return_value = {"datasetFiles": []}

    mock_api.dataset_list_files.return_value = mock_file_listing

    # Replacing the real KaggleApi call with the mock api
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "KaggleApi", lambda: mock_api)

    # Replacing the directory for the manifests with the temporary test directory
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "manifests_data_dir", test_manifest_dir)

    #  Create_manifest call returning a mock dictionary and mock save_manifest call
    mock_manifest = {'dataset_metadata': {'dataset_version': 1}}
    mock_create_manifest = Mock(return_value=mock_manifest)
    mock_save_manifest = Mock()

    monkeypatch.setattr(download_module, "create_manifest", mock_create_manifest)
    monkeypatch.setattr(download_module, "save_manifest", mock_save_manifest)

    #  Calling the download with the temporary test directory for the raw data
    download_module.download_raw_data(input_raw_data_dir=test_raw_dir)

    expected_dataset = f"{download_module.KAGGLE_DATASET}/1"

    #  Asserts that all the expected function calls are made once and with the expected parameters
    mock_api.authenticate.assert_called_once_with()

    mock_api.dataset_status.assert_not_called()

    mock_api.dataset_download_files.assert_called_once_with(dataset=expected_dataset, path=test_raw_dir, unzip=True)

    mock_api.dataset_list_files.assert_called_once_with(expected_dataset)

    mock_create_manifest.assert_called_once()

    mock_save_manifest.assert_called_once()


def test_download_raw_data_directory_is_not_empty_replacement_disabled(tmp_path, monkeypatch) -> None:
    # Creating testing directories for the raw data and for the manifests
    test_raw_dir = tmp_path / "raw"
    test_manifest_dir = tmp_path / "manifest"

    test_raw_dir.mkdir()
    test_manifest_dir.mkdir()

    mock_file_path = test_raw_dir / "mock_file.csv"
    mock_file_path.write_text("mock_text")

    # Creating a mock api that will replace the Kaggle api -> WILL NOT ACESS the internet
    mock_api = Mock()

    # Replacing the real KaggleApi call with the mock api
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "KaggleApi", lambda: mock_api)

    #  Create_manifest call returning a mock dictionary and mock save_manifest call
    mock_create_manifest = Mock(return_value={})
    mock_save_manifest = Mock()

    monkeypatch.setattr(download_module, "create_manifest", mock_create_manifest)
    monkeypatch.setattr(download_module, "save_manifest", mock_save_manifest)

    #  Calling the download with the temporary test directory for the raw data
    download_module.download_raw_data(input_raw_data_dir=test_raw_dir, replace_existing=False)

    #  Asserts that all the expected function calls are made once and with the expected parameters
    mock_api.authenticate.assert_called_once_with()

    mock_api.dataset_status.assert_not_called()

    mock_api.dataset_download_files.assert_not_called()

    mock_api.dataset_list_files.assert_not_called()

    mock_create_manifest.assert_not_called()

    mock_save_manifest.assert_not_called()


def test_download_raw_data_directory_is_not_empty_replacement_enabled_no_benchmark(tmp_path, monkeypatch) -> None:
    # Creating testing directories for the raw data and for the manifests
    test_raw_dir = tmp_path / "raw"
    test_manifest_dir = tmp_path / "manifest"

    test_raw_dir.mkdir()
    test_manifest_dir.mkdir()

    mock_file_path = test_raw_dir / "mock_file.csv"
    mock_file_path.write_text("mock_text")

    # Creating a mock api that will replace the Kaggle api -> WILL NOT ACESS the internet
    mock_api = Mock()

    # Setting what the mock api's response is to the dataset_status call
    mock_api.dataset_status.return_value = json.dumps({"current_version_number": 1})

    # Creating a mock file that matches the return value of the api.dataset_list_files call
    mock_file_listing = Mock()
    mock_file_listing.to_dict.return_value = {"datasetFiles": []}

    mock_api.dataset_list_files.return_value = mock_file_listing

    # Replacing the real KaggleApi call with the mock api
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "KaggleApi", lambda: mock_api)

    # Replacing the directory for the manifests with the temporary test directory
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "manifests_data_dir", test_manifest_dir)

    #  Create_manifest call returning a mock dictionary and mock save_manifest call
    mock_manifest = {'dataset_metadata': {'dataset_version': 1}}
    mock_create_manifest = Mock(return_value=mock_manifest)
    mock_save_manifest = Mock()

    monkeypatch.setattr(download_module, "create_manifest", mock_create_manifest)
    monkeypatch.setattr(download_module, "save_manifest", mock_save_manifest)

    #  Calling the download with the temporary test directory for the raw data
    download_module.download_raw_data(input_raw_data_dir=test_raw_dir, replace_existing=True)

    expected_dataset = f"{download_module.KAGGLE_DATASET}/1"

    #  Asserts that all the expected function calls are made once and with the expected parameters
    mock_api.authenticate.assert_called_once_with()

    mock_api.dataset_status.assert_called_once_with(dataset=download_module.KAGGLE_DATASET, format="json(current_version_number)")

    mock_api.dataset_download_files.assert_called_once_with(dataset=expected_dataset, path=test_raw_dir, unzip=True)

    mock_api.dataset_list_files.assert_called_once_with(expected_dataset)

    mock_create_manifest.assert_called_once()

    mock_save_manifest.assert_called_once()


def test_download_raw_data_directory_is_not_empty_replacement_enabled_benchmark_exists(tmp_path, monkeypatch) -> None:
    # Creating testing directories for the raw data and for the manifests
    test_raw_dir = tmp_path / "raw"
    test_tmp_dir = test_raw_dir / "_tmp"
    test_manifest_dir = tmp_path / "manifest"

    test_raw_dir.mkdir()
    test_tmp_dir.mkdir()
    test_manifest_dir.mkdir()

    mock_file_path = test_raw_dir / "mock_file.csv"
    mock_file_path.write_text("mock_text")

    mock_benchmark_path = test_manifest_dir / "benchmark_raw_data_manifest.json"
    with mock_benchmark_path.open("w") as json_file:
        json.dump({'dataset_metadata': {'dataset_version': 1}}, json_file, indent=2)


    # Creating a mock api that will replace the Kaggle api -> WILL NOT ACESS the internet
    mock_api = Mock()

    # Creating a mock file that matches the return value of the api.dataset_list_files call
    mock_file_listing = Mock()
    mock_file_listing.to_dict.return_value = {"datasetFiles": []}

    mock_api.dataset_list_files.return_value = mock_file_listing

    # Simulate Kaggle writing a downloaded file into _tmp
    def fake_dataset_download_files(dataset, path, unzip) -> None:
        downloaded_file = path / "downloaded_file.csv"
        downloaded_file.write_text("new downloaded data")

    mock_api.dataset_download_files.side_effect = fake_dataset_download_files

    mock_validate_raw_data = Mock()

    mock_manifest = {"dataset_metadata": {"dataset_version": 1}}

    mock_create_manifest = Mock(return_value=mock_manifest)
    mock_save_manifest = Mock()

    # noinspection unresolved-references
    monkeypatch.setattr(download_module,"KaggleApi",lambda: mock_api)

    # noinspection unresolved-references
    monkeypatch.setattr(download_module,"manifests_data_dir", test_manifest_dir)

    # noinspection unresolved-references
    monkeypatch.setattr(download_module,"validate_raw_data", mock_validate_raw_data)

    monkeypatch.setattr(download_module,"create_manifest", mock_create_manifest)

    monkeypatch.setattr(download_module,"save_manifest", mock_save_manifest)

    test_tmp_dir = test_raw_dir / "_tmp"

    download_module.download_raw_data(input_raw_data_dir=test_raw_dir, replace_existing=True)

    expected_dataset = f"{download_module.KAGGLE_DATASET}/1"

    mock_api.authenticate.assert_called_once_with()

    mock_api.dataset_status.assert_not_called()

    mock_api.dataset_download_files.assert_called_once_with(dataset=expected_dataset, path=test_tmp_dir, unzip=True)

    mock_api.dataset_list_files.assert_called_once_with(expected_dataset)

    mock_validate_raw_data.assert_called_once_with(test_tmp_dir)

    mock_create_manifest.assert_called_once()

    mock_save_manifest.assert_called_once_with(manifest_name="benchmark_raw_data_manifest.json", manifest=mock_manifest)

    assert not mock_file_path.exists()

    downloaded_file = test_raw_dir / "downloaded_file.csv"

    assert downloaded_file.is_file()
    assert (downloaded_file.read_text(encoding="utf-8") == "new downloaded data")

    assert not test_tmp_dir.exists()