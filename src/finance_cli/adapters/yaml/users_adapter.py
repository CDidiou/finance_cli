"""YAML-backed access to the account contract catalogue."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finance_cli.adapters.yaml import inheritance_loader, yaml_io
from finance_cli.config import paths_resolver
from old.src.finance_cli.models.user import User


class UserCatalog:
    """Resolve and load user definitions from the configured YAML catalogue."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
    ) -> None:
        path_resolver = paths_resolver.ConfigPathResolver(config)
        self.root = path_resolver.resolve_directory(
            entity="users",
            io_type="inputs",
            name="portfolio",
            path_type="data",
        )

    # --- API PUBLIQUE ---

    def get_by_id(self, user_id: str) -> User:
        """Find and load an user by identifier."""
        implementation_file = self._find_implementation(user_id)
        data, schema = self._load(implementation_file)
        return User(user_id, data, schema)

    def list_files(self) -> list[Path]:
        """Liste tous les fichiers d'actifs valides du catalogue, triés."""
        if not self.root or not self.root.exists():
            return []

        pattern = "**/*.yaml"
        files = sorted(
            path
            for path in self.root.glob(pattern)
            if path.is_file() and not path.name.startswith(".")
        )

        # Filtrage similaire à _is_definition_file de YamlResourceReader
        filtered_files = []
        for path in files:
            name = path.name.casefold()
            stem = path.stem.casefold()

            # Exclusions standard
            if name.endswith(".rules.yaml") or name.endswith(".schemas.yaml"):
                continue
            # Exclusion de la définition de type elle-même (ex: .../stock/stock.yaml)
            if stem == path.parent.name.casefold():
                continue

            filtered_files.append(path)

        return filtered_files

    # --- HELPERS INTERNES (Privés, cachés aux autres modules) ---

    def _find_implementation(
        self,
        implementations_dir: Path,
        account_id: str,
    ) -> list[Path]:
        if not implementations_dir.is_dir():
            return []

        matches: list[Path] = []
        for path in sorted(implementations_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
                continue
            resolved = path.resolve()
            if not self._is_within_root(resolved):
                continue
            data = yaml_io.load_yaml_mapping(resolved)
            implementation_id = data.get("id")
            if isinstance(implementation_id, str):
                if implementation_id.strip() == account_id:
                    matches.append(resolved)
        return matches

    def _load(self, implementation_file: Path) -> dict[str, Any]:
        """Load cumulative asset data through its YAML ``extends`` chain."""
        return inheritance_loader.load_data_with_extends(
            implementation_file, root=self.root
        )

    def _is_within_root(self, path: Path) -> bool:
        try:
            path.relative_to(self.root.resolve())
        except ValueError:
            return False
        return True
