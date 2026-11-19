from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from finance_cli.common import yaml_io

"""
Charge les schémas JSON Schema.
Gère le Registry et les $ref.
Fournit les validateurs JSON Schema.

---

Use of SchemaLoader:
    from validation.schema_loader import SchemaLoader
    loader = SchemaLoader("config/config_app.yaml")
    validator = loader.resolve_schema("share")
    validator.validate(asset_data)
    # ou directement: loader.validate("share", asset_data)

Pour récupérer un schéma:
    schema = loader.get_schema("assets")

"""

logger = logging.getLogger(__name__)


class SchemaLoaderError(Exception):
    """Erreur lors du chargement ou de la préparation d'un schéma."""


class SchemaLoader:
    """
    Charge les schémas JSON Schema YAML locaux et construit
    des validateurs capables de résoudre les références $ref.

    Les schémas sont identifiés par leur propriété $id.
    """

    def __init__(
        self,
        schemas_dir: Path,
        common_schemas_dir: Path,
    ) -> None:

        self.schemas_dir = schemas_dir
        self.common_schemas_dir = common_schemas_dir

        if not self.schemas_dir.is_dir():
            raise SchemaLoaderError(
                f"Dossier de schémas introuvable : {self.schemas_dir}"
            )

        if self.common_schemas_dir and not self.common_schemas_dir.is_dir():
            raise SchemaLoaderError(
                f"Dossier de schémas communs introuvable : {self.common_schemas_dir}"
            )

        self._schemas: dict[str, dict[str, Any]] = {}
        self._schema_ids: dict[str, str] = {}
        self._validators: dict[str, Draft202012Validator] = {}
        self.registry = Registry()

        self._load_schemas()
        self._build_registry()

    # --- API PUBLIQUE ---
    def validate(
        self,
        schema_name: str,
        data: dict[str, Any],
    ) -> None:
        """
        Valide des données et lève une exception si elles sont invalides.
        """

        validator = self.resolve_schema(schema_name)
        errors = sorted(
            validator.iter_errors(data),
            key=lambda error: list(map(str, error.absolute_path)),
        )

        if errors:
            messages = []

            for error in errors:
                location = (
                    ".".join(str(part) for part in error.absolute_path) or "<racine>"
                )

                messages.append(f"- {location} : {error.message}")

            raise SchemaLoaderError("Validation échouée :\n" + "\n".join(messages))

    def resolve_schema(
        self,
        schema_name: str,
    ) -> Draft202012Validator:
        """
        Construit et retourne un validateur JSON Schema.

        Le Registry permet de résoudre les $ref locaux.
        jsonschema applique automatiquement allOf et les autres
        mots-clés de composition.
        """

        schema_id = self._get_schema_id(schema_name)

        if schema_id not in self._validators:
            schema = self._schemas[schema_id]

            self._validators[schema_id] = Draft202012Validator(
                schema,
                registry=self.registry,
                format_checker=FormatChecker(),
            )

        return self._validators[schema_id]

    def get_schema(self, schema_name: str) -> dict[str, Any]:
        """
        Retourne le contenu d'un schéma.

        schema_name peut être :
        - assets
        - share
        - assets.schema
        - un $id complet
        """

        schema_id = self._get_schema_id(schema_name)
        return self._schemas[schema_id]

    # --- HELPERS INTERNES ---
    def _load_schemas(self) -> None:
        """Charge les schémas locaux et les schémas communs."""

        schema_files = set(self.schemas_dir.rglob("*.schemas.yaml"))

        if self.common_schemas_dir:
            schema_files.update(self.common_schemas_dir.rglob("*.schemas.yaml"))

        if not schema_files:
            raise SchemaLoaderError(f"Aucun schéma trouvé dans {self.schemas_dir}")

        for path in sorted(schema_files):
            schema = yaml_io.load_yaml_mapping(path)

            schema_id = schema.get("$id")
            if not isinstance(schema_id, str) or not schema_id.strip():
                raise SchemaLoaderError(
                    f"Le schéma {path} doit déclarer un $id non vide."
                )

            if schema_id in self._schemas:
                raise SchemaLoaderError(f"Identifiant $id dupliqué : {schema_id}")

            try:
                Draft202012Validator.check_schema(schema)
            except Exception as exc:
                raise SchemaLoaderError(
                    f"Schéma JSON Schema invalide dans {path} : {exc}"
                ) from exc

            self._schemas[schema_id] = schema

            stem = path.stem
            self._schema_ids[stem] = schema_id

    def _build_registry(self) -> None:
        """
        Enregistre toutes les ressources dans le Registry.

        Les références $ref sont résolues par referencing,
        sans accès réseau.
        """

        registry = Registry()

        for schema_id, schema in self._schemas.items():
            resource = Resource.from_contents(
                schema,
                default_specification=DRAFT202012,
            )

            registry = registry.with_resource(
                uri=schema_id,
                resource=resource,
            )

        self.registry = registry

    def _get_schema_id(self, schema_name: str) -> str:
        """Retrouve le $id à partir d'un nom court, d'un stem ou d'un $id."""

        # 1. Déjà un $id connu
        if schema_name in self._schemas:
            return schema_name

        # 2. stem ("equity.schemas") [Nom court ("equity") en option]
        if schema_name in self._schema_ids:
            return self._schema_ids[schema_name]

        raise SchemaLoaderError(f"Schéma inconnu : {schema_name}")
