from __future__ import annotations

from pathlib import Path
from typing import Any

from finance_cli.common import inheritance


class RuleLoaderError(Exception):
    pass


class RuleLoader:
    """Charge et fusionne les règles métier avec support de extends."""

    def __init__(self, rules_dir: Path) -> None:
        self.rules_dir = rules_dir.resolve()
        if not self.rules_dir.is_dir():
            raise RuleLoaderError(f"Dossier de règles introuvable : {self.rules_dir}")

    # --- API PUBLIQUE ---
    def load(self, rule_name: str) -> list[dict[str, Any]]:
        path = self._resolve_path(rule_name)
        data = inheritance.load_data_with_extends(path, root=self.rules_dir)

        raw_rules = data.get("rules") or []
        if not isinstance(raw_rules, list):
            raise RuleLoaderError(f"'rules' doit être une liste dans {path}")

        return self._merge_rules_by_id(raw_rules)

    # --- HELPERS INTERNES ---
    def _resolve_path(self, rule_name: str) -> Path:
        name = rule_name
        if not name.endswith(".yaml"):
            if not name.endswith(".rules"):
                name = f"{name}.rules"
            name = f"{name}.yaml"

        path = self.rules_dir / name
        if path.exists():
            return path

        # recherche récursive si organisation en sous-dossiers
        candidates = list(self.rules_dir.rglob(name))
        if not candidates:
            raise RuleLoaderError(f"Fichier de règles introuvable : {name}")
        return candidates[0]

    def _merge_rules_by_id(self, rules: list[Any]) -> list[dict[str, Any]]:
        by_id: dict[str, dict[str, Any]] = {}
        order: list[str] = []

        for rule in rules:
            if not isinstance(rule, dict):
                raise RuleLoaderError(f"Chaque règle doit être un mapping : {rule!r}")

            rule_id = rule.get("id")
            if not isinstance(rule_id, str) or not rule_id.strip():
                raise RuleLoaderError(
                    f"Chaque règle doit avoir un id non vide : {rule!r}"
                )

            if rule_id not in by_id:
                order.append(rule_id)
            by_id[rule_id] = rule  # le plus spécifique écrase

        return [by_id[i] for i in order]
