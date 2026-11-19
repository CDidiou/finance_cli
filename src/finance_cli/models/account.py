"""Domain model for an account already loaded from the contract catalogue."""

from typing import Any

from pydantic import BaseModel, HttpUrl


class GeneralInfo(BaseModel):
    name: str
    category: str
    broker: str
    cash_asset: str


class Sources(BaseModel):
    contract: HttpUrl
    broker: HttpUrl


class Account(BaseModel):
    """Represent an asset loaded from its validated catalogue definition.

    YAML loading, inheritance resolution and schema validation
    belong to the catalogue adapter.
    """

    id: str
    general_info: GeneralInfo
    sources: Sources

    @property
    def name(self) -> str:
        return self.general_info.name

    @property
    def category(self) -> str:
        return self.general_info.category

    def sections(self, *names: str) -> dict[str, Any]:
        if not names:
            names = (
                "general_info",
                "sources",
            )
        data = self.model_dump()
        return {name: data[name] for name in names if name in data}

    def __repr__(self) -> str:
        return f"Account(id={self.id!r})"
