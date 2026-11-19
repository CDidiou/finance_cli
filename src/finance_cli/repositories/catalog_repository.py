"""Repository de lecture des définitions du catalogue."""

from pathlib import Path

from finance_cli.adapters.yaml.resource_reader import YamlResourceReader
from finance_cli.models.definition_info import DefinitionInfo


class CatalogueRepository:
    """Accès aux définitions YAML d'un catalogue."""

    def __init__(self, folder: Path, category: str) -> None:
        self._reader = YamlResourceReader(folder)
        self._category = category

    # --- API PUBLIQUE ---

    def list_definitions(
        self,
        *,
        recursive: bool = True,
    ) -> list[DefinitionInfo]:
        """Retourne les définitions disponibles."""

        files = self._reader.list_files(recursive=recursive)

        return [self._to_definition_info(filepath) for filepath in files]

    # --- HELPERS INTERNES ---

    def _to_definition_info(self, filepath: Path) -> DefinitionInfo:
        relative_id = (
            filepath.relative_to(self._reader.folder).with_suffix("").as_posix()
        )

        data = self._reader.read(filepath)

        entry_id = data.get("id") or filepath.stem
        name = (data.get("general_info") or {}).get("name") or entry_id

        return DefinitionInfo(
            id=str(entry_id),
            generic_name=str(name).strip(),
            label=relative_id,
            path=filepath,
            category=self._category,
        )
