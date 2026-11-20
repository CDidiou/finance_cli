"""Validation des références aux référentiels métier."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finance_cli.adapters.yaml import yaml_io

"""
Référentiels:
    Contient REFERENCE_VALIDATORS.
    Vérifie les références dans les référentiels YAML.
    Centralise le chargement des référentiels.

---

Use of ReferenceValidator:
    reference_validator = ReferenceValidator()

    assert reference_validator.validate_value(
        "EUR",
        "currency",
        "trading_places[0].currency",
    ) == []

    assert reference_validator.validate_value(
        "XXX",
        "currency",
        "trading_places[0].currency",
    ) == ["trading_places[0].currency"]

    assert reference_validator.validate_value(
        10,
        "gics",
        "general_info.sector",
    ) == []    
"""


class ReferenceValidatorError(Exception):
    """Erreur lors du chargement ou de la validation des référentiels."""


class ReferenceValidator:
    """Valide les références aux référentiels métier."""

    REFERENCE_FILES = {
        "currency": ("currency.yaml", "currencies", "code"),
        "gics": ("gics.yaml", "gics_sectors", "code"),
        "stock_exchange": (
            "stock_exchanges.yaml",
            "stock_exchanges",
            "acronym",
        ),
        "benchmark": ("benchmarks.yaml", "benchmarks", "symbol"),
        "broker": ("brokers.yaml", "brokers", "id"),
        "asset_manager": (
            "asset_managers.yaml",
            "asset_managers",
            "code",
        ),
    }

    def __init__(self, references_dir: Path) -> None:
        self._valid_values: dict[str, set[Any]] = {}
        self._load_references(references_dir)

    # --- API PUBLIQUE ---
    def validate_value(
        self,
        value: Any,
        reference: str,
        path: str = "",
    ) -> list[str]:
        """Vérifie qu'une valeur existe dans un référentiel."""

        if reference not in self.REFERENCE_FILES:
            raise ReferenceValidatorError(f"Référence inconnue : {reference!r}")

        if reference == "gics":
            if not isinstance(value, int) or isinstance(value, bool):
                return [path or "racine"]
        elif not isinstance(value, str):
            return [path or "racine"]

        if value not in self._valid_values[reference]:
            return [path or "racine"]

        return []

    # --- HELPERS INTERNES ---
    def _load_references(self, references_dir: Path) -> None:
        """Charge les référentiels et construit les ensembles de valeurs valides."""

        for reference_name, (filename, section, field) in self.REFERENCE_FILES.items():
            reference_path = references_dir / filename

            if not reference_path.is_file():
                raise FileNotFoundError(f"Référentiel introuvable : {reference_path}")

            data = yaml_io.load_yaml_mapping(reference_path)
            entries = data.get(section, [])

            if not isinstance(entries, list):
                raise ReferenceValidatorError(
                    f"Section {section!r} invalide dans {filename}."
                )

            values = set()

            for index, entry in enumerate(entries):
                if not isinstance(entry, dict) or field not in entry:
                    raise ReferenceValidatorError(
                        f"Entrée invalide dans {filename}, "
                        f"section {section}, index {index} : "
                        f"champ {field!r} manquant."
                    )

                values.add(entry[field])

            self._valid_values[reference_name] = values
