# -*- coding: utf-8 -*-
"""Chargement et comparaison de contrats d'investissement."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ContractLoader:
    """Charge et agrège les fichiers de contrats (générique + brokers)."""

    def __init__(self, contracts_folder: Path) -> None:
        self.contracts_folder = contracts_folder

    def load_contract_with_brokers(
        self, contract_type: str
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        """Charge le contrat générique et tous les fichiers brokers.

        Args:
            contract_type: Type de contrat (ex: "PEA")

        Returns:
            Tuple (generic_contract_dict, brokers_dict)
            où brokers_dict = {"BB_PEA": {...}, "FN_PEA": {...}, ...}

        Raises:
            FileNotFoundError: Si le fichier générique n'existe pas
            yaml.YAMLError: Si un fichier YAML est invalide
        """
        contract_folder = self.contracts_folder / contract_type
        if not contract_folder.exists():
            raise FileNotFoundError(
                f"Dossier de contrat introuvable : {contract_folder}"
            )

        # Charge le fichier générique (pea.yaml, LDDS.yaml, etc.)
        generic_file = contract_folder / f"{contract_type.lower()}.yaml"
        if not generic_file.exists():
            raise FileNotFoundError(f"Fichier générique introuvable : {generic_file}")

        generic_contract = self._load_yaml(generic_file)
        logger.debug(f"Contrat générique chargé : {generic_file}")

        # Charge tous les fichiers brokers (BB_PEA.yaml, FN_PEA.yaml, etc.)
        brokers: dict[str, dict[str, Any]] = {}
        for broker_file in sorted(contract_folder.glob(f"*_{contract_type}.yaml")):
            broker_data = self._load_yaml(broker_file)
            broker_name = broker_file.stem  # ex: "BB_PEA"
            brokers[broker_name] = broker_data
            logger.debug(f"Données broker chargées : {broker_file}")

        return generic_contract, brokers

    @staticmethod
    def _load_yaml(filepath: Path) -> dict[str, Any]:
        """Charge et parse un fichier YAML."""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError(f"YAML doit contenir un dictionnaire au niveau racine")
            return data
        except yaml.YAMLError as exc:
            raise yaml.YAMLError(
                f"Erreur lors de la lecture de {filepath}: {exc}"
            ) from exc


def generate_contract_comparison_html(
    contract_type: str,
    generic_contract: dict[str, Any],
    brokers: dict[str, dict[str, Any]],
) -> str:
    """Génère un HTML de comparaison des offres broker pour un contrat.

    Args:
        contract_type: Type de contrat (ex: "PEA")
        generic_contract: Dict avec les infos génériques du contrat
        brokers: Dict {nom_broker: données_broker}

    Returns:
        Code HTML comme string
    """

    def render_dict(data: dict[str, Any], indent: int = 0) -> str:
        """Récursivement rend un dict en HTML."""
        html = ""
        for key, value in data.items():
            if isinstance(value, dict):
                html += f"{'  ' * indent}<div class='nested-item'>\n"
                html += (
                    f"{'  ' * (indent + 1)}<strong>{escape_html(str(key))}:</strong>\n"
                )
                html += render_dict(value, indent + 2)
                html += f"{'  ' * indent}</div>\n"
            elif isinstance(value, list):
                html += f"{'  ' * indent}<div class='nested-item'>\n"
                html += (
                    f"{'  ' * (indent + 1)}<strong>{escape_html(str(key))}:</strong>\n"
                )
                html += f"{'  ' * (indent + 1)}<ul>\n"
                for item in value:
                    if isinstance(item, dict):
                        html += f"{'  ' * (indent + 2)}<li>\n"
                        html += render_dict(item, indent + 3)
                        html += f"{'  ' * (indent + 2)}</li>\n"
                    else:
                        html += (
                            f"{'  ' * (indent + 2)}<li>{escape_html(str(item))}</li>\n"
                        )
                html += f"{'  ' * (indent + 1)}</ul>\n"
                html += f"{'  ' * indent}</div>\n"
            else:
                html += f"{'  ' * indent}<div class='item'><strong>{escape_html(str(key))}:</strong> {escape_html(str(value))}</div>\n"
        return html

    def escape_html(text: str) -> str:
        """Échappe les caractères HTML."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    # Prépare les sections des brokers
    broker_sections = ""
    for broker_name in sorted(brokers.keys()):
        broker_data = brokers[broker_name]
        broker_html_name = escape_html(broker_data.get("broker", broker_name))
        broker_link = broker_data.get("link", "#")

        broker_sections += f"""
        <div class="broker-section">
          <h3><a href="{broker_link}" target="_blank">{broker_html_name}</a></h3>
          <div class="broker-content">
            {render_dict(broker_data)}
          </div>
        </div>
        """

    # Assemble le HTML complet
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparaison {escape_html(contract_type)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        header h1 {{
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}
        
        .generic-section {{
            background: white;
            border-left: 5px solid #667eea;
            padding: 2rem;
            margin-bottom: 2rem;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .generic-section h2 {{
            color: #667eea;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }}
        
        .brokers-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
        }}
        
        .broker-section {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .broker-section:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .broker-section h3 {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            margin: 0;
        }}
        
        .broker-section h3 a {{
            color: white;
            text-decoration: none;
        }}
        
        .broker-section h3 a:hover {{
            text-decoration: underline;
        }}
        
        .broker-content {{
            padding: 1.5rem;
        }}
        
        .nested-item {{
            margin: 1rem 0;
            padding: 1rem;
            background-color: #fafafa;
            border-left: 3px solid #ddd;
            border-radius: 2px;
        }}
        
        .item {{
            margin: 0.75rem 0;
            padding: 0.5rem;
        }}
        
        .item strong {{
            color: #667eea;
            min-width: 150px;
            display: inline-block;
        }}
        
        ul {{
            list-style-position: inside;
            padding-left: 1rem;
        }}
        
        li {{
            margin: 0.5rem 0;
        }}
        
        footer {{
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>📊 Comparaison {escape_html(contract_type)}</h1>
        <p>Analyse des offres par broker</p>
    </header>
    
    <div class="container">
        <div class="generic-section">
            <h2>ℹ️ Informations Génériques</h2>
            {render_dict(generic_contract)}
        </div>
        
        <h2 style="color: #333; margin-top: 2rem; margin-bottom: 1.5rem;">🏦 Offres Broker</h2>
        <div class="brokers-container">
            {broker_sections}
        </div>
    </div>
    
    <footer>
        <p>Generated by finance-cli | {contract_type} Comparison Report</p>
    </footer>
</body>
</html>
"""
    return html
