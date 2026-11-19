"""Contexte d'exécution de l'application."""

from dataclasses import dataclass

from finance_cli.config.config_models import AppConfig
from finance_cli.bootstrap.services import Services


@dataclass(frozen=True)
class AppContext:
    config: AppConfig
    services: Services
