"""Repository for YAML-backed external scraped data."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from finance_cli.common import yaml_io
from finance_cli.exceptions.scraped_data import (
    ScrapedDataContentError,
    ScrapedDataStorageError,
)
from finance_cli.models.scraped_asset import AggregatedScrapedAsset
from finance_cli.validation.schema_validator import SchemaValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScrapedDataWriteResult:
    """Outcome of a scraped data persistence operation."""

    status: Literal["created", "updated", "unchanged"]
    file_path: Path
    last_updated: date
    message: str | None = None


class ScrapedDataRepository:
    """Read, validate and persist scraped asset data."""

    SCHEMA_NAME = "scraped_data.schemas"

    def __init__(
        self,
        resolve_path: Callable[[str, Path], Path],
        schema_validator: SchemaValidator,
        *,
        model: type,
    ) -> None:
        self._resolve_path = resolve_path
        self._schema_validator = schema_validator
        self.model = model

    # --- PUBLIC API ---

    def read_scraped_data(
        self,
        asset_id: str,
        category_path: Path,
    ) -> AggregatedScrapedAsset:
        path = self._resolve_scraped_path(asset_id, category_path)

        try:
            payload = yaml_io.load_yaml_mapping(path)
        except FileNotFoundError as exc:
            raise ScrapedDataContentError(
                f"No scraped data found for '{asset_id}': {path}"
            ) from exc
        except ValueError as exc:
            raise ScrapedDataContentError(
                f"Invalid scraped YAML for '{asset_id}': {path}"
            ) from exc
        except OSError as exc:
            raise ScrapedDataStorageError(
                f"Cannot access scraped data for '{asset_id}': {path}"
            ) from exc

        self._validate_payload(payload, asset_id)
        # last_updated = self._get_last_updated(payload)

        try:
            return self.model.model_validate(payload)
        except ValidationError as exc:
            raise ScrapedDataContentError(
                f"Invalid scraped data model for '{asset_id}'."
            ) from exc

    def write_scraped_data(
        self,
        asset_id: str,
        category_path: Path,
        payload: dict[str, Any],
    ) -> ScrapedDataWriteResult:
        """Write scraped data if valid and strictly newer than existing data."""

        # Validate the incoming payload before touching the existing file.
        self._validate_payload(payload, asset_id)
        new_date = self._get_last_updated(payload)

        path = self._resolve_scraped_path(asset_id, category_path)
        # directory = self._resolve_scraped_path(asset_id, category_path)
        # path = directory / f"{asset_id}_scraping.yaml"

        status: Literal["created", "updated"] = "created"
        try:
            existing_payload = yaml_io.load_yaml_mapping(path)

        except FileNotFoundError:
            # No existing file: creation is allowed.
            logger.info(
                "No existing scraped data for '%s'. Creating it.",
                asset_id,
            )

        except (yaml.YAMLError, TypeError, ValueError) as exc:
            # The existing document is malformed or has an invalid root type.
            # A valid incoming payload is allowed to replace it.
            status = "updated"
            logger.warning(
                "Existing scraped data is unreadable or malformed for '%s'. "
                "Replacement is allowed.",
                asset_id,
                exc_info=exc,
            )

        except OSError as exc:
            # An access failure must never be interpreted as invalid content.
            raise ScrapedDataStorageError(
                f"Cannot access existing scraped data for '{asset_id}': {path}"
            ) from exc

        else:
            status = "updated"
            try:
                self._validate_payload(existing_payload, asset_id)
                existing_date = self._get_last_updated(existing_payload)

            except ScrapedDataContentError as exc:
                # The existing document is invalid according to business
                # rules, schema or date requirements.
                logger.warning(
                    "Existing scraped data is invalid for '%s'. "
                    "Replacement is allowed: %s",
                    asset_id,
                    exc,
                )

            else:
                if new_date <= existing_date:
                    logger.info(
                        "Existing scraped data retained for '%s': "
                        "incoming date (%s) is not newer than existing date (%s).",
                        asset_id,
                        new_date,
                        existing_date,
                    )
                    return ScrapedDataWriteResult(
                        status="unchanged",
                        file_path=path,
                        last_updated=existing_date,
                        message="Existing scraped data retained.",
                    )

        self._atomic_write(path, payload)

        logger.info("Scraped data saved: %s", path)

        return ScrapedDataWriteResult(
            status=status,
            file_path=path,
            last_updated=new_date,
            message=(
                "Scraped data created."
                if status == "created"
                else "Scraped data updated."
            ),
        )

    # --- VALIDATION ---

    def _validate_payload(
        self,
        payload: dict[str, Any],
        asset_id: str,
    ) -> None:
        """Validate payload type, asset identity and JSON Schema."""

        if not isinstance(payload, dict):
            raise ScrapedDataContentError(
                "The scraped document must be a YAML mapping."
            )

        source = payload.get("source")

        if not isinstance(source, dict):
            raise ScrapedDataContentError(
                "The scraped payload does not contain a valid source mapping."
            )

        if source.get("asset_id") != asset_id:
            raise ScrapedDataContentError(
                f"Asset identifier mismatch: expected '{asset_id}', "
                f"received '{source.get('asset_id')}'."
            )

        issues = self._schema_validator.validate(
            value=payload,
            schema_name=self.SCHEMA_NAME,
        )

        if issues:
            details = ", ".join(issues)
            raise ScrapedDataContentError(
                f"Invalid scraped payload for '{asset_id}': {details}"
            )

    # --- HELPERS INTERNES ---

    def _get_last_updated(self, payload: dict[str, Any]) -> date:
        """Return the reference date used to compare scraped data freshness."""

        market_data = payload.get("market_data")

        if not isinstance(market_data, dict):
            raise ScrapedDataContentError("Missing or invalid market_data mapping.")

        value = market_data.get("last_updated")

        if not isinstance(value, str) or not value.strip():
            raise ScrapedDataContentError(
                "Missing or invalid market_data.last_updated."
            )

        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ScrapedDataContentError(
                f"Invalid market_data.last_updated date: {value!r}."
            ) from exc

    def _resolve_scraped_path(
        self,
        asset_id: str,
        category_path: Path,
    ) -> Path:
        return self._resolve_path(asset_id, category_path)

    def _atomic_write(
        self,
        path: Path,
        payload: dict[str, Any],
    ) -> None:
        """Atomically write a validated scraped payload."""

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            yaml_io.atomic_dump_yaml_mapping(path, payload)

        except OSError as exc:
            raise ScrapedDataStorageError(
                f"Cannot write scraped data for '{path}'."
            ) from exc

        except yaml.YAMLError as exc:
            raise ScrapedDataStorageError(
                f"Cannot serialize scraped data for '{path}'."
            ) from exc
