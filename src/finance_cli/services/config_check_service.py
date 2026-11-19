"""Service de contrôle de la configuration applicative."""

from dataclasses import dataclass

from finance_cli.config.config_models import AppConfig


@dataclass(frozen=True)
class ConfigCheckIssue:
    resource: str
    message: str


@dataclass(frozen=True)
class ConfigCheckResult:
    checked_resources: int
    issues: tuple[ConfigCheckIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues


class ConfigCheckService:
    """Orchestre les contrôles complémentaires de configuration."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def check_config(self) -> ConfigCheckResult:
        """Exécute les contrôles de configuration."""

        issues: list[ConfigCheckIssue] = []
        checked_resources = 0

        catalog = self.config.data.catalog

        resources = {
            "data.catalog.financial.assets": catalog.financial.assets,
            "data.catalog.financial.contracts": catalog.financial.contracts,
            "data.catalog.references.economy": catalog.references.economy,
        }

        for name, resource in resources.items():
            checked_resources += 1

            for attribute in ("folder", "schemas", "rules"):
                relative_path = getattr(resource, attribute)
                path = self.config.base_dir / relative_path

                if not path.exists():
                    issues.append(
                        ConfigCheckIssue(
                            resource=f"{name}.{attribute}",
                            message=f"Répertoire introuvable : {path}",
                        )
                    )
                elif not path.is_dir():
                    issues.append(
                        ConfigCheckIssue(
                            resource=f"{name}.{attribute}",
                            message=f"Le chemin n'est pas un répertoire : {path}",
                        )
                    )

        return ConfigCheckResult(
            checked_resources=checked_resources,
            issues=tuple(issues),
        )
