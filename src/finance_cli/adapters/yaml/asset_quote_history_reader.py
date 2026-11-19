"""Read raw YAML quote-history documents from the archive."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finance_cli.common import yaml_io
import yaml


class QuoteHistoryReadError(Exception):
    """Raised when a quote-history file cannot be read or parsed."""


class AssetQuoteHistoryReader:
    """Read quote-history YAML documents without applying business rules."""

    def read(self, filepath: Path) -> Any:
        """Return the raw YAML value stored in a history file."""
        return yaml_io.load_yaml_mapping(filepath)
