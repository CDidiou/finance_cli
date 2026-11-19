"""Repository for YAML-backed financial assets."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from finance_cli.adapters.yaml import resource_reader
from finance_cli.common import find_yaml_by_id, inheritance, yaml_io
from finance_cli.exceptions.assets import (
    AssetContentError,
    AssetStorageError,
)
from finance_cli.models.asset import Asset
from finance_cli.validation import (
    catalog_validation_error,
    rule_loader,
    rule_validator,
    schema_validator,
)

logger = logging.getLogger(__name__)


class AssetRepository:
    """Load, validate and persist financial assets."""

    def __init__(
        self,
        folder: Path,
        rules_dir: Path | None,
        schema_validator: schema_validator.SchemaValidator,
        *,
        model: type,
    ) -> None:
        self.reader = resource_reader.YamlResourceReader(folder)

        self.root = folder
        self.rules_dir = rules_dir

        self.rule_loader = rule_loader.RuleLoader(rules_dir) if rules_dir else None
        self.rule_validator = rule_validator.RuleValidator()
        self.schema_validator = schema_validator
        self.model = model

    # --- API PUBLIQUE ---

    def get_by_id(self, asset_id: str):
        """Charge un asset et valide ses données."""

        path = self._find_implementation(asset_id)

        try:
            data = self._load(path)
        except ValueError as exc:
            raise AssetContentError(
                f"Contenu invalide dans la fiche de l'actif {asset_id!r}."
            ) from exc
        except OSError as exc:
            raise AssetStorageError(
                f"Impossible de lire la fiche de l'actif {asset_id!r}."
            ) from exc

        self._validate(data, asset_id)

        return self.model.model_validate(data)

    def save(self, asset: Asset) -> Path:
        """Sauvegarde un asset existant au format YAML."""
        asset_id = asset.id

        try:
            path = self._find_implementation(asset_id)
        except OSError as exc:
            raise AssetStorageError(
                f"Impossible d'accéder au catalogue pour l'actif {asset_id!r}."
            ) from exc

        data = asset.model_dump(mode="json")

        # Vérifie les données avant leur persistance.
        self._validate(data, asset_id)

        try:
            yaml_io.dump_yaml_mapping(path, data)
        except yaml.YAMLError as exc:
            raise AssetContentError(
                f"Impossible de sérialiser les données de l'actif {asset_id!r} en YAML."
            ) from exc
        except OSError as exc:
            raise AssetStorageError(
                f"Impossible de sauvegarder l'actif {asset_id!r} dans {path}."
            ) from exc

        logger.info("Asset '%s' sauvegardé dans %s", asset_id, path)

        return path

    def list_ids(self) -> list[str]:
        """Retourne les identifiants sans résoudre l'héritage."""
        return [path.stem for path in self.list_files()]

    def load_all(self) -> list[Asset]:
        """Charge l'ensemble des assets du catalogue."""
        return [self.get_by_id(asset_id) for asset_id in self.list_ids()]

    def list_files(self) -> list[Path]:
        """Retourne les fichiers YAML du catalogue."""
        _, files = self.reader.list_files()
        return files

    def get_category_path(self, asset_id: str) -> Path:
        """Retourne le chemin relatif du répertoire contenant l'asset."""
        try:
            implementation_file = self._find_implementation(asset_id)
            return implementation_file.parent.relative_to(self.root)
        except OSError as exc:
            raise AssetStorageError(
                f"Impossible d'accéder au chemin de l'actif {asset_id!r}."
            ) from exc

    # --- VALIDATION ---

    def _validate(self, data: dict[str, Any], asset_id: str) -> None:
        schema_name = self._get_schema_name(data)

        # 1. Validation structurelle
        issues = self.schema_validator.validate(data, schema_name)

        # 2. Validation des règles métier
        if not issues and self.rule_loader:
            rules = self._get_rules(data)
            issues = self.rule_validator.validate(data, rules)

        if issues:
            raise catalog_validation_error.InCatalogValidationError(
                id_catalog=asset_id,
                issues=issues,
            )

    # --- HELPERS INTERNES ---

    def _find_implementation(self, asset_id: str) -> Path:
        return find_yaml_by_id.find_yaml_file(asset_id, self.root)

    def _load(self, implementation_file: Path) -> dict[str, Any]:
        return inheritance.load_data_with_extends(
            implementation_file,
            root=self.root,
        )

    def _get_rules(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Charge les règles métier de la catégorie."""
        if not self.rule_loader:
            return []

        category = (data.get("general_info") or {}).get("category")
        if not category:
            item_id = data.get("id", "<unknown>")
            raise ValueError(f"Élément '{item_id}' n'a pas de 'general_info.category'")

        return self.rule_loader.load(category)

    def _get_schema_name(self, data: dict[str, Any]) -> str:
        general_info = data.get("general_info") or {}
        category = general_info.get("category")

        if not category:
            item_id = data.get("id", "<unknown>")
            raise ValueError(f"Élément '{item_id}' n'a pas de 'general_info.category'")

        # schema_filename = f"{category}.schemas.yaml"
        # schema_path = self.schemas_dir / schema_filename
        schema_name = f"{category}.schemas"

        # if not schema_path.exists():
        #    raise FileNotFoundError(
        #        f"Schéma introuvable pour la catégorie '{category}' : {schema_path}"
        #    )

        return schema_name
