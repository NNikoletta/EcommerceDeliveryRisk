import pytest

from unittest.mock import Mock

import ecommercedeliveryrisk.cli as cli
from ecommercedeliveryrisk.config import Settings

@pytest.mark.parametrize(
    "arguments,expected_replace,can_download",
    [
        pytest.param([],False, True, id="default"),
        pytest.param(["--replace-existing"],True, True, id="replace-existing"),
        pytest.param(["--validate-only"],False, False, id="validate-only")
    ]
)
def test_cli_modes(tmp_path, monkeypatch,
                   arguments, expected_replace,
                   can_download):
    settings = Settings(kaggle_dataset="owner/dataset",
                        raw_data_dir=tmp_path / "raw",
                        manifests_data_dir=tmp_path / "manifests")

    mock_download = Mock()
    mock_validate = Mock()
    mock_compare = Mock()

    monkeypatch.setattr(cli,"load_settings", Mock(return_value=settings))
    monkeypatch.setattr(cli, "load_dotenv", Mock())
    monkeypatch.setattr(cli, "download_raw_data", mock_download)
    monkeypatch.setattr(cli, "validate_data", mock_validate)
    monkeypatch.setattr(cli, "compare_manifests", mock_compare)

    cli.main(arguments)

    if can_download:
        mock_download.assert_called_once_with(settings=settings,
                                              replace_existing=expected_replace)
    else:
        mock_download.assert_not_called()

    mock_validate.assert_called_once_with(data_dir=settings.raw_data_dir,
                                          manifests_dir=settings.manifests_data_dir)

    mock_compare.assert_called_once_with(manifests_dir=settings.manifests_data_dir)


def test_cli_rejects_conflicting_modes():
    parser = cli.build_parser()

    with pytest.raises(SystemExit) as error:
        parser.parse_args(
            ["--replace-existing", "--validate-only"]
        )

    assert error.value.code == 2