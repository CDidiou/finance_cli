from typing import Any

from finance_cli.repositories.asset_repository import AssetRepository
from finance_cli.repositories.external_asset_repository import ExternalAssetRepository


class AssetStatusService:
    def __init__(
        self,
        asset_repository: AssetRepository,
        external_asset_repository: ExternalAssetRepository,
    ) -> None:
        self.asset_repository = asset_repository
        self.external_asset_repository = external_asset_repository

    def get_status(self, asset_id: str) -> dict[str:Any]:
        asset = self.asset_repository.get_by_id(asset_id)

        category_path = self.asset_repository.get_category_path(asset_id)

        return self.external_asset_repository.inspect_asset(
            asset_id=asset.id,
            category_path=category_path,
        )
