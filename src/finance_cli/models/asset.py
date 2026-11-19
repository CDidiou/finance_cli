"""Domain model for an asset validated and loaded from the catalogue."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# class AssetStatus(str, Enum):
#    ACTIVE = "active"
#    CLOSED = "closed"


class TradingPlace(BaseModel):
    stock_exchange: str
    currency: str
    ticker: str


class GeneralInfo(StrictModel):
    name: str
    category: str

    sector: int | None = None
    management_company: str | None = None
    benchmark: str | None = None
    ter: float | None = None
    distribution: str | None = None
    replication: str | None = None
    fund_currency: str | None = None

    trading_places: list[TradingPlace] | None = None
    status: str | None = None
    inception_date: date | None = None
    closed_date: date | None = None
    pea: bool | None = None


class Quote(BaseModel):
    quote_always_one: bool


class MarketDataIndicative(BaseModel):
    # Valeur de marché
    price: float | None = None
    nav: float | None = None

    # Devise et date
    currency: str | None = None
    as_of: date | None = None

    # Capitalisation / encours
    market_cap: float | None = None
    mc_unit: str | None = None

    aum: float | None = None
    aum_unit: str | None = None


class MarketData(StrictModel):
    last_updated: date | None = None
    indicative: MarketDataIndicative | None = None


class FactsheetSources(BaseModel):
    provider: str
    symbol: str


class AggregatorSources(BaseModel):
    provider: str
    symbol: str


class PricesSources(BaseModel):
    provider: str
    symbol: str


class Sources(StrictModel):
    factsheet: FactsheetSources | None = None
    aggregator: AggregatorSources | None = None
    prices: PricesSources | None = None


class AssetClass(StrictModel):
    cash: float = 0.0
    fixed_income: float = 0.0
    real_estate: float = 0.0
    commodities: float = 0.0
    equity: float = 0.0
    alternate: float = 0.0
    crypto: float = 0.0


class LowRisk(StrictModel):
    savings_account: float = 0.0
    euro_funds: float = 0.0
    monetary: float = 0.0


class MidRisk(StrictModel):
    commodities: float = 0.0
    gold: float = 0.0
    real_estate: float = 0.0
    fixed_income: float = 0.0
    aristocrats: float = 0.0


class HighRisk(StrictModel):
    world: float = 0.0
    usa: float = 0.0
    em: float = 0.0
    eu: float = 0.0
    france: float = 0.0
    others: float = 0.0


class Risk(StrictModel):
    low_risk: LowRisk
    mid_risk: MidRisk
    high_risk: HighRisk


class PyFinance(StrictModel):
    asset_class: AssetClass
    risk: Risk


class Asset(BaseModel):
    """Represent an asset loaded from its validated catalogue definition.

    YAML loading, inheritance resolution and schema validation
    belong to the catalogue adapter.
    """

    id: str
    general_info: GeneralInfo
    quote: Quote
    market_data: MarketData
    sources: Sources | None = None
    py_finance: PyFinance

    @property
    def name(self) -> str:
        return self.general_info.name

    @property
    def category(self) -> str:
        return self.general_info.category

    @property
    def is_closed(self) -> bool:
        return self.general_info.status == "closed"

    def sections(self, *names: str) -> dict[str, Any]:
        if not names:
            names = (
                "general_info",
                "market_data",
                "sources",
                "quote",
                "py_finance",
            )
        data = self.model_dump()
        return {name: data[name] for name in names if name in data}

    @property
    def quote_always_one(self) -> bool:
        return self.quote.quote_always_one

    def prices_provider(self) -> str:
        if self.sources and self.sources.prices:
            return self.sources.prices.provider
        return "none"

    def __repr__(self) -> str:
        return f"Asset(id={self.id!r})"
