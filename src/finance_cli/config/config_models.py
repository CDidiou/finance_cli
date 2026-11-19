"""Modèles typés de la configuration applicative."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Base commune
# ---------------------------------------------------------------------------


class ConfigModel(BaseModel):
    """Base commune des modèles de configuration."""

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
    )


# ---------------------------------------------------------------------------
# Configuration générale
# ---------------------------------------------------------------------------


class AppSettings(ConfigModel):
    name: Literal["patrimonia"]
    version: str
    base_dir: Path = Path(".")


class LoggingSettings(ConfigModel):
    enabled: bool
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: Literal["simple", "standard", "detailed"] = "standard"
    output: Literal["console", "file"] = "console"
    file_path: Path | None = None


# ---------------------------------------------------------------------------
# Ressources configurables
# ---------------------------------------------------------------------------


class ResourceConfig(ConfigModel):
    format: str
    folder: str
    filename: str | None = None
    schemas: str | None = None
    rules: str | None = None
    templates: str | None = None
    styles: str | None = None


class CommonDataConfig(ConfigModel):
    schemas: str


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


class FinancialConfig(ConfigModel):
    assets: ResourceConfig
    contracts: ResourceConfig


class EconomyReferencesConfig(ConfigModel):
    format: Literal["yaml"]
    folder: str
    schemas: str
    rules: str


class ReferencesConfig(ConfigModel):
    economy: EconomyReferencesConfig


class CatalogConfig(ConfigModel):
    financial: FinancialConfig
    references: ReferencesConfig


# ---------------------------------------------------------------------------
# Données externes
# ---------------------------------------------------------------------------


class FactsheetsConfig(ConfigModel):
    source: ResourceConfig
    extracted: ResourceConfig


class ExternalAssetsConfig(ConfigModel):
    quotes: ResourceConfig
    factsheets: FactsheetsConfig
    scraped_data: ResourceConfig


class ExternalDataConfig(ConfigModel):
    assets: ExternalAssetsConfig


# ---------------------------------------------------------------------------
# Données utilisateurs
# ---------------------------------------------------------------------------


class WalletInputConfig(ConfigModel):
    balances: ResourceConfig
    transactions: ResourceConfig


class CustomerInputConfig(ConfigModel):
    users: ResourceConfig
    wallets: WalletInputConfig


class CalculatedUsersConfig(ConfigModel):
    balances: ResourceConfig
    evolution: ResourceConfig
    dashboards: ResourceConfig


class CalculatedWalletsConfig(ConfigModel):
    transactions_enriched: ResourceConfig
    balances: ResourceConfig
    evolution: ResourceConfig
    dashboards: ResourceConfig


class CustomerCalculatedConfig(ConfigModel):
    users: CalculatedUsersConfig
    wallets: CalculatedWalletsConfig


class CustomerConfig(ConfigModel):
    input: CustomerInputConfig
    calculated: CustomerCalculatedConfig


# ---------------------------------------------------------------------------
# Données et configuration applicative
# ---------------------------------------------------------------------------


class DataSettings(ConfigModel):
    common: CommonDataConfig
    catalog: CatalogConfig
    external: ExternalDataConfig
    customer: CustomerConfig


class ApiKeys(ConfigModel):
    fmp: str | None = Field(default=None, repr=False)
    alpha_vantage: str | None = Field(default=None, repr=False)


class AppConfig(ConfigModel):
    app: AppSettings
    logging: LoggingSettings
    data: DataSettings
    api_keys: ApiKeys
    source_path: Path

    @property
    def base_dir(self) -> Path:
        """Répertoire racine de l'application."""
        return self.app.base_dir
