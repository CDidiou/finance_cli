"""Fusion profonde de mappings (données et schémas)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal


def deep_merge(
    target: dict[str, Any],
    source: dict[str, Any],
    *,
    on_conflict: Literal["overwrite", "raise"] = "overwrite",
    context: str | Path | None = None,
) -> None:
    """Fusionne ``source`` dans ``target`` en place.

    - ``on_conflict="overwrite"`` : la valeur de source remplace celle de target
      (comportement classique pour les données YAML héritées).
    - ``on_conflict="raise"`` : lève ValueError si deux valeurs scalaires diffèrent
      (comportement pour la fusion de schémas).
    """
    for key, value in source.items():
        if (
            key == "rules"
            and isinstance(value, list)
            and isinstance(target.get(key), list)
        ):
            target[key] = target[key] + value
            continue

        if key not in target:
            if isinstance(value, dict):
                target[key] = {}
                deep_merge(target[key], value, on_conflict=on_conflict, context=context)
            else:
                target[key] = value
            continue

        if isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value, on_conflict=on_conflict, context=context)
            continue

        if on_conflict == "raise" and target[key] != value:
            loc = f" dans {context}" if context else ""
            raise ValueError(f"Schémas incompatibles pour '{key}'{loc}")

        # overwrite (ou valeurs identiques)
        target[key] = value
