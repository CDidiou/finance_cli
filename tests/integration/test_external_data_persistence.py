from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from finance_cli.common import yaml_io
from finance_cli.models.scraped_asset import AggregatedScrapedAsset
from finance_cli.repositories.scraped_data_repository import (
    ScrapedDataContentError,
    ScrapedDataRepository,
    ScrapedDataStorageError,
)


def test_external_data_adapter_write_and_read(
    tmp_path,
    scraped_asset,
):
    # Arrange
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    adapter = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )

    asset_id = scraped_asset.source.asset_id
    category_path = Path("european_etf")
    payload = scraped_asset.model_dump(mode="json")

    # Act : écriture
    write_result = adapter.write_scraped_data(
        asset_id=asset_id,
        category_path=category_path,
        payload=payload,
    )

    # Assert : chemin et existence
    expected_path = (
        tmp_path
        / "external-data"
        / "assets"
        / category_path
        / asset_id
        / "scraped_data"
    )

    # print("Write result:", write_result)
    # print("File path:", write_result.file_path)
    # print("Exists:", write_result.file_path.exists())
    # print(
    #     "Files:",
    #     list(expected_path.rglob("*"))
    #     if expected_path.exists()
    #     else "Directory missing",
    # )
    assert write_result.file_path.parent == expected_path
    assert write_result.file_path.parent.is_dir()

    expected_file = expected_path / f"{asset_id}_scraping.yaml"
    assert expected_file.is_file()

    # Act : relecture
    loaded_payload = adapter.read_scraped_data(
        asset_id=asset_id,
        category_path=category_path,
    )

    # Assert : contenu
    assert loaded_payload.model_dump(mode="json") == payload

    schema_validator.validate.assert_called_with(
        value=payload,
        schema_name="scraped_data.schemas",
    )
    assert schema_validator.validate.call_count == 2


def test_scraped_repository_keeps_existing_data_if_new_data_is_older(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )

    asset_id = scraped_asset.source.asset_id
    category_path = Path("european_etf")

    existing_payload = scraped_asset.model_dump(mode="json")
    repository.write_scraped_data(
        asset_id,
        category_path,
        existing_payload,
    )

    older_payload = deepcopy(existing_payload)
    older_payload["market_data"]["last_updated"] = "2026-11-13"

    repository.write_scraped_data(
        asset_id,
        category_path,
        older_payload,
    )

    result = repository.read_scraped_data(asset_id, category_path)

    assert result.model_dump(mode="json") == existing_payload
    assert result.market_data.last_updated.isoformat() == "2026-11-14"


def test_scraped_repository_replaces_existing_data_if_new_data_is_newer(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )

    asset_id = scraped_asset.source.asset_id
    category_path = Path("european_etf")

    existing_payload = scraped_asset.model_dump(mode="json")
    repository.write_scraped_data(
        asset_id,
        category_path,
        existing_payload,
    )

    newer_payload = deepcopy(existing_payload)
    newer_payload["market_data"]["last_updated"] = "2026-11-15"

    repository.write_scraped_data(
        asset_id,
        category_path,
        newer_payload,
    )

    result = repository.read_scraped_data(asset_id, category_path)

    assert result.model_dump(mode="json") == newer_payload


def test_scraped_repository_keeps_existing_data_if_new_data_is_invalid(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )

    asset_id = scraped_asset.source.asset_id
    category_path = Path("european_etf")

    existing_payload = scraped_asset.model_dump(mode="json")
    repository.write_scraped_data(
        asset_id,
        category_path,
        existing_payload,
    )

    invalid_payload = deepcopy(existing_payload)
    invalid_payload["market_data"]["last_updated"] = "2026-11-16"

    schema_validator.validate.return_value = ["Erreur de validation"]

    with pytest.raises(
        ScrapedDataContentError,
        match="Invalid scraped payload",
    ):
        repository.write_scraped_data(
            asset_id,
            category_path,
            invalid_payload,
        )

    path = repository._resolve_scraped_path(asset_id, category_path)
    result = yaml_io.load_yaml_mapping(path)

    assert result == existing_payload


def test_read_scraped_data_raises_when_file_is_missing(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )

    with pytest.raises(ScrapedDataContentError, match="No scraped data found"):
        repository.read_scraped_data(
            scraped_asset.source.asset_id,
            Path("european_etf"),
        )


def test_write_scraped_data_raises_on_permission_error(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )
    payload = scraped_asset.model_dump(mode="json")

    with patch(
        "finance_cli.repositories.scraped_data_repository.yaml_io.load_yaml_mapping",
        side_effect=PermissionError("Access denied"),
    ):
        with pytest.raises(ScrapedDataStorageError):
            repository.write_scraped_data(
                payload["source"]["asset_id"],
                Path("european_etf"),
                payload,
            )


def test_write_scraped_data_replaces_malformed_existing_file(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )
    payload = scraped_asset.model_dump(mode="json")

    path = repository._resolve_scraped_path(
        payload["source"]["asset_id"],
        Path("european_etf"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("invalid: [yaml", encoding="utf-8")

    repository.write_scraped_data(
        payload["source"]["asset_id"],
        Path("european_etf"),
        payload,
    )

    assert yaml_io.load_yaml_mapping(path) == payload


def test_write_scraped_data_raises_on_atomic_write_error(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )
    payload = scraped_asset.model_dump(mode="json")

    with (
        patch(
            "finance_cli.repositories.scraped_data_repository.yaml_io.load_yaml_mapping",
            side_effect=FileNotFoundError,
        ),
        patch(
            "finance_cli.repositories.scraped_data_repository.yaml_io.atomic_dump_yaml_mapping",
            side_effect=OSError("Disk full"),
        ),
    ):
        with pytest.raises(ScrapedDataStorageError, match="Cannot write scraped data"):
            repository.write_scraped_data(
                payload["source"]["asset_id"],
                Path("european_etf"),
                payload,
            )


def test_write_scraped_data_keeps_existing_data_when_dates_are_equal(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )
    payload = scraped_asset.model_dump(mode="json")

    repository.write_scraped_data(
        payload["source"]["asset_id"],
        Path("european_etf"),
        payload,
    )

    updated_payload = deepcopy(payload)
    updated_payload["market_data"]["indicative"]["price"] = 999.99

    repository.write_scraped_data(
        payload["source"]["asset_id"],
        Path("european_etf"),
        updated_payload,
    )

    path = repository._resolve_scraped_path(
        payload["source"]["asset_id"],
        Path("european_etf"),
    )

    assert yaml_io.load_yaml_mapping(path) == payload


def test_write_scraped_data_rejects_invalid_last_updated(
    tmp_path,
    scraped_asset,
):
    schema_validator = Mock()
    schema_validator.validate.return_value = []

    def resolve_path(asset_id: str, category_path: Path) -> Path:
        return (
            tmp_path
            / "external-data"
            / "assets"
            / category_path
            / asset_id
            / "scraped_data"
            / f"{asset_id}_scraping.yaml"
        )

    repository = ScrapedDataRepository(
        resolve_path=resolve_path,
        schema_validator=schema_validator,
        model=AggregatedScrapedAsset,
    )
    payload = scraped_asset.model_dump(mode="json")
    payload["market_data"]["last_updated"] = "invalid-date"

    with patch(
        "finance_cli.repositories.scraped_data_repository.yaml_io.load_yaml_mapping"
    ) as mock_load:
        with pytest.raises(
            ScrapedDataContentError,
            match="Invalid market_data.last_updated date",
        ):
            repository.write_scraped_data(
                payload["source"]["asset_id"],
                Path("european_etf"),
                payload,
            )

    mock_load.assert_not_called()
