# Finance CLI — Documentation synthétique

## 1. Présentation

`finance-cli` est une application Python en ligne de commande destinée à gérer des portefeuilles financiers, leurs comptes, leurs transactions et leurs historiques de valorisation.

Le projet utilise Python, Click pour l'interface CLI, Poetry pour la gestion du projet, YAML pour les fichiers de configuration et Excel pour les données financières des utilisateurs.

## 2. Poetry

### Installation

```bash
pip install finance-cli
```

Ou en développement :

```bash
poetry install
```

### Utilisation

```bash
poetry run finance-cli
```

Options disponibles depuis le terminal :

```bash
finance-cli --help
finance-cli --version
```

### Développement

```bash
# Lancer les tests
poetry run pytest
poetry run pytest tests/test_cli/test_list.py::test_list_users_uses_yaml_name_and_skips_nested_wallets

# Linter / formatter
poetry run ruff check .
poetry run ruff format .

# Vérification de types
poetry run mypy src/
```

## 3. Commandes CLI disponibles

### Afficher un compte

```bash
finance-cli account show <account_id>
```

Affiche les informations d'un compte.

### Afficher un wallet

```bash
finance-cli wallet show <wallet_id> --user <user_id>
```

Exemple :

```bash
finance-cli wallet show pea-pierre --user pierre
```

Charge la fiche du wallet et affiche ses données.

## 4. Organisation des données (vue d'ensemble)

```text
data/
  contracts/
  assets/

external-data/
  users/
    pierre.yaml
    pierre/
      pea-pierre.yaml
      pea-pierre/
        tx/
          2025_tx_pea-pierre.xlsx
        balance/
          2024_12_31_balance_pea-pierre.xlsx
```

Le fichier utilisateur référence les wallets détenus. Chaque fiche wallet référence son contrat et les actifs concernés.

Les fichiers de transactions sont organisés par année. Les fichiers de balances sont identifiés par leur date.

Pour le détail du modèle de données YAML, des règles d’héritage et du format Excel, voir [info_project.md](info_project.md).

## 5. Architecture technique

Les modèles métier sont regroupés dans `finance_cli/models/` :

```text
finance_cli/
  models/
    __init__.py
    account.py
    wallet.py
    transaction.py
    balance.py
  readers/
    transaction_excel_reader.py
  common/
    generic_functions.py
```

Les responsabilités sont séparées :

- **Models** : représentation des objets métier et validation de leurs données.
- **Readers** : lecture, validation et écriture des fichiers de données.
- **Common** : fonctions utilitaires partagées, notamment la configuration et le chargement YAML.
- **CLI** : commandes Click exposant les fonctionnalités à l'utilisateur.

Les imports des modèles privilégient le module, par exemple :

```python
from finance_cli.models import wallet

obj = wallet.Wallet(user_id="pierre", wallet_id="pea-pierre").load()
```
