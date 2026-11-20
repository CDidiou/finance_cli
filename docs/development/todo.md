# Architecture hexagonale

## Principes

L'architecture hexagonale (aussi appelée Ports et Adapters) est une façon d'organiser votre code pour que votre logique métier reste indépendante des détails techniques (base de données, API externe, interface CLI ou web, frameworks).

L'idée centrale : le cœur de votre application ne dépend jamais de la technique ; ce sont les détails techniques qui s'adaptent au cœur. Vous pouvez ainsi changer de base de données ou tester votre logique métier sans réécrire vos règles métier.

## Définitions

Services : Ils orchestrent un cas d'usage concret de votre application (ex. : enregistrer une transaction, calculer un solde). Ils coordonnent les objets métier et appellent les ports nécessaires, sans connaître SQL ni les détails d'une CLI/API.

Ports : Ce sont des interfaces (contrats) définies par le cœur de l'application (en Python, souvent avec Protocol ou abc.ABC).
Un port entrant (Input port) définit ce que le cœur accepte comme action ou commande.
Un port sortant (Output port) définit ce dont le cœur a besoin vers l'extérieur (sauvegarder des données, appeler un service externe).

Adapters : Ce sont les implémentations concrètes qui branchent le monde extérieur sur les ports.
Côté entrée : une commande CLI, une route HTTP, un script... qui traduit l'entrée utilisateur en appel vers le cœur.
Côté sortie : un adaptateur SQLite/PostgreSQL, un client HTTP vers une API boursière, un adaptateur en mémoire pour les tests.

Repository : C'est un type particulier de port + adapter dédié à la persistance (la lecture/écriture d'entités métier). Le cœur définit un repository abstrait (get_by_id, save), et l'adapter fournit l'implémentation concrète (par exemple avec SQLAlchemy ou des fichiers JSON).

Bootstrap (ou Composition Root) : C'est le point d'assemblage au démarrage de l'application. Il instancie les adapters concrets (ex. : connexion DB, client API), les injecte dans les services, et démarre l'application. C'est là que les fils sont branchés, afin que le reste du code n'ait pas à savoir comment tout est fabriqué.

## Les ports

| Protocol	| Adaptateurs possibles |
| --- | --- |
| MarketDataProvider	| Yahoo, Bloomberg, Morningstar |
| ExchangeRateProvider	| ECB, Open Exchange Rates |
| HistoricalPricesProvider	| Yahoo, Stooq |
| NewsProvider	| Reuters, autres sources |

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
available_data_strategies: # déclarés dans le code, en dur
  resources:
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

    calculated: #outputs
      - yaml
      - html

### Stratégies sélectionnées pour les ressources
resources: # choix des stratégies déclarées dans fichier de config externe
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

database_location:
  base: C:\patrimonia\database # could be: absolute - relative (code package) - url
  options: null # to test availability of database
catalogs:
  assets:
    definitions:
      base_dir: data/assets # relative
      yaml:
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


# Structural subtyping

L'architecture ports / adapters peut s'implémenter en python de 2 manières:
- en héritage classique (ABC)
- en structural subtyping

L'héritage classique (ABC) et le structural subtyping (Protocol) sont deux façons d'exprimer le même contrat pour un port :
- Avec ABC (héritage nominal classique) : le port est une classe abstraite (ABC) et il a des méthodes typées @abstractmethod. L'adaptateur hérite explicitement de ce port et implémente les méthodes.
- Avec Protocol (structural subtyping) : un adaptateur satisfait le port s'il expose les bonnes méthodes avec les bonnes signatures, sans avoir à importer ni hériter du port.



L'héritage classique (ABC) est choisi quand on veut que Python bloque immédiatement l'instanciation d'un adaptateur incomplet.
Protocol est préféré quand on veut un découplage maximal (l'adaptateur n'a même pas à dépendre du module contenant le port) ou quand on écrit des adaptateurs de test (fakes / stubs) très légers.

Utilisation dans le projet: pour les providers de web type market_data ou quotes !