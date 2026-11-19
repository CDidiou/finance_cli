"""Composition des dépendances de l'application."""

from pathlib import Path

from finance_cli.adapters.web.yahoo_finance import YahooFinanceAdapter
from finance_cli.bootstrap.services import Services
from finance_cli.config.config_models import AppConfig
from finance_cli.config.paths_resolver import ConfigPathResolver
from finance_cli.exceptions.configuration import ConfigurationError
from finance_cli.models.asset import Asset
from finance_cli.models.scraped_asset import AggregatedScrapedAsset
from finance_cli.repositories.asset_repository import AssetRepository
from finance_cli.repositories.catalog_repository import CatalogueRepository
from finance_cli.repositories.external_asset_repository import ExternalAssetRepository
from finance_cli.repositories.scraped_data_repository import ScrapedDataRepository
from finance_cli.services.assets.asset_service import AssetService
from finance_cli.services.assets.status_service import AssetStatusService
from finance_cli.services.catalog.catalog_service import CatalogueListService
from finance_cli.services.catalog.list_service import ListService
from finance_cli.services.config_check_service import ConfigCheckService
from finance_cli.validation.reference_validator import ReferenceValidator
from finance_cli.validation.schema_loader import SchemaLoader
from finance_cli.validation.schema_validator import SchemaValidator


def build_services(config: AppConfig) -> Services:
    """Construit l'ensemble des services de l'application."""
    path_resolver = ConfigPathResolver(config)
    reference_validator = build_reference_validator(path_resolver)
    common_schemas_dir = (config.base_dir / config.data.common.schemas).resolve()

    asset_repository = build_asset_repository(
        common_schemas_dir=common_schemas_dir,
        path_resolver=path_resolver,
        reference_validator=reference_validator,
    )
    scraped_asset_repository = build_scraped_asset_repository(
        common_schemas_dir=common_schemas_dir,
        path_resolver=path_resolver,
        reference_validator=reference_validator,
    )
    external_asset_repository = ExternalAssetRepository(
        path_resolver=path_resolver,
    )

    config_check_service = ConfigCheckService(config)
    list_service = build_list_service(path_resolver)

    asset_service = build_asset_service(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_asset_repository,
    )

    asset_status_service = AssetStatusService(
        asset_repository=asset_repository,
        external_asset_repository=external_asset_repository,
    )

    return Services(
        config_check_service=config_check_service,
        list_service=list_service,
        asset_service=asset_service,
        asset_status_service=asset_status_service,
    )


def build_list_service(
    path_resolver: ConfigPathResolver,
) -> ListService:
    # Résolution des ressources nécessaires au service de listes.
    assets_resources = path_resolver.resolve_resources("catalog/financial/assets")
    contracts_resources = path_resolver.resolve_resources("catalog/financial/contracts")
    users_resources = path_resolver.resolve_resources("customer/input/users")

    assets_repository = CatalogueRepository(
        assets_resources.folder,
        "assets",
    )
    accounts_repository = CatalogueRepository(
        contracts_resources.folder,
        "accounts",
    )
    users_repository = CatalogueRepository(
        users_resources.folder,
        "users",
    )

    return ListService(
        assets_service=CatalogueListService(assets_repository),
        accounts_service=CatalogueListService(accounts_repository),
        users_service=CatalogueListService(users_repository),
    )


def build_asset_service(
    asset_repository: AssetRepository,
    scraped_data_repository: ScrapedDataRepository,
) -> AssetService:
    """Construit AssetService avec toutes ses dépendances."""
    yahoo_adapter = YahooFinanceAdapter()

    return AssetService(
        asset_repository=asset_repository,
        scraped_data_repository=scraped_data_repository,
        yahoo_adapter=yahoo_adapter,
    )


def build_asset_repository(
    common_schemas_dir: Path,
    path_resolver: ConfigPathResolver,
    reference_validator: ReferenceValidator,
) -> AssetRepository:
    """Construit le repository du catalogue des actifs."""
    asset_resources = path_resolver.resolve_resources("catalog/financial/assets")
    if asset_resources.schemas is None:
        raise ConfigurationError(
            "Le répertoire des schémas du catalogue des actifs n'est pas configuré."
        )

    reference_validator = build_reference_validator(path_resolver)
    schema_loader = SchemaLoader(
        schemas_dir=asset_resources.schemas,
        common_schemas_dir=common_schemas_dir,
    )

    schema_validator = SchemaValidator(
        schema_loader=schema_loader,
        reference_validator=reference_validator,
    )

    return AssetRepository(
        folder=asset_resources.folder,
        rules_dir=asset_resources.rules,
        schema_validator=schema_validator,
        model=Asset,
    )


def build_scraped_asset_repository(
    common_schemas_dir: Path,
    path_resolver: ConfigPathResolver,
    reference_validator: ReferenceValidator,
) -> ScrapedDataRepository:
    scraped_resources = path_resolver.resolve_resources("external/assets/scraped_data")
    if scraped_resources.schemas is None:
        raise ConfigurationError(
            "Le répertoire des schémas du catalogue des scraped actifs n'est pas configuré."
        )

    reference_validator = build_reference_validator(path_resolver)
    scraped_schema_loader = SchemaLoader(
        schemas_dir=scraped_resources.schemas,
        common_schemas_dir=common_schemas_dir,
    )

    scraped_schema_validator = SchemaValidator(
        schema_loader=scraped_schema_loader,
        reference_validator=reference_validator,
    )

    def resolve_scraped_data_path(
        asset_id: str,
        category_path: Path,
    ) -> Path:
        return path_resolver.resolve_file_path(
            "external/assets/scraped_data",
            context={
                "ID_ASSET": asset_id,
                "CATEGORY_PATH": str(category_path),
            },
        )

    return ScrapedDataRepository(
        resolve_path=resolve_scraped_data_path,
        schema_validator=scraped_schema_validator,
        model=AggregatedScrapedAsset,
    )


def build_reference_validator(
    path_resolver: ConfigPathResolver,
) -> ReferenceValidator:
    """Construit le validateur des références métier."""
    economy_resources = path_resolver.resolve_resources("catalog/references/economy")

    return ReferenceValidator(
        references_dir=economy_resources.folder,
    )
