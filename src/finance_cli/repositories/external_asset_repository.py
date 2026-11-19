"""Accès et inspection des données externes des actifs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from finance_cli.config.paths_resolver import ConfigPathResolver
from finance_cli.exceptions.configuration import ResourceConfigurationError


@dataclass(frozen=True)
class ResourceFileStatus:
    """Résultat de l'inspection d'un dossier de ressource."""

    folder: Path
    folder_exists: bool
    matching_files: tuple[Path, ...] = ()
    unrecognized_files: tuple[Path, ...] = ()


class ExternalAssetRepository:
    """Inspecte les fichiers des ressources externes."""

    PLACEHOLDER_PATTERNS = {
        "YYYY": r"\d{4}",
        "MM": r"\d{2}",
    }

    def __init__(self, path_resolver: ConfigPathResolver) -> None:
        self.path_resolver = path_resolver

    # --- API PUBLIQUE ---

    def inspect_resource(
        self,
        folder: Path,
        filename_pattern: str,
        context: dict[str, str],
        extensions: set[str] | None = None,
    ) -> ResourceFileStatus:
        """Vérifie le dossier et classe les fichiers selon leur nom.

        Args:
            folder: Dossier à inspecter.
            filename_pattern: Modèle configuré du nom de fichier.
            context: Valeurs des placeholders.
            extensions: Extensions à prendre en compte, par exemple {".yaml"}.
                Si None, tous les fichiers sont inspectés.
        """

        if not folder.exists() or not folder.is_dir():
            return ResourceFileStatus(
                folder=folder,
                folder_exists=False,
            )

        normalized_extensions = (
            {
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in extensions
            }
            if extensions is not None
            else None
        )

        regex = self._compile_filename_pattern(
            filename_pattern,
            context,
        )

        matching_files: list[Path] = []
        unrecognized_files: list[Path] = []

        for path in sorted(folder.iterdir()):
            if not path.is_file():
                continue

            if (
                normalized_extensions is not None
                and path.suffix.lower() not in normalized_extensions
            ):
                continue

            if regex.fullmatch(path.name):
                matching_files.append(path)
            else:
                unrecognized_files.append(path)

        return ResourceFileStatus(
            folder=folder,
            folder_exists=True,
            matching_files=tuple(matching_files),
            unrecognized_files=tuple(unrecognized_files),
        )

    def inspect_asset(
        self,
        asset_id: str,
        category_path: Path,
    ) -> dict[str, ResourceFileStatus]:
        """Inspecte les ressources externes d'un actif."""

        context = {
            "ID_ASSET": asset_id,
            "CATEGORY_PATH": category_path.as_posix(),
        }

        resource_keys = {
            "quotes": "external/assets/quotes",
            "factsheets_source": "external/assets/factsheets/source",
            "factsheets_extracted": "external/assets/factsheets/extracted",
            "scraped_data": "external/assets/scraped_data",
        }

        resource_extensions = {
            "quotes": {".yaml"},
            "factsheets_source": {".pdf"},
            "factsheets_extracted": {".yaml"},
            "scraped_data": {".yaml"},
        }

        results: dict[str, ResourceFileStatus] = {}

        # Les deux types de factsheets partagent le même dossier.
        factsheets_folder = self.path_resolver.resolve_directory(
            resource_keys["factsheets_source"],
            context=context,
        )

        for name, resource_key in resource_keys.items():
            resource = self.path_resolver.resolve_resources(
                resource_key,
                context=context,
            )

            folder = (
                factsheets_folder
                if name in {"factsheets_source", "factsheets_extracted"}
                else resource.folder
            )

            if resource.filename is None:
                raise ResourceConfigurationError(
                    f"Modèle de nom absent pour '{resource_key}'."
                )

            results[name] = self.inspect_resource(
                folder=folder,
                filename_pattern=resource.filename,
                context=context,
                extensions=resource_extensions[name],
            )

        return results

    # --- HELPERS INTERNES ---

    def _compile_filename_pattern(
        self,
        filename_pattern: str,
        context: dict[str, str],
    ) -> re.Pattern[str]:
        """Convertit un modèle configuré en expression régulière."""

        parts: list[str] = []
        position = 0

        for match in re.finditer(r"<([^<>]+)>", filename_pattern):
            parts.append(re.escape(filename_pattern[position : match.start()]))

            token = match.group(1)

            if token in self.PLACEHOLDER_PATTERNS:
                expression = self.PLACEHOLDER_PATTERNS[token]
            elif token in context:
                expression = re.escape(context[token])
            else:
                raise ResourceConfigurationError(
                    f"Placeholder non résolu dans le modèle de fichier : '<{token}>'."
                )

            parts.append(expression)
            position = match.end()

        parts.append(re.escape(filename_pattern[position:]))

        return re.compile("".join(parts))
