from __future__ import annotations

from typing import Any, Protocol

from finance_cli.models.scraped_asset import AggregatedScrapedAsset


class MarketDataProvider(Protocol):
    """Interface commune des fournisseurs de données de marché."""

    def fetch(
        self,
        asset_id: str,
        symbol: str,
    ) -> tuple[AggregatedScrapedAsset, dict[str, Any]]:
        """Récupère et structure les données de marché."""
        ...

    def to_dict(
        self,
        scraped: AggregatedScrapedAsset,
        raw: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Sérialise les données récupérées."""
        ...
