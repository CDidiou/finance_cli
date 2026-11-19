# Strategies de stockage des datas

Séparation MarkUp vs Sql

On ne choisit pas indépendamment un repository, un format de fichier et un mécanisme de validation.
On choisit une stratégie de stockage et de manipulation des données.

Une famille de données dispose de plusieurs stratégies de stockage possibles. Chaque stratégie définit conjointement le repository, les formats de données, les mécanismes de lecture/écriture et les validations techniques nécessaires. Les règles métier restent indépendantes de la stratégie choisie.

| Stratégie	| Formats ou mécanismes associés |
| --- | --- |
| YAML direct	| YAML |
| Excel	| XLSX, éventuellement CSV |
| SQL	| Base de données et scripts SQL |

## config_app: sélection des stratégies

2 parties: les stratégies actuellement implémentées et disponibles, et les stratégies sélectionnées par repository.

available décrit les capacités de l'application ; strategy décrit le choix de l'utilisateur. Les deux sont comparés lors du config check.
available est un fichier dans la zone de code et non pas dans la zone globale de config de l'application.

### Stratégies effectivement implémentées dans l'application
available_repositories_strategies:
  repositories:
    catalogs:
      assets:
        available:
          - yaml
          # - sql
        additional_info:
          quotes:
            available:
              - yaml
          scraped_data:
            available:
              - yaml
      contracts:
        available:
          - yaml
      economy_references:
        avalable:
          - yaml

    inputs:
      users:
        available:
          - yaml
          - excel
          # - sql
        wallets:
          transactions:
            available:
              - yaml
              - excel

    calculated:
      - yaml
      - html

### Stratégies sélectionnées pour les ressources
selected_repositories_strategies:
  catalogs:
    assets:
      strategy: yaml  # yaml | sql
      additional_info:
        factsheet:
          source:
            strategy: pdf
          extracted:
            strategy: yaml          
        scraped_data:
          strategy: yaml
        quotes:
          strategy: yaml

    contracts:
      strategy: yaml  # yaml | sql

    economy_references:
      strategy: yaml  # yaml | sql

  inputs:
    users:
      strategy: excel  # yaml | excel | sql
      wallets:
        transactions:
          strategy: excel  # yaml | excel | sql => peut être à reporter dans la fiche user!
        balances:
          strategy: excel  # yaml | excel | sql => peut être à reporter dans la fiche user!

  calculated:
    users:
      dashboards:
        strategy: html
      evolution:
        strategy: yaml
      balances:
        strategy: yaml
      wallets:
        dashboards:
          strategy: html
        evolution:
          strategy: yaml
        transactions_enriched:
          strategy: yaml
        balances:
          strategy: yaml


## config_data: détail de la stratégie

Les regles json schemas sont des definitions. Elles imposent le format de données. Leur implémentation est dépendante de la strategy du repository (yaml ou sql).
En revanche les règles métier sont indépendantes de la strategy du repository.

Pour les règles métiers (rules), il faut distinguer:
- la déclaration d'une règle : ce qu'il faut vérifier - écriture en yaml
- l'exécution d'une règle : comment le système effectue la vérification - fait par un moteur Python
On déclare les règles en YAML et avoir un moteur Python qui les interprète.

Une règle simple comme « la date de clôture doit être postérieure à la date de création » se décrit très bien en YAML.
En revanche, une règle comme :
La performance annualisée d'un actif doit être cohérente avec l'évolution de ses cours sur plusieurs périodes, en tenant compte des opérations sur titres. => fonction python directe!

Le moteur Python fournit les opérateurs disponibles :
- equals
- not_equals
- is_null
- is_not_null
- greater_than
- less_than
- in
- matches
- before
- after
Il sait également combiner les conditions avec all, any et not.
Les règles sont modifiables sans modifier le code Python, tant qu'elles utilisent les capacités existantes du moteur.

catalogs:
  assets:
    definitions:
      yaml:
        folder: data/assets
        filename: "<ID_ASSET>.yaml"
        schemas:
          common: resources/schemas/common
          specific: resources/schemas/assets

      sql:
        database: data/patrimonia.db
        scripts: resources/sql/assets

    rules:
      - general.yaml
      - dates.yaml
      - quotes.yaml

    additional_info:
      quotes:
        definitions:
          yaml:
            folder: external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/quotes
        rules:
          - dates.yaml

  economy_references:
    definitions:
      yaml:
        folder: data/economy
        filename: "<REFERENCE>.yaml"
        schemas:
          common: resources/schemas/common
          specific: resources/schemas/economy

      sql:
        database: data/patrimonia.db
        scripts: resources/sql/economy

    rules:
      - references.yaml