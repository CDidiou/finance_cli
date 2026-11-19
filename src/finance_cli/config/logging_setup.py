"""Configuration du système de logging de Patrimonia."""

import logging
import sys

from finance_cli.config.config_models import LoggingSettings

FORMATS = {
    "simple": "%(levelname)s: %(message)s",
    "standard": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    "detailed": (
        "%(asctime)s - %(levelname)s [%(name)s] %(filename)s:%(lineno)d - %(message)s"
    ),
}


def configure_logging(config: LoggingSettings) -> None:
    """Configure le logging à partir des paramètres dédiés."""

    if not config.enabled:
        logging.disable(logging.CRITICAL)
        return

    # Réactive le logging si celui-ci avait été désactivé.
    logging.disable(logging.NOTSET)

    level = getattr(logging, config.level.upper(), None)
    if not isinstance(level, int):
        raise ValueError(f"Niveau de log invalide : {config.level}")

    try:
        log_format = FORMATS[config.format]
    except KeyError:
        raise ValueError(f"Format de log invalide : {config.format}") from None

    formatter = logging.Formatter(log_format)

    # Configuration du logger racine.
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Suppression des handlers existants.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # Création du handler.
    if config.output == "file":
        log_path = config.file_path

        if log_path is None:
            raise ValueError(
                "Un chemin de fichier de log doit être défini "
                "lorsque logging.output vaut 'file'."
            )

        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")

    elif config.output == "console":
        handler = logging.StreamHandler(sys.stderr)

    else:
        raise ValueError(f"Destination de logging invalide : {config.output}")

    handler.setLevel(level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
