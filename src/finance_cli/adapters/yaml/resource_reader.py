"""YAML adapter: list and read definition files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finance_cli.common import yaml_io


class YamlResourceReader:
    """Accès bas niveau aux fiches YAML d'un répertoire."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder

        if not self.folder.is_dir():
            raise OSError(f"Resource directory not found: {self.folder}")

    # --- API PUBLIQUE ---
    def list_files(
        self,
        *,
        recursive: bool = True,
        definitions_only: bool = True,
    ) -> list[Path]:
        """Liste les fichiers YAML du répertoire."""

        pattern = "**/*.yaml" if recursive else "*.yaml"

        files = sorted(
            path
            for path in self.folder.glob(pattern)
            if path.is_file() and not path.name.startswith(".")
        )

        if definitions_only:
            files = [path for path in files if self._is_definition_file(path)]

        return files

    def read(self, filepath: Path) -> dict[str, Any]:
        """Charge un mapping YAML brut, sans héritage."""

        return yaml_io.load_yaml_mapping(filepath)

    @staticmethod
    def _is_definition_file(path: Path) -> bool:
        """Exclut les fichiers techniques et les définitions de type."""

        name = path.name.casefold()
        stem = path.stem.casefold()

        if name.endswith((".rules.yaml", ".schemas.yaml")):
            return False

        if stem == path.parent.name.casefold():
            return False

        return True
