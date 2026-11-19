"""Application services container."""

from dataclasses import dataclass

from finance_cli.services.config_check_service import ConfigCheckService
from finance_cli.services.assets.asset_service import AssetService
from finance_cli.services.assets.status_service import AssetStatusService
from finance_cli.services.catalog.list_service import ListService


@dataclass
class Services:
    """Services available to CLI commands."""

    config_check_service: ConfigCheckService
    asset_service: AssetService
    asset_status_service: AssetStatusService
    list_service: ListService
