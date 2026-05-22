# -*- coding: utf-8 -*-
"""Modèles du domaine : Asset, Account, Wallet."""

from __future__ import annotations

import logging
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, computed_field


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------

AssetType = Literal["share", "opcvm", "etf"]


class Asset(BaseModel):
    asset_id: str
    account_id: str
    asset_type: AssetType
    isin: str
    label: str
    quantity: float = Field(ge=0)
    unit_price: float = Field(ge=0)
    currency: str = "EUR"
    last_updated: date | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def market_value(self) -> float:
        """Valorisation = quantité × prix unitaire."""
        return round(self.quantity * self.unit_price, 2)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

ContractType = Literal["PEA", "CTO", "PEA-PME", "AV", "PER"]


class Account(BaseModel):
    account_id: str
    user_id: str
    contract_type: ContractType
    broker: str
    label: str = ""
    currency: str = "EUR"
    opened_at: date | None = None
    assets: list[Asset] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_value(self) -> float:
        """Valorisation totale du compte."""
        return round(sum(a.market_value for a in self.assets), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def asset_count(self) -> int:
        return len(self.assets)

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------


class Wallet(BaseModel):
    user_id: str
    accounts: list[Account] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_value(self) -> float:
        """Valorisation totale du wallet."""
        return round(sum(a.total_value for a in self.accounts), 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def account_count(self) -> int:
        return len(self.accounts)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def asset_count(self) -> int:
        return sum(a.asset_count for a in self.accounts)

    def summary(self) -> str:
        lines = [
            f"Wallet  — user : {self.user_id}",
            f"  {self.account_count} compte(s)  |  "
            f"{self.asset_count} asset(s)  |  "
            f"valorisation : {self.total_value:,.2f} {self.accounts[0].currency if self.accounts else 'EUR'}",
        ]
        for acc in self.accounts:
            lines.append(
                f"  ├─ [{acc.contract_type}] {acc.broker}"
                f"{f' — {acc.label}' if acc.label else ''}"
                f"  →  {acc.total_value:,.2f} {acc.currency}"
                f"  ({acc.asset_count} assets)"
            )
            for asset in acc.assets:
                lines.append(
                    f"  │    • {asset.label:<30} {asset.asset_type:<6} "
                    f"{asset.quantity:>10.4f} × {asset.unit_price:>10.4f} "
                    f"= {asset.market_value:>12,.2f} {asset.currency}"
                )
        return "\n".join(lines)

    model_config = {"extra": "forbid"}
