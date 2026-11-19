"""Résolution des chemins de ressources à partir de AppConfig."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, get_args

from finance_cli.config.config_models import AppConfig
from finance_cli.exceptions.configuration import (
    ResourceConfigurationError,
)

ResourceFormat = Literal["yaml", "excel", "pdf", "html"]
ALLOWED_FORMATS = frozenset(get_args(ResourceFormat))


@dataclass(frozen=True)
class ResourcePaths:
    folder: Path
    schemas: Path | None
    rules: Path | None
    data_format: ResourceFormat
    filename: str | None = None
    templates: Path | None = None
    styles: Path | None = None


class ConfigPathResolver:
    """Résout les chemins des ressources définies dans AppConfig.

    Les resource_key sont relatifs à `config.data`.
    Les séparateurs '/' et '.' sont acceptés.

    Exemples :
        - "catalog/financial/assets"
        - "catalog.references.economy"
        - "external/assets/quotes"
        - "external/assets/factsheets/extracted"
        - "customer/input/wallets/balances"
        - "customer/calculated/wallets/dashboards"
    """

    PATH_TYPES = frozenset(
        {
            "folder",
            "schemas",
            "rules",
            "templates",
            "styles",
        }
    )

    def __init__(self, config: AppConfig) -> None:
        self.config_data = config.data
        self.base_dir = config.base_dir.resolve()

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def resolve_resources(
        self,
        resource_key: str,
        context: dict[str, Any] | None = None,
    ) -> ResourcePaths:
        """Résout l'ensemble des propriétés d'une ressource."""

        node = self._get_node(resource_key)

        data_format = getattr(node, "format", None)

        if data_format not in ALLOWED_FORMATS:
            raise ResourceConfigurationError(
                f"Format invalide pour '{resource_key}' : {data_format!r}"
            )

        folder = self._resolve_path(node, "folder", required=True, context=context)

        schemas = self._resolve_path(node, "schemas", context=context)
        rules = self._resolve_path(node, "rules", context=context)
        templates = self._resolve_path(node, "templates", context=context)
        styles = self._resolve_path(node, "styles", context=context)

        if data_format == "yaml" and schemas is None:
            raise ResourceConfigurationError(
                f"Un schéma est requis pour '{resource_key}' au format YAML."
            )

        return ResourcePaths(
            folder=folder,
            schemas=schemas,
            rules=rules,
            data_format=data_format,
            filename=self._resolve_optional_filename(resource_key, context),
            templates=templates,
            styles=styles,
        )

    def resolve_directory(
        self,
        resource_key: str,
        path_type: str = "folder",
        context: dict[str, Any] | None = None,
    ) -> Path:
        """Résout un chemin de répertoire individuel."""

        if path_type not in self.PATH_TYPES:
            raise ResourceConfigurationError(
                f"Type de chemin non autorisé : {path_type!r}"
            )

        node = self._get_node(resource_key)

        path = self._resolve_path(
            node,
            path_type,
            required=True,
            context=context,
        )

        if path is None:
            raise ResourceConfigurationError(
                f"Chemin '{path_type}' absent pour '{resource_key}'."
            )

        return path

    def resolve_filename(
        self,
        resource_key: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Génère le nom de fichier à partir de son modèle."""

        node = self._get_node(resource_key)
        filename = getattr(node, "filename", None)

        if not isinstance(filename, str) or not filename.strip():
            raise ResourceConfigurationError(
                f"Aucun modèle de nom de fichier valide pour '{resource_key}'."
            )

        if context is not None:
            filename = self._interpolate(filename, context)

        return filename

    def _resolve_optional_filename(
        self,
        resource_key: str,
        context: dict[str, Any] | None,
    ) -> str | None:
        """Résout le nom de fichier si un modèle est configuré et résolvable."""

        node = self._get_node(resource_key)
        filename = getattr(node, "filename", None)

        if filename is None:
            return None

        if not isinstance(filename, str) or not filename.strip():
            raise ResourceConfigurationError(
                f"Modèle de nom de fichier invalide pour '{resource_key}'."
            )

        if context is None:
            return filename

        return self._interpolate(filename, context)

    def resolve_file_path(
        self,
        resource_key: str,
        context: dict[str, Any] | None = None,
        path_type: str = "folder",
    ) -> Path:
        """Construit le chemin complet d'un fichier."""

        directory = self.resolve_directory(
            resource_key,
            path_type=path_type,
            context=context,
        )

        filename = self.resolve_filename(
            resource_key,
            context=context,
        )

        return directory / filename

    # ------------------------------------------------------------------
    # Navigation dans AppConfig
    # ------------------------------------------------------------------

    def _get_node(self, resource_key: str) -> object:
        """Navigue dans les dataclasses selon un chemin 'a/b/c' ou 'a.b.c'."""

        keys = [key for key in re.split(r"[./]", resource_key.strip()) if key]

        if not keys:
            raise ValueError("resource_key vide.")

        node: object = self.config_data

        for key in keys:
            if not hasattr(node, key):
                raise KeyError(
                    f"Ressource introuvable : '{resource_key}' "
                    f"(échec sur le segment '{key}')."
                )

            node = getattr(node, key)

        if not hasattr(node, "format"):
            raise ValueError(
                f"Le nœud '{resource_key}' n'est pas une ressource configurée."
            )

        return node

    # ------------------------------------------------------------------
    # Résolution des chemins
    # ------------------------------------------------------------------

    def _resolve_path(
        self,
        node: object,
        key: str,
        required: bool = False,
        context: dict[str, Any] | None = None,
    ) -> Path | None:
        """Résout un chemin défini dans un objet de configuration."""

        value = getattr(node, key, None)

        if value is None or value == "":
            if required:
                raise KeyError(f"Chemin obligatoire absent : '{key}'.")
            return None

        path = str(value)

        if context:
            path = self._interpolate(path, context)

        return self._resolve_absolute_path(path)

    def _resolve_absolute_path(self, path: str) -> Path:
        """Convertit un chemin configuré en chemin absolu."""

        resolved_path = Path(path)

        if not resolved_path.is_absolute():
            resolved_path = self.base_dir / resolved_path

        return resolved_path.resolve()

    # ------------------------------------------------------------------
    # Interpolation
    # ------------------------------------------------------------------

    @staticmethod
    def _interpolate(
        text: str,
        context: dict[str, Any],
    ) -> str:
        """Remplace les tokens par les valeurs du contexte."""

        def replace_match(match: re.Match[str]) -> str:
            token_path = match.group(1).strip()
            value: Any = context

            for key in token_path.split("."):
                if not isinstance(value, dict) or key not in value:
                    raise ResourceConfigurationError(
                        f"Valeur manquante pour le token '<{token_path}>'."
                    )

                value = value[key]

            if value is None:
                raise ResourceConfigurationError(
                    f"Valeur nulle pour le token '<{token_path}>'."
                )

            return str(value)

        return re.sub(r"<([^>]+)>", replace_match, text)
