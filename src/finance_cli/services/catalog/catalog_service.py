"""Service applicatif de listing du catalogue."""

from finance_cli.models.definition_info import DefinitionInfo
from finance_cli.repositories.catalog_repository import CatalogueRepository


class CatalogueListService:
    """Service de listing des définitions du catalogue."""

    def __init__(self, repository: CatalogueRepository) -> None:
        self._repository = repository

    def list(
        self,
        *,
        recursive: bool = True,
    ) -> list[DefinitionInfo]:
        return self._repository.list_definitions(
            recursive=recursive,
        )
