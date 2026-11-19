from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from finance_cli.exceptions.providers import (
    ProviderSymbolError,
)
from finance_cli.exceptions.scraped_data import (
    ScrapedDataContentError,
)
from finance_cli.main import main


@patch("finance_cli.main.build_services")
# @patch("finance_cli.main.logging_setup.configure_logging")
@patch("finance_cli.main.app_config.load_app_config")
def test_retrieve_market_data_success(
    mock_load_config,
    # mock_configure_logging,
    mock_build_services,
    tmp_config,
):
    # Arrange
    mock_load_config.return_value = tmp_config

    service = MagicMock()
    service.retrieve_market_data.return_value = MagicMock(
        status="created",
        file_path=Path("external-data/assets/equity/FR0000120271/scraped_data"),
        last_updated=None,
        message=None,
    )

    mock_build_services.return_value = MagicMock(
        asset_service=service,
    )

    # Act
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["asset", "--id", "FR0000120271", "retrieve", "market-data"],
    )

    # Assert
    assert result.exit_code == 0, result.output
    assert "Nouvelles données marché enregistrées" in result.output
    service.retrieve_market_data.assert_called_once_with("FR0000120271")
    mock_build_services.assert_called_once_with(tmp_config)


@patch("finance_cli.main.build_services")
@patch("finance_cli.main.logging_setup.configure_logging")
@patch("finance_cli.main.app_config.load_app_config")
def test_retrieve_market_data_rejected(
    mock_load_config,
    mock_configure_logging,
    mock_build_services,
    tmp_config,
):
    # Arrange
    mock_load_config.return_value = tmp_config

    service = MagicMock()
    service.retrieve_market_data.return_value = MagicMock(
        status="rejected",
        file_path=None,
        last_updated=None,
        message="Données invalides",
    )

    mock_build_services.return_value = MagicMock(
        asset_service=service,
    )

    # Act
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["asset", "--id", "FR0000120271", "retrieve", "market-data"],
    )

    # Assert
    assert result.exit_code == 0, result.output
    assert "Données marché rejetées : Données invalides" in result.output
    service.retrieve_market_data.assert_called_once_with("FR0000120271")
    mock_build_services.assert_called_once_with(tmp_config)


@patch("finance_cli.main.logging_setup.configure_logging")
@patch("finance_cli.main.app_config.load_app_config")
@patch("finance_cli.main.build_services")
def test_retrieve_market_data_provider_error(
    mock_build_services,
    mock_configure_logging,
    mock_load_config,
    tmp_config,
):
    mock_load_config.return_value = tmp_config

    service = MagicMock()
    service.retrieve_market_data.side_effect = ProviderSymbolError(
        "Symbole Yahoo Finance invalide."
    )
    mock_build_services.return_value = MagicMock(
        asset_service=service,
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["asset", "--id", "FR0000120271", "retrieve", "market-data"],
    )

    assert result.exit_code != 0
    assert "Symbole Yahoo Finance invalide." in result.output


@patch("finance_cli.main.logging_setup.configure_logging")
@patch("finance_cli.main.app_config.load_app_config")
@patch("finance_cli.main.build_services")
def test_update_market_data_success(
    mock_build_services,
    mock_load_config,
    mock_configure_logging,
    tmp_config,
):
    mock_load_config.return_value = tmp_config

    service = MagicMock()
    service.update_scraped_data.return_value = MagicMock()
    mock_build_services.return_value = MagicMock(
        asset_service=service,
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["asset", "--id", "FR0000120271", "update", "market-data"],
    )

    assert result.exit_code == 0
    assert "Catalogue mis à jour pour l'actif : FR0000120271" in result.output
    service.update_scraped_data.assert_called_once_with("FR0000120271")


@patch("finance_cli.main.logging_setup.configure_logging")
@patch("finance_cli.main.app_config.load_app_config")
@patch("finance_cli.main.build_services")
def test_update_market_data_scraped_data_error(
    mock_build_services,
    mock_load_config,
    mock_configure_logging,
    tmp_config,
):
    mock_load_config.return_value = tmp_config

    service = MagicMock()
    service.update_scraped_data.side_effect = ScrapedDataContentError(
        "Aucune donnée scraped trouvée."
    )
    mock_build_services.return_value = MagicMock(
        asset_service=service,
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["asset", "--id", "FR0000120271", "update", "market-data"],
    )

    assert result.exit_code != 0
    assert "Aucune donnée scraped trouvée." in result.output


@patch("finance_cli.main.logging_setup.configure_logging")
@patch("finance_cli.main.app_config.load_app_config")
@patch("finance_cli.main.build_services")
def test_interactive_prompt_handles_unexpected_error(
    mock_build_services,
    mock_load_config,
    mock_configure_logging,
    tmp_config,
):
    # Arrange
    mock_load_config.return_value = tmp_config

    service = MagicMock()
    service.retrieve_market_data.side_effect = RuntimeError("Unexpected failure")

    mock_build_services.return_value = MagicMock(
        asset_service=service,
    )

    # Act
    runner = CliRunner()
    result = runner.invoke(
        main,
        [],
        input="asset --id FR0000120271 retrieve market-data\nexit\n",
    )

    # Assert
    assert result.exit_code == 0, (
        f"Output: {result.output}\nException: {result.exception!r}"
    )
    assert "Erreur interne inattendue" in result.output
    service.retrieve_market_data.assert_called_once_with("FR0000120271")
