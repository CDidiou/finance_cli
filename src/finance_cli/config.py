# -*- coding: utf-8 -*-
"""Gestion de la configuration via un fichier YAML et Pydantic."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Chemin par défaut — ancré sur la racine du projet via __file__
#
#   __file__  →  <projet>/src/finance_cli/config.py # on utilise __file__ pour naviguer à l'intérieur du package! (dans src/<mon_package>)
#   .parent   →  <projet>/src/finance_cli/
#   .parent   →  <projet>/src/
#   .parent   →  <projet>/                ← racine
# ---------------------------------------------------------------------------


def _default_config_path() -> Path:
    # 1. Variable d'environnement (CI, Docker, overrides explicites)
    if env := os.getenv("MON_OUTIL_CONFIG"):
        return Path(env)
    # 2. Relatif au cwd — fonctionne avec `poetry run` et pytest
    return Path.cwd() / "config" / "config_app.yaml"


DEFAULT_CONFIG_PATH = _default_config_path()


# ---------------------------------------------------------------------------
# Sous-modèle : Logging
# ---------------------------------------------------------------------------

LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

LOG_FORMATS = {
    "simple": "%(levelname)s: %(message)s",
    "standard": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    "detailed": "%(asctime)s [%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
}


class LoggingConfig(BaseModel):
    """Configuration du logging."""

    enabled: bool = Field(default=True, description="Active ou désactive le logging")
    level: str = Field(default="INFO", description=f"Niveau : {sorted(LOG_LEVELS)}")
    format: str = Field(
        default="standard",
        description=(
            "Nom d'un format prédéfini (simple | standard | detailed) "
            "ou une chaîne de formatage Python directe."
        ),
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        v = v.upper()
        if v not in LOG_LEVELS:
            raise ValueError(
                f"level doit être parmi {sorted(LOG_LEVELS)}, reçu : {v!r}"
            )
        return v

    @property
    def resolved_format(self) -> str:
        """Retourne la chaîne de format finale (prédéfinie ou littérale)."""
        return LOG_FORMATS.get(self.format, self.format)

    @property
    def numeric_level(self) -> int:
        return getattr(logging, self.level)

    model_config = {"extra": "forbid", "validate_assignment": True}


# ---------------------------------------------------------------------------
# Sous-modèle : Data
# ---------------------------------------------------------------------------


class DataUsersConfig(BaseModel):
    """Configuration des données utilisateurs."""

    folder: Path = Field(
        default=Path("data/users"), description="Dossier des données utilisateurs"
    )

    @field_validator("folder", mode="before")
    @classmethod
    def resolve_path(cls, v):
        path = Path(v)
        return path.resolve() if path.is_absolute() else path

    model_config = {"extra": "forbid", "validate_assignment": True}


class DataContractsConfig(BaseModel):
    """Configuration des données contrats."""

    folder: Path = Field(
        default=Path("data/contracts"), description="Dossier des données contrats"
    )

    @field_validator("folder", mode="before")
    @classmethod
    def resolve_path(cls, v):
        path = Path(v)
        return path.resolve() if path.is_absolute() else path

    model_config = {"extra": "forbid", "validate_assignment": True}


class DataAssetsConfig(BaseModel):
    """Configuration des données actifs."""

    folder: Path = Field(
        default=Path("data/assets"), description="Dossier des données actifs"
    )

    @field_validator("folder", mode="before")
    @classmethod
    def resolve_path(cls, v):
        path = Path(v)
        return path.resolve() if path.is_absolute() else path

    model_config = {"extra": "forbid", "validate_assignment": True}


# ---------------------------------------------------------------------------
# Sous-modèle : Excel
# ---------------------------------------------------------------------------


class ExcelConfig(BaseModel):
    """Options spécifiques au format Excel."""

    data_dir: Path = Field(
        default=Path("R:/Finance"), description="Répertoire des données d'entrée"
    )

    @field_validator("data_dir", mode="before")
    @classmethod
    def make_absolute_path(cls, v):
        # On transforme la string en Path et on s'assure qu'il est absolu
        path = Path(v)
        # .resolve() transforme les chemins relatifs en absolus
        # et gère les bizarreries de slashs
        return path.resolve() if path.is_absolute() else path

    output_dir: Path = Field(default=Path("output"), description="Répertoire de sortie")
    sheet_name: str = Field(default="Data", description="Nom de l'onglet")
    date_format: str = Field(default="%Y-%m-%d", description="Format de date Python")
    include_header: bool = Field(default=True, description="Inclut la ligne d'en-tête")
    include_index: bool = Field(default=False, description="Inclut la colonne d'index")
    freeze_header: bool = Field(default=True, description="Fige la première ligne")
    max_col_width: int = Field(
        default=40,
        ge=5,
        le=255,
        description="Largeur maximale des colonnes en caractères (5–255)",
    )

    model_config = {"extra": "forbid", "validate_assignment": True}


# ---------------------------------------------------------------------------
# Sous-modèle : SQL
# ---------------------------------------------------------------------------


class SqlConfig(BaseModel):
    """Options spécifiques à la sortie SQL."""

    dialect: Literal["postgresql", "mysql", "sqlite", "mssql"] = Field(
        default="postgresql", description="Dialecte SQLAlchemy"
    )
    host: str = Field(default="localhost", description="Hôte du serveur")
    port: int = Field(default=5432, ge=0, le=65535, description="Port TCP")
    database: str = Field(default="", description="Nom de la base de données")
    user: str = Field(default="", description="Utilisateur SQL")
    schema_name: str = Field(
        default="public", description="Schéma cible (PostgreSQL/MSSQL)"
    )
    table: str = Field(default="data", description="Table cible par défaut")
    if_exists: Literal["fail", "replace", "append"] = Field(
        default="append", description="Comportement si la table existe déjà"
    )
    batch_size: int = Field(
        default=1000, ge=1, description="Lignes par batch d'insertion"
    )

    @model_validator(mode="after")
    def adjust_port_for_sqlite(self) -> SqlConfig:
        if self.dialect == "sqlite":
            object.__setattr__(self, "port", 0)
        return self

    @property
    def dsn(self) -> str:
        """URL de connexion SQLAlchemy (sans mot de passe)."""
        if self.dialect == "sqlite":
            return f"sqlite:///{self.database}"
        return f"{self.dialect}://{self.user}@{self.host}:{self.port}/{self.database}"

    model_config = {"extra": "forbid", "validate_assignment": True}


class DataConfig(BaseModel):
    """Configuration globale des données."""

    users: DataUsersConfig = Field(default_factory=DataUsersConfig)
    contracts: DataContractsConfig = Field(default_factory=DataContractsConfig)
    assets: DataAssetsConfig = Field(default_factory=DataAssetsConfig)
    tx_data_format: Literal["excel", "sql"] = Field(
        default="excel",
        description="Format de sortie des données transactionnelles",
        alias="tx-data_format",
    )
    excel: ExcelConfig = Field(default_factory=ExcelConfig)
    sql: SqlConfig = Field(default_factory=SqlConfig)

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "populate_by_name": True,
    }


# ---------------------------------------------------------------------------
# Modèle racine
# ---------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Configuration complète de l'application."""

    app_name: str = Field(default="finance-cli", description="Nom affiché de l'appli")
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    data: DataConfig = Field(default_factory=DataConfig)

    model_config = {"extra": "forbid", "validate_assignment": True}


# ---------------------------------------------------------------------------
# Gestionnaire de configuration
# ---------------------------------------------------------------------------


class ConfigManager:
    """Charge, sauvegarde et expose la configuration (format YAML)."""

    def __init__(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.path = path
        self._config: AppConfig | None = None

    @property
    def config(self) -> AppConfig:
        if self._config is None:
            self._config = self.load()
        return self._config

    # -- I/O ----------------------------------------------------------------

    def load(self) -> AppConfig:
        """Charge depuis le YAML. Retourne les défauts si le fichier est absent."""
        if not self.path.exists():
            return AppConfig()

        try:
            raw: Any = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigError(f"Fichier YAML invalide ({self.path}): {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigError(
                f"Le fichier de config doit être un mapping YAML ({self.path})"
            )

        try:
            return AppConfig.model_validate(raw)
        except Exception as exc:
            raise ConfigError(f"Erreur de validation de la config: {exc}") from exc

    def save(self) -> None:
        """Persiste la configuration courante sur disque."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self._to_yaml(self.config), encoding="utf-8")

    def init(self, overwrite: bool = False) -> bool:
        """Crée le fichier de config avec les valeurs par défaut."""
        if self.path.exists() and not overwrite:
            return False
        self._config = AppConfig()
        self.save()
        return True

    # -- Mise à jour --------------------------------------------------------

    def update(self, **kwargs: Any) -> None:
        """Met à jour des champs de premier niveau.

        Exemple : manager.update(data_format="sql")
        """
        updated = self.config.model_copy(update=kwargs)
        AppConfig.model_validate(updated.model_dump())
        self._config = updated
        self.save()

    def update_section(self, section: str, **kwargs: Any) -> None:
        """Met à jour une sous-section (logging, excel, sql).

        Exemple : manager.update_section("logging", level="DEBUG", enabled=True)
        """
        current = self.config.model_dump()
        if section not in current:
            raise ConfigError(
                f"Section inconnue : {section!r}. Disponibles : {list(current)}"
            )
        current[section].update(kwargs)
        self._config = AppConfig.model_validate(current)
        self.save()

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _to_yaml(cfg: AppConfig) -> str:
        raw = cfg.model_dump()
        _paths_to_str(raw)
        header = (
            "# Configuration de finance-cli\n"
            "# Généré automatiquement — modifiable à la main\n\n"
        )
        return header + yaml.dump(raw, allow_unicode=True, sort_keys=False, indent=2)

    def show(self) -> str:
        """Retourne la config courante en YAML formaté."""
        return self._to_yaml(self.config)

    def apply_logging(self) -> None:
        """Configure le logging Python selon la section [logging] de la config."""
        cfg = self.config.logging
        if not cfg.enabled:
            logging.disable(logging.CRITICAL)
            return
        logging.basicConfig(level=cfg.numeric_level, format=cfg.resolved_format)


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


def _paths_to_str(obj: Any) -> None:
    """Convertit récursivement les Path en str dans un dict (pour sérialisation YAML)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, Path):
                obj[k] = str(v)
            else:
                _paths_to_str(v)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ConfigError(RuntimeError):
    """Erreur liée à la configuration."""
