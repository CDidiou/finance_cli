"""Chargement et construction de la configuration applicative."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from finance_cli.common.yaml_io import load_yaml_mapping
from finance_cli.config.config_models import (
    ApiKeys,
    AppConfig,
    AppSettings,
    CalculatedUsersConfig,
    CalculatedWalletsConfig,
    CatalogConfig,
    CommonDataConfig,
    CustomerCalculatedConfig,
    CustomerConfig,
    CustomerInputConfig,
    DataSettings,
    EconomyReferencesConfig,
    ExternalAssetsConfig,
    ExternalDataConfig,
    FactsheetsConfig,
    FinancialConfig,
    LoggingSettings,
    ReferencesConfig,
    ResourceConfig,
    WalletInputConfig,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.cwd() / "config" / "config_app.yaml"


def load_app_config(
    path: str | Path = DEFAULT_CONFIG_PATH,
) -> AppConfig:
    """Charge, valide et construit la configuration applicative."""

    config_path = Path(path).resolve()
    raw_config = load_yaml_mapping(config_path)

    load_dotenv()

    validate_config(raw_config)

    return build_app_config(raw_config, config_path)


def validate_config(config: dict[str, Any]) -> None:
    """Vérifie la structure minimale de la configuration."""

    if not isinstance(config, dict):
        raise ValueError("La configuration doit être un dictionnaire YAML.")

    for section in ("app", "logging", "data"):
        if not isinstance(config.get(section), dict):
            raise ValueError(f"La section '{section}' est absente ou invalide.")

    app = config["app"]
    if app.get("name") != "patrimonia":
        raise ValueError("La valeur app.name doit être 'patrimonia'.")

    if not app.get("version"):
        raise ValueError("La clé app.version est obligatoire.")

    logging_config = config["logging"]

    if "enabled" not in logging_config:
        raise ValueError("La clé logging.enabled est obligatoire.")

    level = str(logging_config.get("level", "INFO")).upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"Niveau de logging invalide : {level}")

    fmt = logging_config.get("format", "standard")
    if fmt not in {"simple", "standard", "detailed"}:
        raise ValueError(f"Format de logging invalide : {fmt}")

    output = str(logging_config.get("output", "console")).lower()
    if output not in {"console", "file"}:
        raise ValueError(f"Destination de logging invalide : {output}")

    data = config["data"]
    for section in ("catalog", "external", "common"):
        if not isinstance(data.get(section), dict):
            raise ValueError(f"La section data.{section} est absente ou invalide.")

    try:
        data["catalog"]["references"]["economy"]["folder"]
        data["common"]["schemas"]
        data["external"]["assets"]["scraped_data"]["schemas"]
    except (KeyError, TypeError):
        raise ValueError(
            "La configuration data est incomplète : "
            "vérifiez catalog.references.economy.folder, "
            "common.schemas et external.assets.scraped_data.schemas."
        ) from None


def _build_resource(raw: dict[str, Any]) -> ResourceConfig:
    """Construit la configuration d'une ressource."""

    return ResourceConfig(
        format=raw["format"],
        folder=raw["folder"],
        filename=raw.get("filename"),
        schemas=raw.get("schemas"),
        rules=raw.get("rules"),
        templates=raw.get("templates"),
        styles=raw.get("styles"),
    )


def _build_economy_references(
    raw: dict[str, Any],
) -> EconomyReferencesConfig:
    """Construit la configuration des références économiques."""

    return EconomyReferencesConfig(
        format=raw["format"],
        folder=raw["folder"],
        schemas=raw["schemas"],
        rules=raw["rules"],
    )


def build_app_config(
    raw: dict[str, Any],
    config_path: Path,
) -> AppConfig:
    """Construit AppConfig à partir de la configuration YAML validée."""

    app_raw = raw["app"]
    logging_raw = raw["logging"]
    data_raw = raw["data"]

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    base_dir = Path(app_raw.get("base_dir", "."))
    if not base_dir.is_absolute():
        base_dir = (Path.cwd() / base_dir).resolve()
    else:
        base_dir = base_dir.resolve()

    app = AppSettings(
        name=app_raw["name"],
        version=str(app_raw["version"]),
        base_dir=base_dir,
    )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    file_path_raw = logging_raw.get("file_path")

    if file_path_raw is None:
        file_path = base_dir / "logs" / "app.log"
    else:
        file_path = Path(file_path_raw)
        if not file_path.is_absolute():
            file_path = base_dir / file_path
    file_path = file_path.resolve()

    logging_config = LoggingSettings(
        enabled=logging_raw["enabled"],
        level=str(logging_raw.get("level", "INFO")).upper(),
        format=logging_raw.get("format", "standard"),
        output=str(logging_raw.get("output", "console")).lower(),
        file_path=file_path,
    )

    # ------------------------------------------------------------------
    # Données communes
    # ------------------------------------------------------------------

    common = CommonDataConfig(
        schemas=data_raw["common"]["schemas"],
    )

    # ------------------------------------------------------------------
    # Catalogue
    # ------------------------------------------------------------------

    catalog_raw = data_raw["catalog"]

    catalog = CatalogConfig(
        financial=FinancialConfig(
            assets=_build_resource(catalog_raw["financial"]["assets"]),
            contracts=_build_resource(catalog_raw["financial"]["contracts"]),
        ),
        references=ReferencesConfig(
            economy=_build_economy_references(catalog_raw["references"]["economy"]),
        ),
    )

    # ------------------------------------------------------------------
    # Données externes
    # ------------------------------------------------------------------

    external_assets_raw = data_raw["external"]["assets"]

    external = ExternalDataConfig(
        assets=ExternalAssetsConfig(
            quotes=_build_resource(external_assets_raw["quotes"]),
            factsheets=FactsheetsConfig(
                source=_build_resource(external_assets_raw["factsheets"]["source"]),
                extracted=_build_resource(
                    external_assets_raw["factsheets"]["extracted"]
                ),
            ),
            scraped_data=_build_resource(external_assets_raw["scraped_data"]),
        ),
    )

    # ------------------------------------------------------------------
    # Données utilisateurs : entrées
    # ------------------------------------------------------------------

    customer_raw = data_raw["customer"]

    customer_input_raw = customer_raw["input"]
    wallet_input_raw = customer_input_raw["wallets"]

    customer_input = CustomerInputConfig(
        users=_build_resource(customer_input_raw["users"]),
        wallets=WalletInputConfig(
            balances=_build_resource(wallet_input_raw["balances"]),
            transactions=_build_resource(wallet_input_raw["transactions"]),
        ),
    )

    # ------------------------------------------------------------------
    # Données utilisateurs : calculées
    # ------------------------------------------------------------------

    calculated_raw = customer_raw["calculated"]

    calculated_users_raw = calculated_raw["users"]
    calculated_wallets_raw = calculated_raw["wallets"]

    customer_calculated = CustomerCalculatedConfig(
        users=CalculatedUsersConfig(
            balances=_build_resource(calculated_users_raw["balances"]),
            evolution=_build_resource(calculated_users_raw["evolution"]),
            dashboards=_build_resource(calculated_users_raw["dashboards"]),
        ),
        wallets=CalculatedWalletsConfig(
            transactions_enriched=_build_resource(
                calculated_wallets_raw["transactions_enriched"]
            ),
            balances=_build_resource(calculated_wallets_raw["balances"]),
            evolution=_build_resource(calculated_wallets_raw["evolution"]),
            dashboards=_build_resource(calculated_wallets_raw["dashboards"]),
        ),
    )

    customer = CustomerConfig(
        input=customer_input,
        calculated=customer_calculated,
    )

    # ------------------------------------------------------------------
    # Assemblage final
    # ------------------------------------------------------------------

    return AppConfig(
        app=app,
        logging=logging_config,
        data=DataSettings(
            common=common,
            catalog=catalog,
            external=external,
            customer=customer,
        ),
        api_keys=ApiKeys(
            fmp=os.getenv("FMP_API_KEY") or None,
            alpha_vantage=os.getenv("ALPHA_VANTAGE_API_KEY") or None,
        ),
        source_path=config_path.resolve(),
    )
