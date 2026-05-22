"""Loader SQL — lit les données via SQLAlchemy.

Requiert : poetry add sqlalchemy
"""

from __future__ import annotations

from typing import Any

from finance_cli.config import SqlConfig
from finance_cli.loaders.base import DataLoader


class SqlLoader(DataLoader):
    def __init__(self, cfg: SqlConfig) -> None:
        self.cfg = cfg
        self._engine: Any = None  # sqlalchemy.Engine

    @property
    def engine(self) -> Any:
        if self._engine is None:
            try:
                from sqlalchemy import create_engine
            except ImportError as exc:
                raise ImportError(
                    "sqlalchemy est requis pour le loader SQL : poetry add sqlalchemy"
                ) from exc
            self._engine = create_engine(self.cfg.dsn)
        return self._engine

    def load_accounts(self, user_id: str) -> list[dict[str, Any]]:
        query = f"""
            SELECT account_id, user_id, contract_type, broker,
                   label, currency, opened_at
            FROM {self.cfg.schema_name}.accounts
            WHERE user_id = :user_id
        """
        return self._fetch(query, {"user_id": user_id})

    def load_assets(self, account_id: str) -> list[dict[str, Any]]:
        query = f"""
            SELECT asset_id, account_id, asset_type, isin, label,
                   quantity, unit_price, currency, last_updated
            FROM {self.cfg.schema_name}.assets
            WHERE account_id = :account_id
        """
        return self._fetch(query, {"account_id": account_id})

    def _fetch(self, query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        from sqlalchemy import text

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            cols = list(result.keys())
            return [dict(zip(cols, row)) for row in result.fetchall()]
