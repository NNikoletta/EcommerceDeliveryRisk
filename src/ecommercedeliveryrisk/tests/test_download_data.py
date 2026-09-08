import json
from unittest.mock import create_autospec

import pytest

import ecommercedeliveryrisk.download_data as download_module
from ecommercedeliveryrisk.config import DownloadResult, Settings

@pytest.fixture
def settings(tmp_path):
    return Settings(kaggle_dataset='test-owner/test-dataset',
                    raw_data_dir=tmp_path/"raw",
                    manifests_data_dir=tmp_path/"manifests")

@pytest.fixture
def pipeline_mocks(monkeypatch):
    download = create_autospec(download_module.download_kaggle_dataset)
    create = create_autospec(download_module.create_manifest)
    validate = create_autospec(download_module.validate_raw_data)
    monkeypatch.setattr(download_module, "download_kaggle_dataset", download)
    monkeypatch.setattr(download_module, "create_manifest", create)
    # noinspection unresolved-references
    monkeypatch.setattr(download_module, "validate_raw_data", validate)
    return download, create, validate

@pytest.mark.parametrize(
    "contains_old_data,benchmark_available,replace_existing",
    [
        pytest.param(False, False, False, id="empty-no-benchmark"),
        pytest.param(False, True, False, id="empty-with-benchmark"),
        pytest.param(True, False, True, id="replace-no-benchmark"),
        pytest.param(True, True, True, id="replace-with-benchmark"),
        pytest.param(True, True, False, id="retain-existing")
    ]
)

def test_download_raw_data(settings, pipeline_mocks,
                           contains_old_data, benchmark_available,
                           replace_existing):
    download, create, validate = pipeline_mocks
    old_file = settings.raw_data_dir / "old.csv"
    if contains_old_data:
        settings.raw_data_dir.mkdir()
        old_file.write_text('original data', encoding='utf-8')

    benchmark_path = settings.manifests_data_dir / "benchmark_raw_data_manifest.json"
    benchmark = {'dataset_metadata': {'dataset_version': 1}}
    if benchmark_available:
        settings.manifests_data_dir.mkdir()
        benchmark_path.write_text(json.dumps(benchmark), encoding='utf-8')

    version = 1 if benchmark_available else 2
    result =  DownloadResult("2026-09-08T12:00:00Z", [], version)

    manifest = {'dataset_metadata': {'dataset_version': version}, 'test': 'new'}
    create.return_value = manifest
    destinations = []

    def mock_download(settings: Settings, data_dir=None, dataset_version=None):
        destination = settings.raw_data_dir if data_dir is None else data_dir
        destinations.append(destination)
        assert destination.is_dir()
        if contains_old_data and benchmark_available:
            assert old_file.read_text(encoding='utf-8') == "original data"
            assert destination != settings.raw_data_dir
        (destination / "new.csv").write_text("downloaded data", encoding='utf-8')
        return result

    def mock_validate(data_dir=None, manifests_dir=None):
        assert old_file.read_text(encoding='utf-8') == "original data"
        assert (data_dir / "new.csv").is_file()
        assert manifests_dir == settings.manifests_data_dir

    download.side_effect = mock_download
    validate.side_effect = mock_validate

    download_module.download_raw_data(settings=settings, replace_existing=replace_existing)

    if contains_old_data and not replace_existing:
        download.assert_not_called()
        create.assert_not_called()
        validate.assert_not_called()
        assert old_file.read_text(encoding='utf-8') == "original data"
        assert json.loads(benchmark_path.read_text(encoding='utf-8')) == benchmark
        assert not (settings.manifests_data_dir / "tmp_raw_data_manifest.json").exists()
        return

    download.assert_called_once()
    if contains_old_data and benchmark_available:
        staging_dir = destinations[0]
        download.assert_called_once_with(settings=settings,
                                         data_dir=staging_dir,
                                         dataset_version=1)
        validate.assert_called_once_with(staging_dir, manifests_dir=settings.manifests_data_dir)
        assert staging_dir.parent == settings.raw_data_dir.parent
        assert not staging_dir.exists()
    else:
        validate.assert_not_called()
        expected_kwargs = {'settings': settings}
        if benchmark_available:
            expected_kwargs['dataset_version'] = 1
        download.assert_called_once_with(**expected_kwargs)
    assert not old_file.exists()
    assert (settings.raw_data_dir / "new.csv").read_text(encoding='utf-8') == "downloaded data"

    create.assert_called_once_with(dataset_metadata=result.dataset_metadata,
                                   dataset_version=result.dataset_version,
                                   download_date=result.download_date,
                                   settings=settings)

    saved_path = benchmark_path
    if benchmark_available:
        assert json.loads(benchmark_path.read_text(encoding='utf-8')) == benchmark
        saved_path = settings.manifests_data_dir / "tmp_raw_data_manifest.json"
    assert json.loads(saved_path.read_text(encoding='utf-8')) == manifest


@pytest.mark.parametrize("failure_stage", ["download", "validation"])
def test_replacement_failure_preserves_original_and_cleans_staging(settings, pipeline_mocks, failure_stage):
    download, create, validate = pipeline_mocks
    settings.raw_data_dir.mkdir()
    settings.manifests_data_dir.mkdir()

    old_file = settings.raw_data_dir / "old.csv"
    old_file.write_text("original data", encoding='utf-8')

    benchmark_path = settings.manifests_data_dir / "benchmark_raw_data_manifest.json"
    original_manifest = json.dumps({'dataset_metadata': {'dataset_version': 1}})
    benchmark_path.write_text(original_manifest, encoding='utf-8')

    destinations = []

    def mock_download(settings, data_dir=None, dataset_version=None):
        destinations.append(data_dir)
        (data_dir / "partial.csv").write_text("partial data", encoding='utf-8')
        if failure_stage == "download":
            raise RuntimeError("simulated failure")
        return DownloadResult("2026-09-08T12:00:00Z", [], 1)

    download.side_effect = mock_download
    validate.side_effect = RuntimeError("simulated failure")

    with pytest.raises(RuntimeError, match="simulated failure"):
        download_module.download_raw_data(settings=settings, replace_existing=True)

    assert old_file.read_text(encoding='utf-8') == "original data"
    assert len(destinations) == 1
    assert not destinations[0].exists()
    assert benchmark_path.read_text(encoding='utf-8') == original_manifest
    assert not (settings.manifests_data_dir / "tmp_raw_data_manifest.json").exists()

    create.assert_not_called()
    if failure_stage == "download":
        validate.assert_not_called()
    else:
        validate.assert_called_once()