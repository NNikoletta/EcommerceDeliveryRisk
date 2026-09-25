from unittest.mock import Mock

import pytest

import ecommercedeliveryrisk.cli as cli
from ecommercedeliveryrisk.config import Settings


@pytest.mark.parametrize(
    "arguments,expected_replace,download,validate,ingest",
    [
        pytest.param([], False, True, True, True, id="default"),
        pytest.param(["--download"], False, True, False, False,id="download"),
        pytest.param(["--replace-existing"], True, True, False, False, id="replace-existing"),
        pytest.param(["--validate"], False, False, True, False, id="validate"),
        pytest.param(["--ingest"], False, False, False, True, id="ingest"),
    ],
)
def test_cli_modes(tmp_path, monkeypatch, arguments, expected_replace, download, validate, ingest):
    settings = Settings(
        kaggle_dataset="owner/dataset",
        raw_data_dir=tmp_path / "raw",
        manifests_data_dir=tmp_path / "manifests",
    )

    mock_download = Mock()
    mock_validate = Mock()
    mock_compare = Mock()
    mock_ingest = Mock()

    monkeypatch.setattr(cli, "load_settings", Mock(return_value=settings))
    monkeypatch.setattr(cli, "load_dotenv", Mock())
    monkeypatch.setattr(cli, "download_raw_data", mock_download)
    monkeypatch.setattr(cli, "validate_data", mock_validate)
    monkeypatch.setattr(cli, "compare_manifests", mock_compare)
    monkeypatch.setattr(cli, "run_ingestion", mock_ingest)

    cli.main(arguments)

    if download:
        mock_download.assert_called_once_with(settings=settings, replace_existing=expected_replace)
    else:
        mock_download.assert_not_called()

    if validate:
        mock_validate.assert_called_once_with(
            data_dir=settings.raw_data_dir, manifests_dir=settings.manifests_data_dir
        )
        mock_compare.assert_called_once_with(manifests_dir=settings.manifests_data_dir)
    else:
        mock_validate.assert_not_called()

    if ingest:
        mock_ingest.assert_called_once_with(settings=settings)
    else:
        mock_ingest.assert_not_called()


def test_cli_rejects_conflicting_modes():
    parser = cli.build_parser()

    with pytest.raises(SystemExit) as error:
        parser.parse_args(["--replace-existing", "--validate-only"])

    assert error.value.code == 2
