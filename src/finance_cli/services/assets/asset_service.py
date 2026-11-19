from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from finance_cli.adapters.web.yahoo_finance import YahooFinanceAdapter
from finance_cli.common import scraped_to_catalog
from finance_cli.exceptions.scraped_data import ScrapedDataContentError
from finance_cli.models.asset import Asset
from finance_cli.models.scraped_asset import AggregatedScrapedAsset
from finance_cli.repositories.asset_repository import AssetRepository
from finance_cli.repositories.scraped_data_repository import ScrapedDataRepository
from finance_cli.validation import catalog_validation_error

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResult:
    asset_id: str
    status: Literal["created", "updated", "unchanged", "rejected"]
    file_path: Path | None = None
    last_updated: date | None = None
    message: str | None = None


class AssetService:
    """Cas d'utilisation autour des actifs."""

    def __init__(
        self,
        asset_repository: AssetRepository,
        scraped_data_repository: ScrapedDataRepository,
        yahoo_adapter: YahooFinanceAdapter,
    ) -> None:
        self._asset_repository = asset_repository
        self._scraped_data_repository = scraped_data_repository
        self._yahoo_adapter = yahoo_adapter

    # --- API PUBLIQUE ---

    def get_by_id(self, asset_id: str) -> Asset:
        return self._asset_repository.get_by_id(asset_id)

    def show(
        self,
        asset_id: str,
        sections: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        asset = self.get_by_id(asset_id)

        if not sections:
            sections = ("general_info", "market_data")

        return asset.model_dump(include=set(sections))

    def retrieve_market_data(self, asset_id: str) -> FetchResult:
        """Collecte les données marché sans modifier le catalogue."""

        asset = self.get_by_id(asset_id)

        aggregator = asset.sources.aggregator if asset.sources is not None else None

        if aggregator is None:
            raise ValueError(f"Aucun agrégateur défini pour l'actif {asset_id!r}.")

        if aggregator.provider != "yahoo_finance":
            raise ValueError(
                f"Provider {aggregator.provider!r} non supporté pour fetch market-data."
            )

        if not aggregator.symbol:
            raise ValueError(f"Aucun symbole de prix défini pour l'actif {asset_id!r}.")

        logger.info(
            "Collecte des données marché : asset=%s, provider=%s, symbol=%s",
            asset.id,
            aggregator.provider,
            aggregator.symbol,
        )

        scraped, raw = self._yahoo_adapter.fetch(
            asset_id=asset.id,
            symbol=aggregator.symbol,
        )

        payload = self._yahoo_adapter.to_dict(scraped, raw=raw)

        category_path = self._asset_repository.get_category_path(asset.id)

        try:
            write_result = self._scraped_data_repository.write_scraped_data(
                asset_id=asset.id,
                category_path=category_path,
                payload=payload,
            )
        except ScrapedDataContentError as exc:
            return FetchResult(
                asset_id=asset.id,
                status="rejected",
                message=str(exc),
            )

        return FetchResult(
            asset_id=asset.id,
            status=write_result.status,
            file_path=write_result.file_path,
            last_updated=write_result.last_updated,
            message=write_result.message,
        )

    def update_scraped_data(self, asset_id: str) -> Asset:
        """Intègre les données scraped courantes dans le catalogue."""

        asset = self.get_by_id(asset_id)

        category_path = self._asset_repository.get_category_path(asset.id)

        payload = self._scraped_data_repository.read_scraped_data(
            asset_id=asset.id,
            category_path=category_path,
        )

        try:
            external = AggregatedScrapedAsset.model_validate(payload)
        except ValidationError as exc:
            raise ScrapedDataContentError(
                f"Les données scraped de l'actif {asset_id!r} "
                "sont incompatibles avec le modèle attendu."
            ) from exc

        catalog_data = asset.model_dump(mode="json")

        updated_data = scraped_to_catalog.apply_external_to_catalog(
            external,
            catalog_data,
        )

        try:
            updated_asset = Asset.model_validate(updated_data)
        except ValidationError as exc:
            raise catalog_validation_error.InCatalogValidationError(
                id_catalog=asset_id,
                issues=exc.errors(),
                message=(
                    f"Les données intégrées ne permettent pas de construire "
                    f"un Asset valide pour {asset_id!r}."
                ),
            ) from exc

        self._asset_repository.save(updated_asset)

        return self._asset_repository.get_by_id(asset_id)
