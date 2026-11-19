"""Interactive command-line interface for patrimonia."""

from __future__ import annotations

import logging
import shlex
from datetime import datetime
from pathlib import Path

import click
import yaml

from finance_cli import __version__
from finance_cli.bootstrap.app_context import AppContext
from finance_cli.bootstrap.container import build_services
from finance_cli.config import app_config, logging_setup
from finance_cli.exceptions.base import PatrimoniaError

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Logging levels is governed by the application conf


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="patrimonia")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=app_config.DEFAULT_CONFIG_PATH,
    show_default=True,
    help="Chemin vers le fichier de configuration YAML.",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path) -> None:
    """Ouvre l'invite interactive de Patrimonia."""

    if isinstance(ctx.obj, AppContext):
        app_context = ctx.obj
    else:
        config = app_config.load_app_config(config_path)
        logging_setup.configure_logging(config.logging)

        services = build_services(config)

        app_context = AppContext(
            config=config,
            services=services,
        )

    ctx.obj = app_context

    if ctx.invoked_subcommand is None:
        _run_prompt(ctx)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@main.group("config")
def config_group() -> None:
    """Opérations sur la configuration de Patrimonia."""


@config_group.command("check")
@click.pass_obj
def check_config(app: AppContext) -> None:
    """Vérifie la configuration applicative."""

    result = app.services.config_check_service.check_config()

    click.echo("Configuration applicative")
    click.echo("--------------------------")

    if result.is_valid:
        click.echo(f"OK - {result.checked_resources} ressources contrôlées.")
        return

    click.echo(f"ÉCHEC - {len(result.issues)} problème(s) détecté(s).")

    for issue in result.issues:
        click.echo(f"  [ERREUR] {issue.resource}")
        click.echo(f"           {issue.message}")

    raise click.exceptions.Exit(3)


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


@main.group("users")
def users_group() -> None:
    """Opérations sur la collection des utilisateurs."""


@users_group.command("list")
@click.pass_obj
def users_list(app: AppContext) -> None:
    """Liste les utilisateurs configurés."""
    items = app.services.list_service.list_users()

    if not items:
        click.echo("Aucun utilisateur trouvé.")
        return

    click.echo("Liste des utilisateurs :")
    for item in items:
        click.echo(f"{item.id} / {item.generic_name}: {item.label}")


@main.group("accounts")
def accounts_group() -> None:
    """Opérations sur la collection des comptes."""


@accounts_group.command("list")
@click.pass_obj
def accounts_list(app: AppContext) -> None:
    """Liste les comptes définis."""
    items = app.services.list_service.list_accounts()

    if not items:
        click.echo("Aucun compte trouvé.")
        return

    click.echo("Liste des comptes :")
    for item in items:
        click.echo(f"{item.label} : {item.generic_name}")


@main.group("assets")
def assets_group() -> None:
    """Opérations sur la collection des actifs."""


@assets_group.command("list")
@click.pass_obj
def assets_list(app: AppContext) -> None:
    """Liste les actifs définis."""
    items = app.services.list_service.list_assets()

    if not items:
        click.echo("Aucun actif trouvé.")
        return

    click.echo("Liste des actifs :")
    for item in items:
        click.echo(f"{item.label} : {item.generic_name}")


# ---------------------------------------------------------------------------
# Asset : un actif identifié par son ID
# ---------------------------------------------------------------------------


@main.group("asset")
@click.option(
    "--id",
    "asset_id",
    required=True,
    help="Identifiant de l'actif (ISIN).",
)
@click.pass_context
def asset_group(ctx: click.Context, asset_id: str) -> None:
    """Opérations sur un actif identifié par son ID."""
    pass


@asset_group.command("show")
@click.option(
    "--section",
    "sections",
    multiple=True,
    type=click.Choice(
        ["general_info", "market_data", "sources", "quote", "py_finance"]
    ),
    help="Sections to display.",
)
@click.pass_context
def asset_show(
    ctx: click.Context,
    sections: tuple[str, ...],
) -> None:
    """Display an asset from the reference catalogue."""
    app: AppContext = ctx.obj
    asset_id = ctx.parent.params["asset_id"]
    sections = ctx.params["sections"] or None

    try:
        payload = app.services.asset_service.show(asset_id, sections=sections or None)
    except PatrimoniaError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Actif : {asset_id}")
    click.echo("---")
    click.echo(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))


@asset_group.command("status")
@click.pass_context
def asset_status(ctx: click.Context) -> None:
    """Display an asset from the reference catalogue."""
    app: AppContext = ctx.obj
    asset_id = ctx.parent.params["asset_id"]

    try:
        folder_status = app.services.asset_status_service.get_status(asset_id)
    except PatrimoniaError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Actif : {asset_id}")
    click.echo("---")
    click.echo(yaml.safe_dump(folder_status, allow_unicode=True, sort_keys=False))


@asset_group.group("extract")
def asset_extract_group() -> None:
    """Extrait des données externes pour cet actif."""


@asset_extract_group.command("factsheet")
@click.pass_context
def asset_extract_factsheet(ctx: click.Context) -> None:
    """Extrait les informations d'une factsheet PDF."""
    asset_id = ctx.obj["asset_id"]
    pass


@asset_group.group("retrieve")
@click.pass_context
def asset_retrieve_group(ctx: click.Context) -> None:
    """Collecte des données externes pour cet actif."""
    asset_id = ctx.parent.params["asset_id"]
    ctx.obj = {
        "app": ctx.obj,
        "asset_id": asset_id,
    }


@asset_retrieve_group.command("market-data")
@click.pass_context
def asset_fetch_market_data(ctx: click.Context) -> None:
    """Collecte les données marché via Yahoo Finance."""
    app: AppContext = ctx.obj["app"]
    asset_id: str = ctx.obj["asset_id"]

    try:
        result = app.services.asset_service.retrieve_market_data(asset_id)
    except PatrimoniaError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.status == "created":
        click.echo(f"Nouvelles données marché enregistrées : {result.file_path}")

    elif result.status == "updated":
        click.echo(f"Données marché mises à jour : {result.file_path}")

    elif result.status == "unchanged":
        click.echo(
            f"Aucune mise à jour nécessaire. "
            f"Les données existantes sont conservées : {result.file_path}"
        )

    elif result.status == "rejected":
        click.echo(
            f"Données marché rejetées : {result.message}",
            err=True,
        )


@asset_group.group("update")
@click.pass_context
def asset_update_group(ctx: click.Context) -> None:
    """Applique des données externes au catalogue."""
    asset_id = ctx.parent.params["asset_id"]
    ctx.obj = {
        "app": ctx.obj,
        "asset_id": asset_id,
    }


@asset_update_group.command("factsheet")
@click.pass_context
def asset_update_factsheet(ctx: click.Context) -> None:
    """Applique les données extraites d'une factsheet."""
    asset_id = ctx.obj["asset_id"]
    pass


@asset_update_group.command("market-data")
@click.pass_context
def asset_update_market_data(ctx: click.Context) -> None:
    """Applique les données marché au catalogue."""
    app: AppContext = ctx.obj["app"]
    asset_id: str = ctx.obj["asset_id"]

    try:
        asset = app.services.asset_service.update_scraped_data(asset_id)
    except PatrimoniaError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Catalogue mis à jour pour l'actif : {asset_id}")


# ---------------------------------------------------------------------------
# Account : un compte identifié par son ID
# ---------------------------------------------------------------------------


@main.group("account")
@click.argument("account_id")
@click.pass_context
def account_group(ctx: click.Context, account_id: str) -> None:
    """Opérations sur un compte identifié par son ID."""
    ctx.obj["account_id"] = account_id


@account_group.command("show")
@click.option(
    "--type-path",
    required=True,
    help="Chemin du fichier ou dossier définissant le type de compte.",
)
@click.pass_context
def account_show(ctx: click.Context, type_path: str) -> None:
    """Affiche les informations d'un compte."""
    account_id = ctx.obj["account_id"]
    pass


# ---------------------------------------------------------------------------
# Wallet : un portefeuille identifié par son ID
# ---------------------------------------------------------------------------


@main.group("wallet")
@click.argument("wallet_id")
@click.option(
    "--user",
    required=True,
    help="Identifiant de l'utilisateur propriétaire du wallet.",
)
@click.pass_context
def wallet_group(
    ctx: click.Context,
    wallet_id: str,
    user: str,
) -> None:
    """Opérations sur un wallet identifié par son ID."""
    ctx.obj["wallet_id"] = wallet_id
    ctx.obj["user_id"] = user


@wallet_group.command("show")
@click.pass_context
def wallet_show(ctx: click.Context) -> None:
    """Affiche les informations d'un wallet."""
    wallet_id = ctx.obj["wallet_id"]
    user_id = ctx.obj["user_id"]
    pass


@wallet_group.command("check")
@click.pass_context
def wallet_check(ctx: click.Context) -> None:
    """Vérifie la cohérence du wallet et de ses données."""
    wallet_id = ctx.obj["wallet_id"]
    user_id = ctx.obj["user_id"]
    pass


@wallet_group.group("transactions")
def wallet_transactions_group() -> None:
    """Opérations sur les transactions du wallet."""


@wallet_transactions_group.command("validate")
@click.pass_context
def wallet_transactions_validate(ctx: click.Context) -> None:
    """Valide les transactions du wallet."""
    wallet_id = ctx.obj["wallet_id"]
    user_id = ctx.obj["user_id"]
    pass


@wallet_transactions_group.command("prepare")
@click.pass_context
def wallet_transactions_prepare(ctx: click.Context) -> None:
    """Prépare les transactions du wallet."""
    wallet_id = ctx.obj["wallet_id"]
    user_id = ctx.obj["user_id"]
    pass


@wallet_group.group("balance")
def wallet_balance_group() -> None:
    """Opérations sur la balance du wallet."""


@wallet_balance_group.command("calculate")
@click.option(
    "--date",
    "target_datetime",
    required=True,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Date cible (YYYY-MM-DD).",
)
@click.pass_context
def wallet_balance_calculate(
    ctx: click.Context,
    target_datetime: datetime,
) -> None:
    """Calcule la balance du wallet à la date cible."""
    wallet_id = ctx.obj["wallet_id"]
    user_id = ctx.obj["user_id"]
    pass


# --- HELPERS INTERNES ---
def _run_prompt(ctx: click.Context) -> None:
    """Run the interactive Patrimonia command prompt."""

    click.echo("patrimonia - tapez 'help' pour l'aide, 'exit' pour quitter.")

    app_context = ctx.obj

    while True:
        try:
            line = click.prompt(
                "patrimonia",
                prompt_suffix="> ",
                default="",
                show_default=False,
            )

        except (EOFError, KeyboardInterrupt):
            click.echo()
            return

        if not line.strip():
            continue

        try:
            arguments = shlex.split(line)

        except ValueError as exc:
            click.echo(f"Erreur de saisie : {exc}", err=True)
            continue

        command = arguments[0].casefold()

        if command in {"exit", "quit"} and len(arguments) == 1:
            return

        if command in {"help", "?"}:
            command_path = " ".join(arguments[1:]) or None
            _show_help(ctx, command_path)
            continue

        try:
            main.main(
                args=arguments,
                prog_name="patrimonia",
                standalone_mode=False,
                obj=app_context,
            )

        except click.ClickException as exc:
            click.echo(
                f"Erreur : {exc.format_message()}",
                err=True,
            )

        except click.exceptions.Exit:
            pass

        except click.Abort:
            click.echo("Commande interrompue.", err=True)

        except PatrimoniaError as exc:
            click.echo(f"Erreur : {exc}", err=True)

        except Exception:
            logger.exception(
                "Erreur inattendue lors de l'exécution d'une commande interactive."
            )
            click.echo(
                "Erreur interne inattendue. Consultez les logs pour plus de détails.",
                err=True,
            )


def _show_help(
    ctx: click.Context,
    command_path: str | None = None,
) -> None:
    """Display general or command-specific help."""

    if not command_path:
        _show_general_help(ctx)
        return

    current_ctx = ctx
    current_command = ctx.command

    for name in command_path.split():
        if not isinstance(current_command, click.Group):
            click.echo(f"Commande inconnue : {command_path}")
            return

        subcommand = current_command.get_command(current_ctx, name)

        if subcommand is None or subcommand.hidden:
            click.echo(f"Commande inconnue : {command_path}")
            return

        current_ctx = click.Context(
            subcommand,
            info_name=name,
            parent=current_ctx,
            resilient_parsing=True,
        )
        current_command = subcommand

    _show_command_help(current_command, current_ctx)


def _show_general_help(ctx: click.Context) -> None:
    """Display general application help and prompt commands."""

    formatter = ctx.make_formatter()

    formatter.write(ctx.get_help())

    with formatter.section("Commandes du prompt"):
        formatter.write_dl(
            [
                ("help", "Affiche cette aide."),
                ("help <commande>", "Affiche l'aide d'une commande."),
                ("exit, quit", "Quitte Patrimonia."),
            ]
        )

    click.echo(formatter.getvalue())


def _show_command_help(
    command: click.Command,
    command_ctx: click.Context,
) -> None:
    """Display detailed help using Click's native formatter."""

    click.echo(command.get_help(command_ctx))
