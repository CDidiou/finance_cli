"""Modèle représentant une définition du catalogue."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DefinitionInfo:
    """Informations synthétiques sur une définition du catalogue."""

    id: str
    generic_name: str
    label: str
    path: Path
    category: str
