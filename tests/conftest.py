from datetime import date
from pathlib import Path

import pytest

from finance_cli.config.config_models import AppConfig
from finance_cli.config.paths_resolver import ConfigPathResolver
from finance_cli.models.asset import Asset
from finance_cli.models.scraped_asset import AggregatedScrapedAsset
from finance_cli.repositories.asset_repository import AssetRepository
from finance_cli.validation.reference_validator import ReferenceValidator
from finance_cli.validation.schema_loader import SchemaLoader
from finance_cli.validation.schema_validator import SchemaValidator


@pytest.fixture
def tmp_config(tmp_path):
    """Configuration minimale utilisant un répertoire temporaire."""

    return AppConfig.model_validate(
        {
            "app": {
                "name": "patrimonia",
                "version": "1.0.0",
                "base_dir": str(tmp_path),
            },
            "logging": {"enabled": "false"},
            "data": {
                "common": {
                    "schemas": "resources/schemas/common",
                },
                "catalog": {
                    "financial": {
                        "assets": {
                            "format": "yaml",
                            "filename": "<ID_ASSET>.yaml",
                            "folder": "data/assets",
                            "schemas": "resources/schemas/assets",
                            "rules": "resources/rules/assets",
                        },
                        "contracts": {"format": "yaml", "folder": "data/contracts"},
                    },
                    "references": {
                        "economy": {
                            "format": "yaml",
                            "folder": "data/economy",
                            "schemas": "resources/schemas/economy",
                            "rules": "resources/rules/economy",
                        },
                    },
                },
                "external": {
                    "assets": {
                        "scraped_data": {
                            "format": "yaml",
                            "filename": "<ID_ASSET>_scraping.yaml",
                            "folder": (
                                "external-data/assets/"
                                "<CATEGORY_PATH>/<ID_ASSET>/scraped_data"
                            ),
                            "schemas": "resources/schemas/assets/scraped",
                            "rules": "resources/rules/assets/scraped",
                        },
                        "quotes": {
                            "format": "yaml",
                            "folder": "external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/quotes",
                        },
                        "factsheets": {
                            "source": {
                                "format": "pdf",
                                "folder": "external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/factsheets",
                            },
                            "extracted": {
                                "format": "yaml",
                                "folder": "external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/factsheets",
                            },
                        },
                    },
                },
                "customer": {
                    "input": {
                        "users": {
                            "format": "yaml",
                            "folder": "external-data/users",
                        },
                        "wallets": {
                            "balances": {
                                "format": "excel",
                                "folder": "external-data/users/<ID_USER>/input/<ID_WALLET>/balances",
                            },
                            "transactions": {
                                "format": "excel",
                                "folder": "external-data/users/<ID_USER>/input/<ID_WALLET>/transactions",
                            },
                        },
                    },
                    "calculated": {
                        "users": {
                            "balances": {
                                "format": "yaml",
                                "folder": "external-data/users/<ID_USER>/calculated/global",
                            },
                            "evolution": {
                                "format": "yaml",
                                "folder": "external-data/users/<ID_USER>/calculated/global",
                            },
                            "dashboards": {
                                "format": "html",
                                "folder": "external-data/users/<ID_USER>/calculated/global",
                            },
                        },
                        "wallets": {
                            "transactions_enriched": {
                                "format": "yaml",
                                "folder": "external-data/users/<ID_USER>/calculated/<ID_WALLET>/transactions",
                            },
                            "balances": {
                                "format": "yaml",
                                "folder": "external-data/users/<ID_USER>/calculated/<ID_WALLET>/balances",
                            },
                            "evolution": {
                                "format": "yaml",
                                "folder": "external-data/users/<ID_USER>/calculated/<ID_WALLET>",
                            },
                            "dashboards": {
                                "format": "html",
                                "folder": "external-data/users/<ID_USER>/calculated/<ID_WALLET>",
                            },
                        },
                    },
                },
            },
            "api_keys": {},
            "source_path": ".",
        }
    )


@pytest.fixture
def true_config(tmp_config):
    project_root = Path(__file__).resolve().parents[1]

    return tmp_config.model_copy(
        update={"app": tmp_config.app.model_copy(update={"base_dir": project_root})}
    )


@pytest.fixture
def asset():
    """Actif représentatif du catalogue."""

    return Asset.model_validate(
        {
            "id": "IE000BI8OT95",
            "general_info": {
                "name": "ETF de référence",
                "category": "european_etf",
                "management_company": "amundi_etf",
                "benchmark": "MXWO",
                "ter": 0.12,
                "distribution": "acc",
                "replication": "physical",
                "pea": False,
                "fund_currency": "USD",
                "trading_places": [
                    {"stock_exchange": "PAR", "ticker": "MWRD", "currency": "EUR"}
                ],
                "status": "active",
            },
            "quote": {
                "quote_always_one": False,
            },
            "market_data": {
                "last_updated": None,
                "indicative": None,
            },
            "sources": {
                "factsheet": {
                    "provider": "amundi_etf",
                    "symbol": "amundi-core-msci-world-ucits-etf-acc",
                },
                "aggregator": {"provider": "yahoo_finance", "symbol": "MWRD.PA"},
                "prices": {"provider": "yahoo_finance", "symbol": "MWRD.PA"},
            },
            "py_finance": {
                "asset_class": {
                    "equity": 100,
                },
                "risk": {
                    "low_risk": {},
                    "mid_risk": {},
                    "high_risk": {
                        "world": 100,
                    },
                },
            },
        }
    )


@pytest.fixture
def scraped_asset():
    """Données collectées représentatives."""

    return AggregatedScrapedAsset.model_validate(
        {
            "source": {
                "asset_id": "IE000BI8OT95",
                "provider": "yahoo_finance",
                "url": "https://finance.yahoo.com/",
                "retrieved_at": date(2026, 11, 15),
            },
            "agg_info": {
                "name": "ETF de référence",
                "management_company": "Example Asset Management",
                "fund_currency": "EUR",
            },
            "market_data": {
                "last_updated": date(2026, 11, 14),
                "indicative": {
                    "price": 125.50,
                    "currency": "EUR",
                    "aum": 1_500_000_000,
                },
            },
        }
    )


@pytest.fixture
def economy_reference_files(tmp_path):
    """Prépare les références économiques minimales."""

    economy_dir = tmp_path / "data/economy"
    economy_dir.mkdir(parents=True)

    currency_file = economy_dir / "currency.yaml"
    currency_file.write_text(
        """
currencies:
  - code: USD
    name: Dollar américain
    symbol: "$"
    country: États-Unis
    ticker_vs_usd: "USD/USD"
    is_base_currency: true

  - code: EUR
    name: Euro
    symbol: "€"
    country: Zone Euro
    ticker_vs_usd: "EUR/USD"
""",
        encoding="utf-8",
    )

    return economy_dir


@pytest.fixture
def catalog_schema_validator(true_config):
    path_resolver = ConfigPathResolver(true_config)

    economy_resources = path_resolver.resolve_resources("catalog/references/economy")

    reference_validator = ReferenceValidator(
        references_dir=economy_resources.folder,
    )

    asset_resources = path_resolver.resolve_resources("catalog/financial/assets")

    common_schemas_dir = (
        true_config.app.base_dir / true_config.data.common.schemas
    ).resolve()

    schema_loader = SchemaLoader(
        schemas_dir=asset_resources.schemas,
        common_schemas_dir=common_schemas_dir,
    )

    return SchemaValidator(
        schema_loader=schema_loader,
        reference_validator=reference_validator,
    )


@pytest.fixture
def asset_repository(
    tmp_path,
    true_config,
    catalog_schema_validator,
):
    assets_config = true_config.data.catalog.financial.assets

    assets_dir = tmp_path / assets_config.folder
    assets_dir.mkdir(parents=True, exist_ok=True)

    return AssetRepository(
        folder=assets_dir,
        rules_dir=(true_config.app.base_dir / assets_config.rules).resolve(),
        schema_validator=catalog_schema_validator,
        model=Asset,
    )
