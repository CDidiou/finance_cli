# finance_cli/validation/rule_validator.py
"""Évaluation des règles métier définies dans les fichiers *.rules.yaml."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


class RuleValidator:
    """Évalue une liste de règles métier contre un document de données."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate(
        self,
        data: dict[str, Any],
        rules: list[dict[str, Any]],
    ) -> list[str]:
        issues: list[str] = []
        for rule in rules:
            rule_type = rule.get("type")
            handler = self._handlers.get(rule_type)
            if handler is None:
                issues.append(
                    f"{rule.get('id', '?')}: type de règle inconnu '{rule_type}'"
                )
                continue
            issues.extend(handler(self, data, rule))
        return issues

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _check_sum_equals(
        self, data: dict[str, Any], rule: dict[str, Any]
    ) -> list[str]:
        root = self._get_by_path(data, rule["path"])
        if not isinstance(root, dict):
            return [self._msg(rule, "chemin introuvable ou invalide")]

        total = 0.0
        for field in rule.get("fields", []):
            section = root.get(field, {})
            if isinstance(section, dict):
                total += sum(float(v) for v in section.values())
            elif section is not None:
                total += float(section)

        expected = float(rule.get("value", 100))
        tolerance = float(rule.get("tolerance", 0.01))

        if abs(total - expected) > tolerance:
            return [
                self._msg(
                    rule,
                    f"obtenu={total}, attendu={expected} (±{tolerance})",
                )
            ]
        return []

    def _check_required(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        value = self._get_by_path(data, rule["path"])
        if value is None or (isinstance(value, str) and not value.strip()):
            return [self._msg(rule, "champ obligatoire manquant ou vide")]
        return []

    def _check_gt(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        return self._compare(data, rule, op=">")

    def _check_gte(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        return self._compare(data, rule, op=">=")

    def _check_lt(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        return self._compare(data, rule, op="<")

    def _check_lte(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        return self._compare(data, rule, op="<=")

    def _check_min_items(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        value = self._get_by_path(data, rule["path"])
        min_count = int(rule.get("value", 1))
        if not isinstance(value, list) or len(value) < min_count:
            actual = len(value) if isinstance(value, list) else 0
            return [
                self._msg(
                    rule,
                    f"attendu au moins {min_count} élément(s), obtenu={actual}",
                )
            ]
        return []

    def _check_in(self, data: dict[str, Any], rule: dict[str, Any]) -> list[str]:
        value = self._get_by_path(data, rule["path"])
        allowed = rule.get("values") or []
        if value is None:
            return [self._msg(rule, "valeur absente")]
        if value not in allowed:
            return [
                self._msg(
                    rule,
                    f"valeur '{value}' hors ensemble autorisé {allowed}",
                )
            ]
        return []

    def _check_date_before_today(
        self, data: dict[str, Any], rule: dict[str, Any]
    ) -> list[str]:
        value = self._get_by_path(data, rule["path"])
        if value is None:
            return [self._msg(rule, "date absente")]

        try:
            if isinstance(value, date) and not isinstance(value, datetime):
                d = value
            else:
                d = date.fromisoformat(str(value)[:10])
        except ValueError:
            return [self._msg(rule, f"date invalide : {value!r}")]

        if d >= date.today():
            return [self._msg(rule, f"la date {d} doit être dans le passé")]
        return []

    def _check_required_with(
        self, data: dict[str, Any], rule: dict[str, Any]
    ) -> list[str]:
        root = self._get_by_path(data, rule["path"])
        if not isinstance(root, dict):
            return []

        if_field = rule.get("if_field")
        if not if_field or not root.get(if_field):
            return []

        missing = [f for f in rule.get("required_fields", []) if not root.get(f)]
        if missing:
            return [
                self._msg(
                    rule,
                    (
                        f"si '{if_field}' est présent, champs obligatoires "
                        f"manquants : {missing}"
                    ),
                )
            ]
        return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compare(
        self,
        data: dict[str, Any],
        rule: dict[str, Any],
        *,
        op: str,
    ) -> list[str]:
        value = self._get_by_path(data, rule["path"])
        if value is None:
            return [self._msg(rule, "valeur absente")]

        try:
            actual = float(value)
            expected = float(rule["value"])
        except (TypeError, ValueError):
            return [self._msg(rule, f"valeur non numérique : {value!r}")]

        ok = {
            ">": actual > expected,
            ">=": actual >= expected,
            "<": actual < expected,
            "<=": actual <= expected,
        }[op]

        if not ok:
            return [self._msg(rule, f"obtenu={actual}, attendu {op} {expected}")]
        return []

    @staticmethod
    def _get_by_path(data: dict[str, Any], path: str) -> Any:
        node: Any = data
        for part in path.split("."):
            if not isinstance(node, dict):
                return None
            node = node.get(part)
        return node

    @staticmethod
    def _msg(rule: dict[str, Any], detail: str) -> str:
        rule_id = rule.get("id", "?")
        description = rule.get("description")
        prefix = f"{rule_id}: {description}" if description else rule_id
        return f"{prefix} ({detail})"

    # Dispatch
    _handlers = {
        "sum_equals": _check_sum_equals,
        "required": _check_required,
        "gt": _check_gt,
        "gte": _check_gte,
        "lt": _check_lt,
        "lte": _check_lte,
        "min_items": _check_min_items,
        "in": _check_in,
        "date_before_today": _check_date_before_today,
        "required_with": _check_required_with,
    }
