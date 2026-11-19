from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from finance_cli.common import scraped_to_catalog
from finance_cli.exceptions.assets import (
    AssetNotFoundError,
    AssetStorageError,
)
from finance_cli.exceptions.providers import (
    ProviderConnectionError,
    ProviderDataError,
    ProviderSymbolError,
)
from finance_cli.exceptions.scraped_data import ScrapedDataContentError
from finance_cli.models.asset import Asset
from finance_cli.repositories.scraped_data_repository import (
    ScrapedDataStorageError,
    ScrapedDataWriteResult,
)
from finance_cli.services.assets.asset_service import AssetService
from finance_cli.validation.catalog_validation_error import InCatalogValidationError

"""
Tests unitaires du service AssetService.

Vérifie l'orchestration des opérations liées aux actifs :
- la transformation et la sauvegarde des données issues du scraping ;
- la récupération des données de marché via l'adaptateur Yahoo Finance ;
- la création, la mise à jour ou la conservation des données scrapées
  selon le résultat de leur enregistrement.
"""


def test_update_scraped_data_updates_catalog(asset, scraped_asset):
    """Les données scraped sont transformées puis sauvegardées au catalogue."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )

    updated_data = asset.model_dump(mode="json")
    updated_data["general_info"]["name"] = "Updated asset"

    updated_asset = Asset.model_validate(updated_data)

    asset_repository.get_by_id.side_effect = [
        asset,
        updated_asset,
    ]
    asset_repository.get_category_path.return_value = Path("european_etf")

    scraped_data_repository.read_scraped_data.return_value = scraped_asset.model_dump(
        mode="json"
    )

    with patch(
        "finance_cli.services.assets.asset_service.scraped_to_catalog.apply_external_to_catalog",
        return_value=updated_data,
    ) as mock_apply:
        result = service.update_scraped_data(asset.id)

    mock_apply.assert_called_once()

    scraped_data_repository.read_scraped_data.assert_called_once_with(
        asset_id=asset.id,
        category_path=Path("european_etf"),
    )

    asset_repository.save.assert_called_once_with(updated_asset)

    assert result == updated_asset


def test_retrieve_market_data_creates_scraped_data(asset, scraped_asset):
    """Les nouvelles données marché sont enregistrées."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )
    asset_repository.get_by_id.return_value = asset

    category_path = Path("european_etf")
    asset_repository.get_category_path.return_value = category_path

    raw_data = {"symbol": "TEST"}
    payload = scraped_asset.model_dump(mode="json")
    file_path = Path("scraped_data/IE000BI8OT95_scraping.yaml")
    # last_updated = date.fromisoformat(scraped_asset.market_data.last_updated)
    last_updated = scraped_asset.market_data.last_updated

    yahoo_adapter.fetch.return_value = (scraped_asset, raw_data)
    yahoo_adapter.to_dict.return_value = payload

    scraped_data_repository.write_scraped_data.return_value = ScrapedDataWriteResult(
        status="created",
        file_path=file_path,
        last_updated=last_updated,
    )

    result = service.retrieve_market_data(asset.id)

    yahoo_adapter.fetch.assert_called_once()
    yahoo_adapter.to_dict.assert_called_once_with(
        scraped_asset,
        raw=raw_data,
    )

    scraped_data_repository.write_scraped_data.assert_called_once_with(
        asset_id=asset.id,
        category_path=category_path,
        payload=payload,
    )

    assert result.status == "created"
    assert result.asset_id == asset.id
    assert result.file_path == file_path
    assert result.last_updated == last_updated


def test_retrieve_market_data_updates_scraped_data(asset, scraped_asset):
    """Les nouvelles données marché sont enregistrées."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )
    asset_repository.get_by_id.return_value = asset

    category_path = Path("european_etf")
    asset_repository.get_category_path.return_value = category_path

    raw_data = {"symbol": "TEST"}
    payload = scraped_asset.model_dump(mode="json")
    file_path = Path("scraped_data/IE000BI8OT95_scraping.yaml")
    # last_updated = date.fromisoformat(scraped_asset.market_data.last_updated)
    last_updated = scraped_asset.market_data.last_updated

    yahoo_adapter.fetch.return_value = (scraped_asset, raw_data)
    yahoo_adapter.to_dict.return_value = payload

    scraped_data_repository.write_scraped_data.return_value = ScrapedDataWriteResult(
        status="updated",
        file_path=file_path,
        last_updated=last_updated,
        message="Données mises à jour.",
    )

    result = service.retrieve_market_data(asset.id)

    assert result.status == "updated"
    assert result.asset_id == asset.id
    assert result.file_path == file_path
    assert result.last_updated == last_updated
    assert result.message == "Données mises à jour."


def test_retrieve_market_data_keeps_scraped_data(asset, scraped_asset):
    """Les nouvelles données marché sont enregistrées."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )
    asset_repository.get_by_id.return_value = asset

    category_path = Path("european_etf")
    asset_repository.get_category_path.return_value = category_path

    raw_data = {"symbol": "TEST"}
    payload = scraped_asset.model_dump(mode="json")
    file_path = Path("scraped_data/IE000BI8OT95_scraping.yaml")
    # last_updated = date.fromisoformat(scraped_asset.market_data.last_updated)
    last_updated = scraped_asset.market_data.last_updated

    yahoo_adapter.fetch.return_value = (scraped_asset, raw_data)
    yahoo_adapter.to_dict.return_value = payload

    scraped_data_repository.write_scraped_data.return_value = ScrapedDataWriteResult(
        status="unchanged",
        file_path=file_path,
        last_updated=last_updated,
        message="Les données existantes sont conservées.",
    )

    result = service.retrieve_market_data(asset.id)

    assert result.status == "unchanged"
    assert result.asset_id == asset.id
    assert result.file_path == file_path
    assert result.last_updated == last_updated
    assert result.message == "Les données existantes sont conservées."


def test_retrieve_market_data_rejects_invalid_scraped_data(asset, scraped_asset):
    """Les données invalides sont rejetées sans interrompre le service."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )

    asset_repository.get_by_id.return_value = asset
    asset_repository.get_category_path.return_value = Path("european_etf")

    raw_data = {"symbol": "TEST"}
    yahoo_adapter.fetch.return_value = (scraped_asset, raw_data)
    yahoo_adapter.to_dict.return_value = scraped_asset.model_dump(mode="json")

    scraped_data_repository.write_scraped_data.side_effect = ScrapedDataContentError(
        "Invalid scraped data"
    )

    result = service.retrieve_market_data(asset.id)

    assert result.status == "rejected"
    assert result.asset_id == asset.id
    assert result.file_path is None
    assert result.last_updated is None
    assert result.message == "Invalid scraped data"

    scraped_data_repository.write_scraped_data.assert_called_once()


def test_retrieve_market_data_propagates_storage_error(asset, scraped_asset):
    """Une erreur de stockage n'est pas transformée en résultat rejected."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )

    asset_repository.get_by_id.return_value = asset
    asset_repository.get_category_path.return_value = Path("european_etf")

    raw_data = {"symbol": "TEST"}
    yahoo_adapter.fetch.return_value = (scraped_asset, raw_data)
    yahoo_adapter.to_dict.return_value = scraped_asset.model_dump(mode="json")

    scraped_data_repository.write_scraped_data.side_effect = ScrapedDataStorageError(
        "Storage unavailable"
    )

    with pytest.raises(ScrapedDataStorageError, match="Storage unavailable"):
        service.retrieve_market_data(asset.id)

    scraped_data_repository.write_scraped_data.assert_called_once()


def test_retrieve_market_data_raises_when_aggregator_missing(asset):
    service = AssetService.__new__(AssetService)
    service._asset_repository = MagicMock()
    service.aggregator = None

    with pytest.raises(ValueError):
        service.retrieve_market_data(asset.id)


def test_retrieve_market_data_raises_when_provider_unsupported(asset):
    """Un fournisseur non supporté provoque une erreur."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )

    asset_data = asset.model_dump(mode="json")
    asset_data["sources"]["aggregator"]["provider"] = "unsupported_provider"

    unsupported_asset = Asset.model_validate(asset_data)
    asset_repository.get_by_id.return_value = unsupported_asset

    with pytest.raises(ValueError):
        service.retrieve_market_data(asset.id)

    yahoo_adapter.fetch.assert_not_called()


def test_retrieve_market_data_raises_when_aggregator_missing2(asset):
    """L'absence de source aggregator empêche la récupération des données."""

    asset_repository = MagicMock()
    # scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=None,
        yahoo_adapter=yahoo_adapter,
    )

    asset_data = asset.model_dump(mode="json")
    asset_data["sources"]["aggregator"] = None

    asset_without_aggregator = Asset.model_validate(asset_data)
    asset_repository.get_by_id.return_value = asset_without_aggregator

    with pytest.raises(ValueError):
        service.retrieve_market_data(asset.id)

    yahoo_adapter.fetch.assert_not_called()


def test_retrieve_market_data_without_aggregator_raises(asset):
    """Une erreur est levée si aucun agrégateur n'est défini."""

    service = AssetService.__new__(AssetService)
    service._asset_repository = MagicMock()
    service._asset_repository.get_by_id.return_value = asset.model_copy(
        update={"sources": None}
    )

    with pytest.raises(ValueError, match="Aucun agrégateur défini"):
        service.retrieve_market_data(asset.id)


def test_retrieve_market_data_with_unsupported_provider_raises(asset):
    """Un provider non supporté provoque une erreur."""

    service = AssetService.__new__(AssetService)

    unsupported_asset = asset.model_copy(
        update={
            "sources": asset.sources.model_copy(
                update={
                    "aggregator": asset.sources.aggregator.model_copy(
                        update={"provider": "unsupported"}
                    )
                }
            )
        }
    )

    service._asset_repository = MagicMock()
    service._asset_repository.get_by_id.return_value = unsupported_asset

    with pytest.raises(ValueError, match="non supporté"):
        service.retrieve_market_data(asset.id)


def test_retrieve_market_data_without_symbol_raises(asset):
    """Une erreur est levée si aucun symbole n'est défini."""

    service = AssetService.__new__(AssetService)

    invalid_asset = asset.model_copy(
        update={
            "sources": asset.sources.model_copy(
                update={
                    "aggregator": asset.sources.aggregator.model_copy(
                        update={"symbol": None}
                    )
                }
            )
        }
    )

    service._asset_repository = MagicMock()
    service._asset_repository.get_by_id.return_value = invalid_asset

    with pytest.raises(ValueError, match="Aucun symbole"):
        service.retrieve_market_data(asset.id)


def test_apply_external_with_empty_indicative_keeps_catalog_unchanged():
    """Une indicative vide ne modifie ni les données ni last_updated."""

    catalog = {
        "id": "IE000BI8OT95",
        "market_data": {
            "last_updated": "2026-01-01",
            "indicative": {
                "price": 100.0,
                "currency": "EUR",
            },
        },
    }

    external = {
        "market_data": {
            "last_updated": "2026-11-15",
            "indicative": {},
        }
    }

    result = scraped_to_catalog.apply_external_to_catalog(external, catalog)

    assert result == catalog
    assert result["market_data"]["last_updated"] == "2026-01-01"


def test_apply_external_with_indicative_updates_last_updated():
    """Une indicative renseignée permet de mettre à jour last_updated."""

    catalog = {
        "id": "IE000BI8OT95",
        "market_data": {
            "last_updated": "2026-01-01",
            "indicative": {
                "price": 100.0,
                "currency": "EUR",
            },
        },
    }

    external = {
        "market_data": {
            "last_updated": "2026-11-15",
            "indicative": {
                "price": 125.0,
            },
        }
    }

    result = scraped_to_catalog.apply_external_to_catalog(external, catalog)

    assert result["market_data"]["last_updated"] == "2026-11-15"
    assert result["market_data"]["indicative"]["price"] == 125.0
    assert result["market_data"]["indicative"]["currency"] == "EUR"

    # Le catalogue d'origine n'est pas modifié.
    assert catalog["market_data"]["last_updated"] == "2026-01-01"
    assert catalog["market_data"]["indicative"]["price"] == 100.0


def test_update_scraped_data_raises_when_asset_not_found():
    """Une erreur est propagée si l'actif n'existe pas."""

    service = AssetService.__new__(AssetService)
    service._asset_repository = MagicMock()

    service._asset_repository.get_by_id.side_effect = AssetNotFoundError(
        "Asset not found"
    )

    with pytest.raises(AssetNotFoundError, match="Asset not found"):
        service.update_scraped_data("UNKNOWN")

    service._asset_repository.get_category_path.assert_not_called()


def test_update_scraped_data_raises_when_scraped_data_is_missing(asset):
    """L'absence de données scraped interrompt l'application au catalogue."""

    service = AssetService.__new__(AssetService)
    service._asset_repository = MagicMock()
    service._scraped_data_repository = MagicMock()

    service._asset_repository.get_by_id.return_value = asset
    service._asset_repository.get_category_path.return_value = Path("european_etf")
    service._scraped_data_repository.read_scraped_data.side_effect = (
        ScrapedDataContentError("No scraped data found")
    )

    with pytest.raises(ScrapedDataContentError, match="No scraped data found"):
        service.update_scraped_data(asset.id)

    service._asset_repository.save.assert_not_called()


def test_update_scraped_data_raises_when_scraped_data_is_invalid(asset):
    """Un payload incompatible avec le modèle scraped est rejeté."""

    service = AssetService.__new__(AssetService)
    service._asset_repository = MagicMock()
    service._scraped_data_repository = MagicMock()

    service._asset_repository.get_by_id.return_value = asset
    service._asset_repository.get_category_path.return_value = Path("european_etf")

    # Payload volontairement incompatible avec AggregatedScrapedAsset
    service._scraped_data_repository.read_scraped_data.return_value = {
        "invalid": "payload"
    }

    with pytest.raises(ScrapedDataContentError):
        service.update_scraped_data(asset.id)

    service._asset_repository.save.assert_not_called()


def test_update_scraped_data_raises_when_updated_asset_is_invalid(
    asset,
    scraped_asset,
):
    """Un Asset invalide après intégration est rejeté."""

    service = AssetService.__new__(AssetService)
    service._asset_repository = MagicMock()
    service._scraped_data_repository = MagicMock()

    service._asset_repository.get_by_id.return_value = asset
    service._asset_repository.get_category_path.return_value = Path("european_etf")
    service._scraped_data_repository.read_scraped_data.return_value = (
        scraped_asset.model_dump(mode="json")
    )

    invalid_data = asset.model_dump(mode="json")
    invalid_data["general_info"]["name"] = None

    with patch(
        "finance_cli.services.assets.asset_service.scraped_to_catalog.apply_external_to_catalog",
        return_value=invalid_data,
    ):
        with pytest.raises(InCatalogValidationError):
            service.update_scraped_data(asset.id)

    service._asset_repository.save.assert_not_called()


def test_update_scraped_data_propagates_storage_error(
    asset,
    scraped_asset,
):
    """Une erreur de stockage du catalogue remonte sans être masquée."""

    service = AssetService.__new__(AssetService)
    service._asset_repository = MagicMock()
    service._scraped_data_repository = MagicMock()

    service._asset_repository.get_by_id.return_value = asset
    service._asset_repository.get_category_path.return_value = Path("european_etf")
    service._scraped_data_repository.read_scraped_data.return_value = (
        scraped_asset.model_dump(mode="json")
    )

    updated_data = asset.model_dump(mode="json")
    updated_asset = Asset.model_validate(updated_data)

    service._asset_repository.save.side_effect = AssetStorageError(
        "Impossible de sauvegarder l'actif."
    )

    with patch(
        "finance_cli.services.assets.asset_service.scraped_to_catalog.apply_external_to_catalog",
        return_value=updated_data,
    ):
        with pytest.raises(AssetStorageError, match="Impossible de sauvegarder"):
            service.update_scraped_data(asset.id)

    service._asset_repository.save.assert_called_once_with(updated_asset)


def test_retrieve_market_data_propagates_provider_connection_error(asset):
    """Une erreur de connexion fournisseur remonte sans être masquée."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )

    asset_repository.get_by_id.return_value = asset
    yahoo_adapter.fetch.side_effect = ProviderConnectionError(
        "Yahoo Finance inaccessible"
    )

    with pytest.raises(
        ProviderConnectionError,
        match="Yahoo Finance inaccessible",
    ):
        service.retrieve_market_data(asset.id)

    scraped_data_repository.write_scraped_data.assert_not_called()


def test_retrieve_market_data_propagates_provider_symbol_error(asset):
    """Une erreur de symbole fournisseur remonte sans être masquée."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )

    asset_repository.get_by_id.return_value = asset
    yahoo_adapter.fetch.side_effect = ProviderSymbolError(
        "Symbole Yahoo Finance introuvable."
    )

    with pytest.raises(
        ProviderSymbolError,
        match="Symbole Yahoo Finance introuvable",
    ):
        service.retrieve_market_data(asset.id)

    scraped_data_repository.write_scraped_data.assert_not_called()


def test_retrieve_market_data_propagates_provider_data_error(asset):
    """Une erreur de données fournisseur remonte sans être masquée."""

    asset_repository = MagicMock()
    scraped_data_repository = MagicMock()
    yahoo_adapter = MagicMock()
    service = AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )

    asset_repository.get_by_id.return_value = asset
    yahoo_adapter.fetch.side_effect = ProviderDataError(
        "Données Yahoo Finance indisponibles."
    )

    with pytest.raises(
        ProviderDataError,
        match="Données Yahoo Finance indisponibles",
    ):
        service.retrieve_market_data(asset.id)

    scraped_data_repository.write_scraped_data.assert_not_called()
