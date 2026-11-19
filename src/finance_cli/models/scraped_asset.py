from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class SourceInfo(BaseModel):
    asset_id: str
    provider: str
    url: str
    retrieved_at: date

    model_config = ConfigDict(extra="allow")


class AggInfo(BaseModel):
    name: str
    management_company: str | None = None
    ter: float | None = None
    fund_currency: str | None = None
    distribution: str | None = None
    replication: str | None = None
    benchmark: str | None = None

    model_config = ConfigDict(extra="allow")


class MarketDataIndicative(BaseModel):
    price: float | None = None
    nav: float | None = None
    currency: str | None = None
    aum: float | None = None
    market_cap: float | None = None
    as_of: date | None = None

    model_config = ConfigDict(extra="allow")


class MarketData(BaseModel):
    last_updated: date
    indicative: MarketDataIndicative

    model_config = ConfigDict(extra="allow")


class AggregatedScrapedAsset(BaseModel):
    # Le modèle représente les données réellement collectées, et non les champs calculés lors de apply
    source: SourceInfo
    agg_info: AggInfo
    market_data: MarketData

    model_config = ConfigDict(extra="allow")
