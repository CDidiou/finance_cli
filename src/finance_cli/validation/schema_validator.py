"""Orchestration de la validation des données d'actifs."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import unquote, urldefrag, urljoin

from finance_cli.validation.reference_validator import ReferenceValidator

logger = logging.getLogger(__name__)

"""
Validation structurelle:
    Orchestre la validation.
    Lance la validation structurelle.
    Lance ensuite les validations métier si la structure est valide.
    Retourne les erreurs de validation.

---

Use of SchemaValidator:
    schema_loader = SchemaLoader(config_path)
    reference_validator = ReferenceValidator()

    schema_validator = SchemaValidator(
        schema_loader=schema_loader,
        reference_validator=reference_validator,
    )

    issues = schema_validator.validate(
        value=asset_data,
        schema_name="share",
    )

    if issues:
        print("Erreurs de validation :")
        for issue in issues:
            print(f"- {issue}")
"""


class SchemaValidatorError(Exception):
    """Erreur lors de l'exécution de la validation."""


class SchemaValidator:
    """Valide la structure et les références métier d'une donnée."""

    def __init__(
        self,
        schema_loader: Any,
        reference_validator: ReferenceValidator,
    ) -> None:
        self.schema_loader = schema_loader
        self.reference_validator = reference_validator

    # --- API PUBLIQUE ---
    def validate(
        self,
        value: Any,
        schema_name: str,
    ) -> list[str]:
        """Exécute la validation structurelle puis métier.

        Retourne une liste de chemins invalides.
        """

        validator = self.schema_loader.resolve_schema(schema_name)

        # 1. Validation structurelle JSON Schema.
        structural_errors = sorted(
            validator.iter_errors(value),
            key=lambda error: list(error.absolute_path),
        )
        # logger.info(f"(schema validator) structural: {structural_errors}")

        if structural_errors:
            return [
                self._format_error_path(error.absolute_path)
                for error in structural_errors
            ]

        # 2. Validation des références métier.
        schema = self.schema_loader.get_schema(schema_name)

        reference_errors = self._validate_references(
            value=value,
            schema=schema,
        )

        # logger.info(f"(schema validator) reference: {reference_errors}")
        return sorted(set(reference_errors))

    # --- HELPERS INTERNES ---
    @staticmethod
    def _format_error_path(path: Any) -> str:
        """Convertit un chemin JSON Schema en chemin lisible."""

        parts = []

        for part in path:
            if isinstance(part, int):
                if parts:
                    parts[-1] += f"[{part}]"
                else:
                    parts.append(f"[{part}]")
            else:
                parts.append(str(part))

        return ".".join(parts) if parts else "racine"

    def _validate_references(
        self,
        value: Any,
        schema: dict[str, Any],
    ) -> list[str]:
        """Parcourt les données et valide les références x-reference."""

        issues: list[str] = []

        self._walk_schema(
            value=value,
            schema=schema,
            path="",
            base_uri=schema.get("$id", ""),
            visited=set(),
            issues=issues,
        )

        return issues

    def _walk_schema(
        self,
        value: Any,
        schema: Any,
        path: str,
        base_uri: str,
        visited: set[tuple[str, int, str]],
        issues: list[str],
    ) -> None:
        """Parcourt un schéma en tenant compte de allOf et des $ref."""

        if not isinstance(schema, dict):
            return

        # Résolution d'une référence JSON Schema.
        reference = schema.get("$ref")

        if reference is not None:
            resolved_uri = urljoin(base_uri, reference)
            visit_key = (resolved_uri, id(value), path)

            if visit_key not in visited:
                visited.add(visit_key)

                target_schema = self._resolve_ref(resolved_uri)

                self._walk_schema(
                    value=value,
                    schema=target_schema,
                    path=path,
                    base_uri=urldefrag(resolved_uri)[0],
                    visited=visited,
                    issues=issues,
                )

        # Validation d'une référence métier.
        reference_name = schema.get("x-reference")

        if reference_name is not None and value is not None:
            issues.extend(
                self.reference_validator.validate_value(
                    value=value,
                    reference=reference_name,
                    path=path or "racine",
                )
            )

        # Composition des schémas.
        for subschema in schema.get("allOf", []):
            self._walk_schema(
                value=value,
                schema=subschema,
                path=path,
                base_uri=base_uri,
                visited=visited,
                issues=issues,
            )

        # Propriétés d'un objet.
        properties = schema.get("properties", {})

        if isinstance(value, dict) and isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key not in value:
                    continue

                child_path = f"{path}.{key}" if path else key

                self._walk_schema(
                    value=value[key],
                    schema=child_schema,
                    path=child_path,
                    base_uri=base_uri,
                    visited=visited,
                    issues=issues,
                )

        # Éléments d'une liste.
        if isinstance(value, list):
            items_schema = schema.get("items")

            if isinstance(items_schema, dict):
                for index, item in enumerate(value):
                    item_path = f"{path}[{index}]" if path else f"[{index}]"

                    self._walk_schema(
                        value=item,
                        schema=items_schema,
                        path=item_path,
                        base_uri=base_uri,
                        visited=visited,
                        issues=issues,
                    )

    def _resolve_ref(self, reference_uri: str) -> dict[str, Any]:
        """Résout une référence locale via le Registry du SchemaLoader."""

        resource_uri, fragment = urldefrag(reference_uri)

        try:
            schema = self.schema_loader.registry.contents(resource_uri)
        except Exception as exc:
            raise SchemaValidatorError(
                f"Impossible de résoudre la référence : {reference_uri}"
            ) from exc

        if not fragment:
            return schema

        # Résolution d'un JSON Pointer.
        if not fragment.startswith("/"):
            raise SchemaValidatorError(f"Fragment non pris en charge : {reference_uri}")

        target = schema

        for token in fragment.lstrip("/").split("/"):
            token = unquote(token)
            token = token.replace("~1", "/").replace("~0", "~")

            try:
                if isinstance(target, list):
                    target = target[int(token)]
                else:
                    target = target[token]
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                raise SchemaValidatorError(
                    f"Fragment introuvable : {reference_uri}"
                ) from exc

        if not isinstance(target, dict):
            raise SchemaValidatorError(
                f"La référence ne désigne pas un schéma objet : {reference_uri}"
            )

        return target
