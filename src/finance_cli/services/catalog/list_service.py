"""Façade des opérations de listing."""

from finance_cli.models.definition_info import DefinitionInfo
from finance_cli.services.catalog.catalog_service import (
    CatalogueListService,
)


class ListService:
    def __init__(
        self,
        *,
        assets_service: CatalogueListService,
        accounts_service: CatalogueListService,
        users_service: CatalogueListService,
    ) -> None:
        self._assets = assets_service
        self._accounts = accounts_service
        self._users = users_service

    def list_assets(self) -> list[DefinitionInfo]:
        return self._assets.list()

    def list_accounts(self) -> list[DefinitionInfo]:
        return self._accounts.list()

    def list_users(self) -> list[DefinitionInfo]:
        return self._users.list(recursive=False)
