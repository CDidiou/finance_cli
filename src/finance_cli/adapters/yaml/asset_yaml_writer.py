"""Persist refreshed asset sections while preserving the YAML document layout."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

import yaml


def write_refreshed_sections(
    asset_file: Path,
    general_info: dict[str, Any],
    market_data: dict[str, Any],
) -> None:
    """Replace or insert the scraped sections using an atomic file replacement."""
    try:
        updated_text = asset_file.read_text(encoding="utf-8")
        for section_name, section_data in (
            ("general_info", general_info),
            ("market_data", market_data),
        ):
            replaced_text = _replace_yaml_section(
                updated_text, section_name, section_data
            )
            if replaced_text is None:
                yaml_text = yaml.safe_dump(
                    {section_name: section_data},
                    sort_keys=False,
                    allow_unicode=True,
                    default_flow_style=False,
                )
                updated_text = _insert_yaml_section(
                    updated_text, section_name, yaml_text
                )
            else:
                updated_text = replaced_text
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=asset_file.parent,
            delete=False,
        ) as temporary_file:
            temporary_file.write(updated_text)
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(asset_file)
    except OSError as exc:
        raise ValueError(f"Impossible de mettre à jour {asset_file} : {exc}") from exc


def _replace_yaml_section(
    original_text: str, section_name: str, section_data: dict[str, Any]
) -> str | None:
    lines = original_text.splitlines(keepends=True)
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if re.fullmatch(rf"{re.escape(section_name)}:\s*(?:#.*)?(?:\r?\n)?", line)
        ),
        None,
    )
    if start is None:
        return None
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_-]*:\s*(?:#.*)?(?:\r?\n)?",
                lines[index],
            )
        ),
        len(lines),
    )
    replacement = yaml.safe_dump(
        {section_name: section_data},
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).splitlines(keepends=True)
    return "".join([*lines[:start], *replacement, *lines[end:]])


def _insert_yaml_section(original_text: str, section_name: str, yaml_text: str) -> str:
    lines = original_text.splitlines(keepends=True)
    if section_name == "market_data":
        general_start = next(
            (
                index
                for index, line in enumerate(lines)
                if re.fullmatch(r"general_info:\s*(?:#.*)?(?:\r?\n)?", line)
            ),
            None,
        )
        if general_start is not None:
            insert_after = next(
                (
                    index - 1
                    for index in range(general_start + 1, len(lines))
                    if re.fullmatch(
                        r"[A-Za-z_][A-Za-z0-9_-]*:\s*(?:#.*)?(?:\r?\n)?",
                        lines[index],
                    )
                ),
                len(lines) - 1,
            )
        else:
            insert_after = next(
                (
                    index
                    for index, line in enumerate(lines)
                    if re.fullmatch(r"(?:id|isin|extends):.*(?:\r?\n)?", line)
                ),
                0,
            )
    else:
        insert_after = next(
            (
                index
                for index, line in enumerate(lines)
                if re.fullmatch(r"(?:id|isin|extends):.*(?:\r?\n)?", line)
            ),
            0,
        )
    insertion = yaml_text
    if (
        insert_after >= 0
        and insert_after < len(lines)
        and not lines[insert_after].endswith(("\n", "\r"))
    ):
        insertion = f"\n{insertion}"
    return "".join([*lines[: insert_after + 1], insertion, *lines[insert_after + 1 :]])
