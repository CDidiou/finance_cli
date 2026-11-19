"""Résolution de l'héritage `extends` pour les fichiers de données YAML.

Ne gère plus les schémas (responsabilité de JSON Schema).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from finance_cli.common import merge, yaml_io

logger = logging.getLogger(__name__)


def resolve_extends_chain(
    path: Path,
    *,
    root: Path | None = None,
) -> list[Path]:
    """Construit la chaîne d'héritage [ancêtre le plus éloigné → ... → fichier].

    Raises:
        ValueError: cycle détecté ou fichier introuvable.
        TypeError: valeur de ``extends`` invalide.
    """
    path = path.resolve()
    root = (root or path.parent).resolve()

    chain: list[Path] = []
    visited: set[Path] = set()
    current: Path | None = path

    while current is not None:
        current = current.resolve()

        if current in visited:
            cycle = " → ".join(str(p) for p in chain) + f" → {current}"
            raise ValueError(f"Cycle d'héritage détecté : {cycle}")

        if not current.is_file():
            raise ValueError(f"Fichier d'héritage introuvable : {current}")

        visited.add(current)
        chain.append(current)

        data = yaml_io.load_yaml_mapping(current)
        extends = data.get("extends")

        if extends is None:
            current = None
        elif isinstance(extends, str):
            current = _resolve_extends_path(extends, base=current.parent, root=root)
        elif isinstance(extends, Sequence) and not isinstance(extends, (str, bytes)):
            if len(extends) != 1:
                raise ValueError(
                    "extends multiple non supporté pour l'instant "
                    f"({current}) : {extends!r}"
                )
            if not isinstance(extends[0], str):
                raise TypeError(f"extends doit contenir des chaînes : {extends!r}")
            current = _resolve_extends_path(extends[0], base=current.parent, root=root)
        else:
            raise TypeError(
                f"extends doit être une chaîne ou une liste d'une chaîne "
                f"({current}) : {extends!r}"
            )

    # chain est actuellement [enfant → ... → racine], on inverse
    chain.reverse()
    return chain


def load_merged_data(chain: Sequence[Path]) -> dict[str, Any]:
    """Charge et fusionne une chaîne déjà résolue (l'enfant gagne)."""
    if not chain:
        raise ValueError("Chaîne d'héritage vide")

    merged: dict[str, Any] = {}
    for file_path in chain:
        data = yaml_io.load_yaml_mapping(file_path)
        if not isinstance(data, Mapping):
            raise TypeError(f"Le fichier doit contenir un mapping : {file_path}")

        # On retire extends avant la fusion pour ne pas le propager
        data = dict(data)
        data.pop("extends", None)
        # logger.info(f"target (avant merge): {merged}")
        # logger.info(f"source data to merge are from: {file_path}")
        # logger.info(f"source data: {data}")
        merge.deep_merge(merged, data, on_conflict="overwrite")
        # logger.info(f"target (apres merge): {merged}")
    return merged


def load_data_with_extends(
    path: str | Path,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Point d'entrée pratique : résout la chaîne puis fusionne les données."""
    path = Path(path)
    root_path = Path(root) if root is not None else None
    chain = resolve_extends_chain(path, root=root_path)
    # logger.info(f"Chaine heritage: {chain}")
    return load_merged_data(chain)


def _resolve_extends_path(extends: str, *, base: Path, root: Path) -> Path:
    """Résout un chemin d'extends (absolu, relatif au fichier, ou relatif au root)."""
    candidate = Path(extends)

    if candidate.is_absolute():
        return candidate

    # 1. Relatif au fichier courant
    relative_to_file = (base / candidate).resolve()
    if relative_to_file.is_file():
        return relative_to_file

    # 2. Relatif à la racine fournie
    relative_to_root = (root / candidate).resolve()
    if relative_to_root.is_file():
        return relative_to_root

    raise ValueError(
        f"Impossible de résoudre extends={extends!r} (cherché depuis {base} et {root})"
    )


def resolve_category_path(
    path: Path,
    *,
    root: Path,
) -> Path:
    """Retourne le chemin hiérarchique d'une catégorie à partir de ses parents."""

    chain = resolve_extends_chain(path, root=root)

    return Path(*[item.stem for item in chain])
