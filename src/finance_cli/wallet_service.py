"""Service de chargement du wallet d'un utilisateur.

Orchestre : loader → validation schéma → modèles Pydantic → Wallet.
"""

from __future__ import annotations

import logging

from finance_cli.loaders.base import DataLoader
from finance_cli.models import Account, Asset, Wallet
from finance_cli.schemas import SchemaRegistry, registry as default_registry

log = logging.getLogger(__name__)


class WalletService:
    def __init__(
        self,
        loader: DataLoader,
        schema_registry: SchemaRegistry = default_registry,
    ) -> None:
        self.loader = loader
        self.registry = schema_registry

    def load(self, user_id: str) -> Wallet:
        """Charge et retourne le wallet complet d'un utilisateur."""
        log.info("Chargement du wallet pour user=%s", user_id)

        raw_accounts = self.loader.load_accounts(user_id)
        log.debug("  %d compte(s) trouvé(s)", len(raw_accounts))

        if not raw_accounts:
            log.warning("Aucun compte trouvé pour user=%s", user_id)
            return Wallet(user_id=user_id)

        # Validation schéma JSON + construction Pydantic
        accounts: list[Account] = []
        for raw_acc in raw_accounts:
            self.registry.validate(raw_acc, "account.schema.json")
            account = Account.model_validate(raw_acc)

            # Assets de ce compte
            raw_assets = self.loader.load_assets(account.account_id)
            log.debug(
                "    compte %s → %d asset(s)", account.account_id, len(raw_assets)
            )

            self.registry.validate_many(raw_assets, "asset.schema.json")
            account.assets = [Asset.model_validate(a) for a in raw_assets]

            accounts.append(account)

        wallet = Wallet(user_id=user_id, accounts=accounts)
        log.info(
            "Wallet chargé : %d compte(s), %d asset(s), valeur totale %.2f",
            wallet.account_count,
            wallet.asset_count,
            wallet.total_value,
        )
        return wallet
