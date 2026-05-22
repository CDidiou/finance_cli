# -*- coding: utf-8 -*-
"""Un outil CLI génial"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import click

from finance_cli import __version__
from finance_cli.config import (
    DEFAULT_CONFIG_PATH,
    AppConfig,
    ConfigError,
    ConfigManager,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Groupe principal
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(version=__version__, prog_name="finance-cli")
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_CONFIG_PATH,
    show_default=True,
    envvar="finance_cli_CONFIG",
    help="Chemin vers le fichier de configuration YAML.",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path) -> None:
    """Un outil CLI génial"""
    ctx.ensure_object(dict)
    manager = ConfigManager(path=config_path)
    try:
        ctx.obj["manager"] = manager
        ctx.obj["config"] = manager.config
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc
    manager.apply_logging()


# ---------------------------------------------------------------------------
# Commande hello (démo)
# ---------------------------------------------------------------------------


@main.command()
@click.argument("name", default="World")
@click.option("--count", "-n", default=1, show_default=True, help="Répétitions.")
@click.pass_context
def hello(ctx: click.Context, name: str, count: int) -> None:
    """Dit bonjour à NAME."""
    cfg = ctx.obj["config"]
    for _ in range(count):
        click.echo(f"[{cfg.app_name}] Hello, {name}!")


# ---------------------------------------------------------------------------
# Groupe config
# ---------------------------------------------------------------------------


@main.group()
def config() -> None:
    """Gère la configuration de l'application."""


@config.command("init")
@click.option("--force", is_flag=True, help="Écrase la config existante.")
@click.pass_context
def config_init(ctx: click.Context, force: bool) -> None:
    """Crée le fichier de config YAML avec les valeurs par défaut."""
    manager: ConfigManager = ctx.obj["manager"]
    created = manager.init(overwrite=force)
    if created:
        click.echo(f"✓ Config créée : {manager.path}")
    else:
        click.echo(f"Config déjà existante : {manager.path}  (--force pour écraser)")


@config.command("show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Affiche la configuration courante en YAML."""
    manager: ConfigManager = ctx.obj["manager"]
    click.echo(manager.show(), nl=False)


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Définit un champ de premier niveau.

    Exemples :\n
      finance-cli config set app_name mon-super-outil\n
      finance-cli config set data_format sql
    """
    manager: ConfigManager = ctx.obj["manager"]
    parsed = _coerce_top(key, value)
    try:
        manager.update(**{key: parsed})
    except (ConfigError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"✓ {key} = {parsed!r}")


@config.command("set-section")
@click.argument("section")
@click.argument("pairs", nargs=-1, required=True, metavar="KEY=VALUE...")
@click.pass_context
def config_set_section(
    ctx: click.Context, section: str, pairs: tuple[str, ...]
) -> None:
    """Définit des champs dans une sous-section (logging, excel, sql).

    Exemples :\n
      finance-cli config set-section logging level=DEBUG enabled=true\n
      finance-cli config set-section sql dialect=mysql port=3306 database=prod\n
      finance-cli config set-section excel sheet_name=Résultats max_col_width=60
    """
    manager: ConfigManager = ctx.obj["manager"]

    kwargs = _parse_pairs(section, pairs, manager.config)
    try:
        manager.update_section(section, **kwargs)
    except (ConfigError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    for k, v in kwargs.items():
        click.echo(f"✓ {section}.{k} = {v!r}")


# ---------------------------------------------------------------------------
# Groupe load
# ---------------------------------------------------------------------------


@main.group()
def load() -> None:
    """Charge des données utilisateur."""


@load.command("user-data")
@click.argument("user_id")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["summary", "json", "yaml"]),
    default="summary",
    show_default=True,
    help="Format de sortie.",
)
@click.pass_context
def load_user_data(
    ctx: click.Context,
    user_id: str,
    output: str,
) -> None:
    """Charge et valide le fichier YAML wallet d'un utilisateur par son ID.

    Scanne le dossier data/users/ à la recherche d'un fichier YAML contenant user.id == USER_ID.

    Exemple :\n
      finance-cli load user-data pierre\n
      finance-cli load user-data pierre --output json
    """
    from finance_cli.check_config import load_and_validate_wallet_yaml
    import json as _json
    import yaml

    cfg: AppConfig = ctx.obj["config"]
    users_folder = cfg.data.users.folder

    # Chercher le fichier YAML correspondant à user_id
    if not users_folder.exists():
        raise click.ClickException(f"Dossier data/users introuvable : {users_folder}")

    matching_file = None
    for yaml_file in users_folder.glob("*.yaml"):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if (
                isinstance(data, dict)
                and isinstance(data.get("user"), dict)
                and data["user"].get("id") == int(user_id)
            ):
                matching_file = yaml_file
                break
        except (yaml.YAMLError, IOError):
            # Ignorer les fichiers non-valides
            continue

    if not matching_file:
        raise click.ClickException(
            f"Aucun fichier utilisateur trouvé pour user_id='{user_id}' dans {users_folder}"
        )

    try:
        config = load_and_validate_wallet_yaml(matching_file)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Fichier non trouvé : {exc}") from exc
    except Exception as exc:
        raise click.ClickException(
            f"Erreur lors du chargement/validation : {exc}"
        ) from exc

    if output == "json":
        click.echo(_json.dumps(config.model_dump(), indent=2, default=str))
    elif output == "yaml":
        click.echo(
            yaml.dump(config.model_dump(), default_flow_style=False, allow_unicode=True)
        )
    else:  # summary
        user = config.user
        click.echo(f"👤 Utilisateur : {user.name}")
        click.echo(f"💼 Portefeuilles : {len(user.wallets)}\n")
        for i, wallet in enumerate(user.wallets, 1):
            status = "✓" if wallet.Active else "✗"
            click.echo(
                f"  [{i}] {status} {wallet.Name} | {wallet.Contract} @ {wallet.Broker}"
            )
            click.echo(f"      📅 {wallet.OpeningDate} | 💱 {wallet.Currency}")


@load.command("contracts")
@click.argument("contract_type")
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Chemin du fichier HTML de sortie (défaut : <contract_type>_comparison.html)",
)
@click.pass_context
def load_contracts(
    ctx: click.Context,
    contract_type: str,
    output: Path | None,
) -> None:
    """Charge et compare les offres broker pour un type de contrat.

    Charge le fichier générique et les fichiers spécifiques brokers,
    puis génère un rapport HTML comparatif.

    Exemple :\n
      finance-cli load contracts PEA\n
      finance-cli load contracts PEA -o comparaison_pea.html
    """
    from finance_cli.contract_loader import ContractLoader, generate_contract_comparison_html

    cfg: AppConfig = ctx.obj["config"]
    contracts_folder = cfg.data.contracts.folder

    if not contracts_folder.exists():
        raise click.ClickException(f"Dossier contracts introuvable : {contracts_folder}")

    try:
        loader = ContractLoader(contracts_folder)
        generic, brokers = loader.load_contract_with_brokers(contract_type)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:
        raise click.ClickException(
            f"Erreur lors du chargement des contrats : {exc}"
        ) from exc

    if not brokers:
        raise click.ClickException(
            f"Aucun fichier broker trouvé pour {contract_type} "
            f"(cherche *_{contract_type}.yaml dans {contracts_folder / contract_type})"
        )

    # Génère le HTML
    html_content = generate_contract_comparison_html(contract_type, generic, brokers)

    # Détermine le fichier de sortie
    output_file = output or Path(f"{contract_type}_comparison.html")

    try:
        output_file.write_text(html_content, encoding="utf-8")
        click.echo(f"✓ Rapport HTML généré : {output_file.resolve()}")
    except IOError as exc:
        raise click.ClickException(f"Erreur lors de l'écriture du fichier : {exc}") from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOP_LEVEL_FIELDS = AppConfig.model_fields


def _coerce_top(key: str, raw: str) -> Any:
    """Convertit la valeur brute vers le type attendu pour un champ de premier niveau."""
    if key not in _TOP_LEVEL_FIELDS:
        raise click.BadParameter(
            f"Clé inconnue {key!r}. Disponibles : {list(_TOP_LEVEL_FIELDS)}",
            param_hint="KEY",
        )
    return _cast(raw, _TOP_LEVEL_FIELDS[key].annotation)


def _parse_pairs(
    section: str, pairs: tuple[str, ...], cfg: AppConfig
) -> dict[str, Any]:
    """Parse KEY=VALUE... et coerce selon le sous-modèle de la section."""
    section_models = {
        "logging": cfg.logging,
        "excel": cfg.excel,
        "sql": cfg.sql,
    }
    if section not in section_models:
        raise click.BadParameter(
            f"Section inconnue {section!r}. Disponibles : {list(section_models)}",
            param_hint="SECTION",
        )
    sub_fields = type(section_models[section]).model_fields
    result: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Format attendu KEY=VALUE, reçu : {pair!r}")
        k, v = pair.split("=", 1)
        if k not in sub_fields:
            raise click.BadParameter(
                f"Clé inconnue {k!r} dans [{section}]. Disponibles : {list(sub_fields)}"
            )
        result[k] = _cast(v, sub_fields[k].annotation)
    return result


def _cast(raw: str, annotation: Any) -> Any:
    """Conversion str → type Python simple."""
    origin = getattr(annotation, "__origin__", annotation)
    if origin is bool or annotation is bool:
        if raw.lower() in ("true", "1", "yes", "oui"):
            return True
        if raw.lower() in ("false", "0", "no", "non"):
            return False
        raise click.BadParameter(f"Booléen attendu (true/false), reçu : {raw!r}")
    if origin is int or annotation is int:
        try:
            return int(raw)
        except ValueError:
            raise click.BadParameter(f"Entier attendu, reçu : {raw!r}")
    if annotation is Path:
        return Path(raw)
    return raw


if __name__ == "__main__":
    main()
