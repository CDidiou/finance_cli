from unittest.mock import patch

import pytest
import yaml

from finance_cli.common import yaml_io
from finance_cli.exceptions.assets import (
    AssetContentError,
    AssetStorageError,
)
from finance_cli.validation.catalog_validation_error import InCatalogValidationError

"""
Tests unitaires de AssetRepository.

Vérifie la traduction des erreurs rencontrées lors des opérations
de lecture et d'écriture du catalogue :
- get_by_id : traduit les erreurs de validation Pydantic en InCatalogValidationError.
- save : traduit les erreurs de sérialisation YAML en AssetContentError.
- get_category_path : traduit les erreurs d'accès au stockage en AssetStorageError.
"""


def test_get_by_id_translates_pydantic_validation_error(
    asset,
    asset_repository,
):
    """
    Vérifie que les erreurs de validation Pydantic rencontrées lors
    de la lecture d'un actif sont traduites en InCatalogValidationError.
    """
    # Arrange
    asset_dir = asset_repository.root / "european_etf"
    asset_dir.mkdir(parents=True, exist_ok=True)

    asset_path = asset_dir / f"{asset.id}.yaml"

    invalid_data = asset.model_dump(mode="json")
    invalid_data["general_info"]["name"] = 123

    yaml_io.dump_yaml_mapping(asset_path, invalid_data)

    # Act / Assert
    with pytest.raises(InCatalogValidationError) as exc_info:
        asset_repository.get_by_id(asset.id)

    assert asset.id in str(exc_info.value)
    assert exc_info.value.issues


def test_save_translates_yaml_serialization_error(
    asset,
    asset_repository,
):
    """
    Vérifie qu'une erreur de sérialisation YAML lors de la sauvegarde
    d'un actif est traduite en AssetContentError.
    """
    # Arrange
    asset_dir = asset_repository.root / "european_etf"
    asset_dir.mkdir(parents=True, exist_ok=True)

    asset_path = asset_dir / f"{asset.id}.yaml"
    yaml_io.dump_yaml_mapping(
        asset_path,
        asset.model_dump(mode="json"),
    )

    # Act / Assert
    with patch(
        "finance_cli.repositories.asset_repository.yaml_io.dump_yaml_mapping",
        side_effect=yaml.YAMLError("Serialization error"),
    ):
        with pytest.raises(AssetContentError, match="sérialiser"):
            asset_repository.save(asset)


def test_get_category_path_translates_os_error(asset_repository):
    """
    Vérifie qu'une erreur système lors de la recherche du chemin
    d'une catégorie est traduite en AssetStorageError.
    """
    with patch.object(
        asset_repository,
        "_find_implementation",
        side_effect=OSError("Permission denied"),
    ):
        with pytest.raises(
            AssetStorageError,
            match="Impossible d'accéder au chemin",
        ):
            asset_repository.get_category_path("IE000BI8OT95")
