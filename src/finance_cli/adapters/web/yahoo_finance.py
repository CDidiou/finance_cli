# finance_cli/adapters/market_data/yahoo_finance.py
from __future__ import annotations

from datetime import date
from typing import Any
import requests

import yfinance as yf
import yfinance.exceptions as yf_exceptions

from finance_cli.models import scraped_asset
from finance_cli.exceptions.providers import (
    ProviderConnectionError,
    ProviderDataError,
    ProviderSymbolError,
)


class YahooFinanceAdapter:
    """Récupère des données de marché via yfinance et les structure
    conformément au schéma external.assets.scraped_data.
    """

    def fetch(
        self, asset_id: str, symbol: str
    ) -> tuple[scraped_asset.AggregatedScrapedAsset, dict]:

        try:
            ticker = yf.Ticker(symbol)
            info: dict[str, Any] = ticker.info or {}

        except (
            yf_exceptions.YFRateLimitError,
            requests.exceptions.RequestException,
        ) as exc:
            raise ProviderConnectionError(
                f"Impossible de récupérer les données Yahoo Finance pour {symbol!r}."
            ) from exc

        except (
            yf_exceptions.YFPricesMissingError,
            yf_exceptions.YFTzMissingError,
        ) as exc:
            raise ProviderDataError(
                f"Données Yahoo Finance indisponibles pour {symbol!r}."
            ) from exc

        except yf_exceptions.YFTickerMissingError as exc:
            raise ProviderSymbolError(
                f"Symbole Yahoo Finance introuvable : {symbol!r}."
            ) from exc

        except (
            yf_exceptions.YFInvalidPeriodError,
            yf_exceptions.YFNotImplementedError,
        ) as exc:
            raise ProviderDataError(
                f"Données Yahoo Finance indisponibles ou invalides pour {symbol!r}."
            ) from exc

        today = date.today()

        source = scraped_asset.SourceInfo(
            asset_id=asset_id,
            provider="yahoo_finance",
            url=f"https://finance.yahoo.com/quote/{symbol}",
            retrieved_at=today,
        )

        name = info.get("longName") or info.get("shortName") or symbol

        # Capitalisation ou encours selon le type d'instrument Yahoo
        quote_type = info.get("quoteType")

        agg_info = scraped_asset.AggInfo(
            name=name,
            management_company=(
                info.get("fundFamily") or info.get("company")
                if quote_type in {"ETF", "MUTUALFUND"}
                else None
            ),
            ter=(
                info.get("netExpenseRatio")
                if quote_type in {"ETF", "MUTUALFUND"}
                else None
            ),
            fund_currency=(
                info.get("currency") if quote_type in {"ETF", "MUTUALFUND"} else None
            ),
        )

        indicative_data = {}

        nav = info.get("previousClose") or info.get("regularMarketPreviousClose")
        if nav is not None:
            indicative_data["nav"] = nav

        if info.get("currency"):
            indicative_data["currency"] = info["currency"]

        if quote_type == "EQUITY":
            market_cap = info.get("marketCap")
            if market_cap is not None:
                indicative_data["market_cap"] = market_cap

        elif quote_type in {"ETF", "MUTUALFUND"}:
            aum = info.get("totalAssets")
            if aum is not None:
                indicative_data["aum"] = aum

        market_data = scraped_asset.MarketData(
            last_updated=today,
            indicative=scraped_asset.MarketDataIndicative(**indicative_data),
        )

        scraped = scraped_asset.AggregatedScrapedAsset(
            source=source,
            agg_info=agg_info,
            market_data=market_data,
        )

        return scraped, info

    def to_dict(
        self, scraped: scraped_asset.AggregatedScrapedAsset, raw: dict | None = None
    ) -> dict:
        """Sérialise pour écriture YAML, en ajoutant éventuellement le raw."""
        data = scraped.model_dump(mode="json")  # dates → str ISO
        if raw is not None:
            data["raw"] = raw
        return data
