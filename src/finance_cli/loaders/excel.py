"""Loader Excel — lit les données depuis des fichiers .xlsx.

Structure attendue (configurable via ExcelConfig) :
  <output_dir>/
    accounts.xlsx   — colonnes : account_id, user_id, contract_type, broker, label, currency, opened_at
    assets.xlsx     — colonnes : asset_id, account_id, asset_type, isin, label, quantity, unit_price, currency, last_updated
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from finance_cli.config import ExcelConfig
from finance_cli.loaders.base import DataLoader


class ExcelLoader(DataLoader):
    def __init__(self, cfg: ExcelConfig) -> None:
        self.cfg = cfg
        self._accounts_cache: list[dict[str, Any]] | None = None
        self._assets_cache: dict[str, list[dict[str, Any]]] = {}

    # -- Comptes ------------------------------------------------------------

    def load_accounts(self, user_id: str) -> list[dict[str, Any]]:
        all_accounts = self._read_accounts()
        return [a for a in all_accounts if a.get("user_id") == user_id]

    # -- Assets -------------------------------------------------------------

    def load_assets(self, account_id: str) -> list[dict[str, Any]]:
        if account_id not in self._assets_cache:
            self._assets_cache[account_id] = self._read_assets(account_id)
        return self._assets_cache[account_id]

    # -- I/O ----------------------------------------------------------------

    def _read_accounts(self) -> list[dict[str, Any]]:
        if self._accounts_cache is not None:
            return self._accounts_cache

        path = self.cfg.data_dir / "Users" / "DS" / "DS_list_Wallets.xlsx"
        # path = "R:/Finance/Users" / "DS" / "DS_list_Wallets.xlsx"
        self._accounts_cache = _read_excel(path)
        return self._accounts_cache

    def _read_assets(self, account_id: str) -> list[dict[str, Any]]:
        path = self.cfg.output_dir / "assets.xlsx"
        all_assets = _read_excel(path)
        return [a for a in all_assets if a.get("account_id") == account_id]


def _read_excel(path: Path) -> list[dict[str, Any]]:
    """Lit un fichier Excel et retourne une liste de dicts row par row."""
    try:
        import openpyxl  # import tardif — openpyxl est optionnel
    except ImportError as exc:
        raise ImportError(
            "openpyxl est requis pour le loader Excel : poetry add openpyxl"
        ) from exc

    if not path.exists():
        raise FileNotFoundError(f"Fichier Excel introuvable : {path}")

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))  # type: ignore[union-attr]
    if not rows:
        return []

    headers = [
        str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(rows[0])
    ]
    result = []
    for row in rows[1:]:
        record = {h: v for h, v in zip(headers, row) if v is not None}
        if record:
            result.append(record)
    return result
