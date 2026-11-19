from __future__ import annotations

from copy import deepcopy
from typing import Any

from finance_cli.models import scraped_asset


def is_present(value: Any) -> bool:
    """Indique si une valeur peut être reportée dans le catalogue."""

    if value is None:
        return False

    if isinstance(value, str) and not value.strip():
        return False

    if isinstance(value, (dict, list)) and len(value) == 0:
        return False

    return True


def split_amount(value: float | None) -> tuple[float | None, str | None]:
    """Convertit un montant en millions ou milliards."""

    if value is None:
        return None, None

    if abs(value) >= 1_000_000_000:
        return value / 1_000_000_000, "B"

    return value / 1_000_000, "M"


def apply_external_to_catalog(
    external: scraped_asset.AggregatedScrapedAsset | dict,
    catalog: dict,
) -> dict:

    if isinstance(external, scraped_asset.AggregatedScrapedAsset):
        external = external.model_dump(mode="json")

    result = deepcopy(catalog)

    ext_md = external.get("market_data") or {}
    ext_indicative = ext_md.get("indicative") or {}

    if not is_present(ext_indicative):
        return result

    if is_present(ext_md.get("last_updated")):
        result.setdefault("market_data", {})["last_updated"] = ext_md["last_updated"]

    cat_indicative = result.setdefault("market_data", {}).setdefault("indicative", {})

    for key in ("price", "nav", "currency", "as_of"):
        value = ext_indicative.get(key)
        if is_present(value):
            cat_indicative[key] = value

    aum = ext_indicative.get("aum")
    if is_present(aum):
        value, unit = split_amount(aum)
        cat_indicative["aum"] = value
        cat_indicative["aum_unit"] = unit

    market_cap = ext_indicative.get("market_cap")
    if is_present(market_cap):
        value, unit = split_amount(market_cap)
        cat_indicative["market_cap"] = value
        cat_indicative["mc_unit"] = unit

    return result
