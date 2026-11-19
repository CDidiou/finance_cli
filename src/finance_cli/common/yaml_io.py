"""Lecture et écriture de fichiers YAML."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_yaml_mapping(filepath: Path) -> dict[str, Any]:
    """Charge un fichier YAML dont la racine doit être un mapping.

    Raises:
        FileNotFoundError: fichier absent.
        OSError: erreur d'accès ou de lecture.
        ValueError: YAML invalide ou racine non-mapping.
    """
    with filepath.open(encoding="utf-8") as stream:
        try:
            data = yaml.load(stream, Loader=NoDatesSafeLoader)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML invalide dans {filepath} : {exc}") from exc

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ValueError(
            f"Le fichier YAML doit contenir un mapping à la racine : {filepath}"
        )

    return data


def dump_yaml_mapping(filepath: Path, data: dict[str, Any]) -> None:
    """Écrit un mapping dans un fichier YAML (création des parents si besoin)."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(
            data,
            stream,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


def atomic_dump_yaml_mapping(
    filepath: Path,
    data: dict[str, Any],
) -> None:
    """Écrit un mapping YAML par remplacement atomique."""

    filepath.parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None

    try:
        # Le fichier temporaire est créé dans le même répertoire
        # afin de garantir que os.replace utilise le même filesystem.
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{filepath.name}.",
            suffix=".tmp",
            dir=filepath.parent,
        )
        temporary_path = Path(temporary_name)

        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            yaml.safe_dump(
                data,
                stream,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, filepath)

    except Exception:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.warning(
                    "Unable to remove temporary YAML file: %s",
                    temporary_path,
                    exc_info=True,
                )
        raise


class NoDatesSafeLoader(yaml.SafeLoader):
    """SafeLoader qui conserve les dates YAML sous forme de chaînes."""


# Désactive uniquement la résolution automatique des dates.
NoDatesSafeLoader.yaml_implicit_resolvers = {
    key: [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
