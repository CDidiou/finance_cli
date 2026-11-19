"""Recherche d'implémentations d'assets dans le catalogue."""

from __future__ import annotations

from pathlib import Path

from finance_cli.common import yaml_io
from finance_cli.exceptions.assets import (
    AssetAmbiguousError,
    AssetContentError,
    AssetNotFoundError,
)


def find_yaml_file(isin: str, category_root: Path) -> Path:
    """Localise le fichier d'implémentation d'un actif par son ISIN (ou id).

    Parcourt ``<category_root>/**/*.yaml``.
    <category_root>: data/assets or data/contracts or external-data/users
    Match sur le stem du fichier, puis sur les champs ``id`` / ``isin``.

    Raises:
        ValueError: aucune fiche, ou plusieurs fiches pour le même identifiant.
    """
    normalized = isin.strip().casefold()
    if not normalized:
        raise ValueError(f"ISIN invalide : {isin!r}")

    matches: list[Path] = []
    for asset_file in category_root.rglob("*.yaml"):
        if asset_file.name.endswith(".schemas.yaml"):
            continue

        # match rapide sur le nom de fichier
        if asset_file.stem.casefold() == normalized:
            matches.append(asset_file)
            continue

        # sinon inspection des champs id / isin
        try:
            asset = yaml_io.load_yaml_mapping(asset_file)
        except ValueError as exc:
            raise AssetContentError(
                f"Contenu YAML invalide dans la fiche d'actif : {asset_file}"
            ) from exc
        for field in ("id", "isin"):
            value = asset.get(field)
            if isinstance(value, str) and value.strip().casefold() == normalized:
                matches.append(asset_file)
                break

    if not matches:
        raise AssetNotFoundError(
            f"Aucune fiche d'actif trouvée pour l'ISIN {isin!r} sous {category_root}"
        )

    if len(matches) > 1:
        paths = ", ".join(path.as_posix() for path in matches)
        raise AssetAmbiguousError(
            f"Plusieurs fiches d'actif pour l'ISIN {isin!r} : {paths}"
        )
    return matches[0]
