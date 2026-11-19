from __future__ import annotations
from collections.abc import Sequence
from typing import Any

from finance_cli.exceptions.base import PatrimoniaError


class InCatalogValidationError(PatrimoniaError):
    """Raised when an asset definition fails schema validation."""

    def __init__(
        self,
        id_catalog: str,
        issues: Sequence[Any],
        message: str | None = None,
    ) -> None:
        self.asset_id = id_catalog
        self.issues = list(issues)

        if message is None:
            count = len(self.issues)
            message = (
                f"Validation failed for asset '{id_catalog}' "
                f"({count} issue{'s' if count != 1 else ''})"
            )

        super().__init__(message)

    def __str__(self) -> str:
        lines = [super().__str__()]
        for i, issue in enumerate(self.issues, start=1):
            lines.append(f"  {i}. {issue}")
        return "\n".join(lines)
