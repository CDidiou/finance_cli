import tempfile
from pathlib import Path

from finance_cli.common import yaml_io
from finance_cli.models.asset import Asset


def test_catalog_adapter_loads_valid_asset(asset, asset_repository):
    """Vérifie le chargement d'un actif valide depuis un catalogue temporaire."""

    # Arrange
    assert asset_repository.root.is_relative_to(Path(tempfile.gettempdir()))

    asset_dir = asset_repository.root / "mutual_funds" / "opcvm" / "european_etf"
    asset_dir.mkdir(parents=True, exist_ok=True)

    asset_path = asset_dir / f"{asset.id}.yaml"
    yaml_io.dump_yaml_mapping(
        asset_path,
        asset.model_dump(mode="json"),
    )

    # Act
    result = asset_repository.get_by_id(asset.id)

    # Assert
    assert isinstance(result, Asset)
    assert result.id == asset.id
    assert result.general_info.category == "european_etf"
