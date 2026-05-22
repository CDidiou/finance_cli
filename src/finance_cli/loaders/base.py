"""Interface abstraite pour les loaders de données."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DataLoader(ABC):
    """Charge les données brutes (accounts + assets) d'un utilisateur.

    Les données retournées sont des dicts bruts — la validation
    Pydantic + schéma JSON se fait en aval dans le service.
    """

    @abstractmethod
    def load_accounts(self, user_id: str) -> list[dict[str, Any]]:
        """Retourne la liste des accounts bruts pour un user."""
        ...

    @abstractmethod
    def load_assets(self, account_id: str) -> list[dict[str, Any]]:
        """Retourne la liste des assets bruts pour un account."""
        ...
