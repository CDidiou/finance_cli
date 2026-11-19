# Patrimonia --- Architecture technique

> **Patrimonia** est le nom fonctionnel proposé pour le projet. Le
> package Python reste nommé `finance_cli` afin d'éviter
> un renommage technique simultané à l'évolution de l'architecture.

## 1. Principes d'architecture

Patrimonia est une application Python organisée autour d'une séparation
entre les responsabilités métier et les mécanismes techniques.

L'architecture distingue notamment :

-   L'interface utilisateur en ligne de commande.
-   Le bootstrap, chargé de construire et d'assembler les dépendances.
-   Les services qui orchestrent les cas d'utilisation.
-   Les repositories qui encapsulent l'accès aux données et leur
    persistance.
-   Les adaptateurs qui assurent les interactions avec les fournisseurs
    externes.
-   Les modèles qui représentent les données métier et les données
    collectées.
-   Les composants de validation.
-   La configuration et la résolution des ressources.

L'objectif est de limiter les dépendances entre composants, de faciliter
les tests et de rendre les services indépendants des mécanismes concrets
de persistance.

Les services ne construisent pas eux-mêmes leurs dépendances et ne
manipulent pas directement les fichiers YAML. Ils délèguent ces
responsabilités aux composants spécialisés.

## 2. Organisation des composants

### 2.1. Vue d'ensemble

``` text
finance_cli/
│
├── bootstrap/
│   └── dependencies.py
│
├── cli/
│   └── Commandes Click
│
├── services/
│   └── assets/
│       └── asset_service.py
│
├── repositories/
│   ├── asset_repository.py
│   └── scraped_data_repository.py
│
├── adapters/
│   └── web/
│       └── yahoo_finance.py
│
├── models/
│   ├── asset.py
│   └── scraped_asset.py
│
├── validation/
│   ├── schema_loader.py
│   ├── schema_validator.py
│   └── reference_validator.py
│
├── config/
│   └── paths_resolver.py
│
└── common/
    ├── yaml_io.py
    └── scraped_to_catalog.py
```

Cette représentation décrit l'organisation logique actuelle des
composants. Les modules pourront évoluer avec l'implémentation.

### 2.2. CLI

La couche CLI expose les fonctionnalités de l'application.

Elle reçoit les arguments de l'utilisateur, vérifie les paramètres de
commande et délègue les traitements aux services.

Elle ne doit contenir ni logique métier ni logique de manipulation
directe des fichiers.

### 2.3. Bootstrap

Le module `bootstrap` est responsable de la construction et de
l'assemblage des dépendances de l'application.

Par exemple, `bootstrap/dependencies.py` construit les validateurs, les
repositories et les adaptateurs nécessaires, puis les injecte dans les
services.

Cette couche constitue le point de composition de l'application. Elle ne
contient pas de logique métier.

Exemple d'utilisation :

``` python
asset_service = build_asset_service(config)
```

### 2.4. Services

Les services orchestrent les cas d'utilisation.

Ils déterminent l'ordre des opérations et coordonnent les repositories
et les adaptateurs nécessaires, sans prendre en charge directement les
mécanismes de persistance.

Par exemple, `AssetService` pilote les opérations relatives aux actifs :

-   Consultation d'un actif.
-   Collecte de données financières.
-   Intégration de données scraped dans le catalogue.

`AssetService` reçoit ses dépendances par injection :

-   `AssetRepository`.
-   `ScrapedDataRepository`.
-   `YahooFinanceAdapter`.

Il ne construit pas lui-même ces composants.

### 2.5. Repositories

Les repositories encapsulent l'accès aux données, leur validation et
leur persistance.

  -----------------------------------------------------------------------
  Repository                          Responsabilité
  ----------------------------------- -----------------------------------
  `AssetRepository`                   Lecture, validation et sauvegarde
                                      des fiches du catalogue

  `ScrapedDataRepository`             Lecture, validation et stockage des
                                      données scraped
  -----------------------------------------------------------------------

Les repositories masquent aux services les détails de stockage,
notamment les chemins, les noms de fichiers et les opérations de lecture
ou d'écriture YAML.

Ils utilisent les composants de configuration et de validation
nécessaires à leur responsabilité.

### 2.6. Adaptateurs

Les adaptateurs isolent les interactions avec les fournisseurs externes.

  -----------------------------------------------------------------------
  Adaptateur                          Responsabilité
  ----------------------------------- -----------------------------------
  `YahooFinanceAdapter`               Collecte et adaptation des données
                                      provenant de Yahoo Finance

  -----------------------------------------------------------------------

L'adaptateur fournisseur ne prend pas en charge la persistance dans le
catalogue ou dans les données externes. Il récupère les données et les
convertit dans une structure exploitable par l'application.

Les anciens adaptateurs de persistance `CatalogAdapter` et
`ExternalDataAdapter` sont remplacés par `AssetRepository` et
`ScrapedDataRepository`. Ils ne font donc plus partie de l'architecture
cible.

### 2.7. Modèles

Les modèles Pydantic représentent les objets manipulés par les services
et les repositories.

Deux modèles principaux interviennent dans le traitement des actifs :

-   `Asset` : représentation d'une fiche du catalogue.
-   `AggregatedScrapedAsset` : représentation des données collectées.

Ces modèles sont distincts : les données scraped ne constituent pas
directement une fiche catalogue.

La conversion entre les deux structures est réalisée explicitement par
`scraped_to_catalog`.

## 3. Organisation des données

### 3.1. Catalogue

Le catalogue contient les données de référence de l'application.

Exemple d'organisation :

``` text
data/
└── assets/
    ├── CW8.yaml
    ├── ...
    └── ...
```

Chaque actif dispose d'une fiche YAML identifiée par son `ID_ASSET`.

Le catalogue constitue la référence interne utilisée par les services
métier.

`AssetRepository` prend en charge la lecture, la validation et la
sauvegarde des fiches du catalogue.

### 3.2. Données externes

Les données externes sont stockées indépendamment du catalogue.

Organisation cible :

``` text
external-data/
└── assets/
    └── <CATEGORY_PATH>/
        └── <ID_ASSET>/
            ├── scraped_data/
            │   └── <ID_ASSET>_scraping.yaml
            │
            ├── factsheets/
            │   ├── <YYYY>-<MM>_<ID_ASSET>_factsheet.pdf
            │   └── <YYYY>-<MM>_<ID_ASSET>_factsheet.yaml
            │
            └── quotes/
                └── ...
```

`<CATEGORY_PATH>` représente le chemin de catégorie relatif à la racine
du catalogue. Il est obtenu à partir de l'emplacement de la fiche de
l'actif dans le catalogue.

Les répertoires et noms de fichiers sont définis dans `config_app.yaml`.

#### Scraped data

Pour chaque actif et type de collecte, un seul fichier courant est
conservé.

Le nom du fichier est stable :

``` text
<ID_ASSET>_scraping.yaml
```

`ScrapedDataRepository` valide les nouvelles données avant leur
enregistrement. Le fichier courant est remplacé uniquement si le nouveau
document est valide et si sa date de référence est strictement plus
récente que celle du document existant.

La date utilisée pour la comparaison est :

``` yaml
market_data:
  last_updated: "YYYY-MM-DD"
```

La date `source.retrieved_at` représente la date de récupération auprès
du fournisseur. Elle ne sert pas à déterminer si les données financières
sont plus récentes.

Aucune archive de fichiers scraped n'est conservée.

#### Factsheets

Les factsheets peuvent être stockées sous leur format source, notamment
PDF, et faire l'objet d'une extraction vers un document YAML.

#### Quotes

Les quotes sont destinées au stockage des données historiques de
cotation. Elles sont indépendantes des données scraped courantes.

### 3.3. Données utilisateurs

Les données propres aux utilisateurs sont séparées des données communes.

Exemple :

``` text
external-data/
└── users/
    └── <ID_USER>/
        └── wallets/
            └── ...
```

Les wallets sont associés à un utilisateur.

Un compte est défini par l'association d'un contrat et d'un courtier :

``` text
contract + broker = account
```

Un wallet correspond à un compte lié à un utilisateur.

## 4. Configuration et résolution des chemins

### 4.1. Configuration centralisée

Le fichier `config_app.yaml` définit les chemins des ressources et leurs
caractéristiques.

Exemple simplifié :

``` yaml
data:
  catalog:
    financial:
      assets:
        format: yaml
        filename: <ID_ASSET>.yaml
        folder: data/assets
        schemas: resources/schemas/assets
        rules: resources/rules/assets

  external:
    assets:
      scraped_data:
        format: yaml
        filename: <ID_ASSET>_scraping.yaml
        folder: external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/scraped_data
        schemas: resources/schemas/assets/scraped
        rules: resources/rules/assets/scraped
```

Les autres ressources, notamment les factsheets et quotes, suivent le
même principe de configuration.

### 4.2. ConfigPathResolver

`ConfigPathResolver` centralise la résolution des chemins.

Ses principales responsabilités sont :

-   Identifier une ressource à partir de sa clé de configuration.
-   Résoudre le répertoire associé.
-   Résoudre le nom de fichier à partir d'un contexte.
-   Interpoler les variables de chemin.
-   Retourner les chemins correspondants.

Les services ne reconstruisent pas eux-mêmes les chemins définis dans la
configuration. Les repositories utilisent `ConfigPathResolver` pour
localiser les ressources dont ils ont la responsabilité.

## 5. Validation

La validation repose sur plusieurs composants complémentaires.

### 5.1. SchemaLoader

`SchemaLoader` charge les fichiers JSON Schema d'un répertoire
configuré.

Il assure notamment :

-   Le chargement des fichiers de schéma.
-   L'indexation des schémas par leur `$id`.
-   Leur indexation par nom de fichier.
-   La construction du registre permettant de résoudre les références
    `$ref`.

Le chargement est effectué à partir d'une clé de ressource définie dans
`config_app.yaml`.

Exemples :

``` python
catalog_schema_loader = SchemaLoader(
    "catalog/financial/assets",
    config,
)

scraped_schema_loader = SchemaLoader(
    "external/assets/scraped_data",
    config,
)
```

Le nom de fichier `scraped_data.schemas.yaml` peut être référencé par le
nom `scraped_data.schemas`.

Son `$id` est un identifiant distinct du nom de fichier.

### 5.2. ReferenceValidator

`ReferenceValidator` charge les référentiels métier à partir de la
configuration.

Il contrôle notamment les références suivantes :

-   `currency`
-   `gics`
-   `stock_exchange`
-   `benchmark`
-   `broker`
-   `asset_manager`

Les valeurs autorisées sont chargées en mémoire dans des ensembles.

Une même instance peut être partagée entre plusieurs `SchemaValidator`,
puisque les validations utilisent les mêmes référentiels métier.

### 5.3. SchemaValidator

`SchemaValidator` combine :

1.  La validation structurelle par JSON Schema.
2.  La validation des références métier identifiées par `x-reference`.

Il reçoit un `SchemaLoader` et un `ReferenceValidator`.

Les validations du catalogue et des données scraped utilisent deux
instances distinctes de `SchemaLoader` et de `SchemaValidator`.

Le référentiel métier peut être partagé entre ces instances.

### 5.4. JSON Schema et Pydantic

Les responsabilités sont complémentaires.

  Composant              Responsabilité
  ---------------------- --------------------------------------------
  JSON Schema            Contrôle structurel du document
  `ReferenceValidator`   Contrôle des références métier
  Pydantic               Typage et représentation des objets Python

Le JSON Schema constitue la référence structurelle des documents.

Les modèles Pydantic représentent les données dans le code Python. Ils
ne doivent pas filtrer arbitrairement les champs autorisés par le
schéma, notamment lors du stockage des données scraped.

Les données sont validées aux frontières de l'application, en
particulier lors de leur lecture et de leur écriture par les
repositories.

## 6. Cycle de traitement des données marché

Le cycle de mise à jour d'un actif repose sur deux opérations explicites
: `fetch` et `apply`.

### 6.1. Fetch

L'opération `fetch` collecte les données auprès du fournisseur configuré
pour l'actif.

Le déroulement est le suivant :

1.  `AssetService` charge l'actif via `AssetRepository`.
2.  Le service vérifie la configuration de l'agrégateur, le fournisseur
    et le symbole.
3.  `YahooFinanceAdapter` récupère les données auprès de Yahoo Finance.
4.  L'adaptateur construit le document de données scraped.
5.  `ScrapedDataRepository` valide le document.
6.  Le repository compare sa date `market_data.last_updated` avec celle
    du document existant.
7.  Le document est enregistré uniquement s'il est valide et plus
    récent.

L'opération `fetch` ne modifie jamais le catalogue.

### 6.2. Apply

L'opération `apply` intègre explicitement les données scraped dans le
catalogue.

Le déroulement est le suivant :

1.  `AssetService` charge l'actif via `AssetRepository`.
2.  Le service détermine le chemin de catégorie de l'actif.
3.  `ScrapedDataRepository` lit et valide le document scraped.
4.  Le document est converti en `AggregatedScrapedAsset`.
5.  `scraped_to_catalog.apply_external_to_catalog` applique la
    transformation vers la structure du catalogue.
6.  Le résultat est validé comme objet `Asset`.
7.  `AssetRepository` sauvegarde l'actif mis à jour.

La transformation est sélective : les valeurs externes absentes ne
remplacent pas les valeurs existantes du catalogue.

La fonction de transformation ne modifie pas le document catalogue
d'origine.

### 6.3. Responsabilités des composants

  -----------------------------------------------------------------------
  Composant                           Responsabilité dans le cycle
  ----------------------------------- -----------------------------------
  `AssetService`                      Orchestration de `fetch` et `apply`

  `YahooFinanceAdapter`               Collecte et adaptation des données
                                      fournisseur

  `ScrapedDataRepository`             Lecture, validation et persistance
                                      des données scraped

  `AssetRepository`                   Lecture, validation et persistance
                                      du catalogue

  `scraped_to_catalog`                Transformation des données scraped
                                      vers la structure catalogue
  -----------------------------------------------------------------------

## 7. Injection de dépendances et assemblage

La construction des composants est centralisée dans
`bootstrap/dependencies.py`.

La fonction `build_asset_service(config)` :

1.  Construit le `ReferenceValidator` partagé.
2.  Construit les loaders et validateurs du catalogue.
3.  Construit `AssetRepository`.
4.  Construit les loaders et validateurs des données scraped.
5.  Construit `ScrapedDataRepository`.
6.  Construit `YahooFinanceAdapter`.
7.  Injecte ces dépendances dans `AssetService`.

Le service ne connaît donc pas les détails de construction de ses
dépendances.

Cette organisation facilite les tests unitaires : les repositories et
les adaptateurs peuvent être remplacés par des mocks ou des
implémentations alternatives.

## 8. Vue des dépendances

``` text
                 CLI
                  |
                  v
              Bootstrap
                  |
          build_asset_service()
                  |
                  v
              AssetService
             /      |      \
            /       |       \
           v        v        v
 AssetRepository  ScrapedDataRepository  YahooFinanceAdapter
        |                  |                    |
        v                  v                    v
    Catalogue        Données scraped       Yahoo Finance
```

Les validateurs et le résolveur de chemins sont utilisés par les
repositories lors de leurs opérations. Ils sont construits et assemblés
par le bootstrap.

Cette architecture sépare l'orchestration applicative, l'accès aux
données et la communication avec les fournisseurs externes.


## 9. Workflow de collecte : fetch

La collecte des données financières est pilotée par `AssetService`.

Elle permet de récupérer les données d'un fournisseur externe et de les enregistrer dans le répertoire des données collectées, sans modifier le catalogue.

### 9.1. Flux de traitement

```text
CLI
 |
 v
AssetService.fetch_market_data()
 |
 v
AssetRepository
 | Lecture et validation de la fiche Asset
 v
Identification du fournisseur et du symbole
 |
 v
YahooFinanceAdapter
 | Collecte auprès de Yahoo Finance
 | Construction du payload
 v
AssetRepository
 | Récupération du chemin de catégorie
 v
ScrapedDataRepository
 | Validation du payload
 | Vérification de l'identifiant de l'actif
 | Comparaison des dates de référence
 | Écriture atomique
 v
Fichier scraped courant
```

### 9.2. Responsabilités

**`AssetService`**

- Charge et valide l'actif depuis le catalogue.
- Identifie le fournisseur configuré et le symbole à interroger.
- Vérifie que le fournisseur est pris en charge.
- Déclenche la collecte auprès de l'adaptateur.
- Construit le payload à partir du résultat de la collecte.
- Récupère le chemin de catégorie de l'actif.
- Transmet les données à `ScrapedDataRepository`.

**`YahooFinanceAdapter`**

- Interroge Yahoo Finance.
- Récupère les données financières disponibles.
- Convertit la réponse du fournisseur vers les modèles de données collectées.
- Construit le document scraped attendu.

**`ScrapedDataRepository`**

- Détermine le chemin de stockage à partir de la configuration et du contexte de l'actif.
- Vérifie la cohérence de l'identifiant de l'actif.
- Valide le payload avec le mécanisme de validation configuré.
- Lit les données existantes lorsqu'elles sont présentes.
- Compare les dates de référence.
- Écrit le fichier courant lorsque les conditions de remplacement sont satisfaites.

### 9.3. Politique de remplacement

Le fichier courant est remplacé uniquement si :

- Le nouveau payload est valide.
- L'identifiant de l'actif est cohérent.
- La date `market_data.last_updated` est strictement supérieure à celle du fichier courant.

La date `source.retrieved_at` indique le moment de récupération des données, mais n'intervient pas dans la comparaison de fraîcheur.

Si les dates sont égales ou si la nouvelle collecte est plus ancienne, le fichier existant est conservé.

Si le fichier existant est illisible ou invalide, une nouvelle collecte valide peut le remplacer.

Le remplacement doit être atomique afin d'éviter de laisser un fichier partiellement écrit.

Le fichier existant ne doit jamais être supprimé ou modifié avant que le nouveau payload ait été validé. L'écriture utilise un fichier temporaire situé dans le même répertoire, puis `os.replace()`.

---

## 10. Workflow d'intégration : apply

L'intégration est une opération distincte de la collecte.

Elle est pilotée par `AssetService` et s'appuie sur `ScrapedDataRepository`, `AssetRepository` et le module de transformation métier `scraped_to_catalog`.

Seule cette opération permet de reporter explicitement les données externes dans le catalogue.

### 10.1. Flux de traitement

```text
CLI
 |
 v
AssetService.apply_scraped_data()
 |
 v
AssetRepository
 | Lecture de la fiche Asset
 | Récupération du chemin de catégorie
 v
ScrapedDataRepository
 | Lecture et validation
 v
AggregatedScrapedAsset
 |
 v
scraped_to_catalog
 | Transformation sélective
 v
Structure Asset
 |
 v
Asset
 | Validation du modèle
 v
AssetRepository
 | Validation et sauvegarde
 v
Catalogue mis à jour
```

### 10.2. Transformation des données

Les données scraped et le catalogue n'utilisent pas nécessairement les mêmes noms de champs ni les mêmes unités.

La transformation est centralisée dans `scraped_to_catalog`.

Exemples de correspondances :

| Donnée scraped | Donnée catalogue |
|---|---|
| `market_data.indicative.price` | Prix indicatif |
| `market_data.indicative.nav` | NAV |
| `market_data.indicative.currency` | Devise de la donnée indicative |
| `market_data.indicative.aum` | Actifs sous gestion |
| `market_data.indicative.market_cap` | Capitalisation boursière |
| `market_data.last_updated` | Date de mise à jour des données marché |

Les unités de capitalisation du catalogue sont calculées pendant cette transformation :

- `aum_unit` pour les actifs sous gestion ;
- `mc_unit` pour la capitalisation boursière.

Les données scraped peuvent contenir simultanément `aum` et `market_cap`, ou ne contenir aucun des deux. Le schéma ne cherche pas à imposer une exclusivité entre ces champs.

Les données collectées conservent leur distinction sémantique : `nav` n'est pas assimilé automatiquement à `price`, et `aum` n'est pas assimilé à `market_cap`.

### 10.3. Règles métier

La transformation ne se limite pas à une copie mécanique des champs.

Elle applique les règles de mise à jour du catalogue, notamment :

- Actualiser les données de marché à partir des données collectées.
- Ne mettre à jour que les champs pour lesquels une donnée exploitable est disponible.
- Conserver les informations internes qui ne sont pas concernées par la mise à jour.
- Éviter d'écraser les informations descriptives déjà renseignées lorsqu'elles ne font pas partie du périmètre de transformation.
- Calculer les unités nécessaires à la représentation des montants.
- Produire une structure conforme au modèle `Asset`.

Le résultat est validé avec le modèle Pydantic `Asset` avant sa sauvegarde par `AssetRepository`.

Le catalogue n'est donc modifié qu'après validation de la structure résultante.

---

## 11. Gestion des fichiers YAML

Le module `common.yaml_io` centralise les opérations techniques de lecture et d'écriture YAML.

Il assure notamment :

- Le chargement de documents YAML.
- Le contrôle du type de document lorsque le traitement attend un mapping.
- La conservation des dates sous forme de chaînes lors du chargement.
- La sérialisation des mappings YAML.

Les repositories utilisent ces fonctions pour assurer la persistance des données :

- `AssetRepository` pour les fiches du catalogue.
- `ScrapedDataRepository` pour les données collectées.

Pour les données scraped, l'écriture utilise un mécanisme atomique basé sur un fichier temporaire situé dans le même répertoire, puis un remplacement avec `os.replace()`.

Cette précaution évite qu'une interruption de l'écriture laisse un document incomplet à l'emplacement du fichier courant.

Les opérations YAML restent des mécanismes techniques : les règles de persistance, de validation et de remplacement relèvent des repositories.

---

## 12. Principes de dépendance

Les dépendances entre les composants doivent respecter les règles suivantes :

- La CLI dépend des services.
- Les services orchestrent les repositories, les adaptateurs et les composants métier.
- Les repositories gèrent la persistance et la validation des données qu'ils manipulent.
- Les adaptateurs encapsulent les communications avec les fournisseurs externes.
- Les repositories utilisent `ConfigPathResolver` pour résoudre les ressources déclarées dans la configuration.
- Les composants de validation ne dépendent pas des services.
- Les modèles ne construisent pas eux-mêmes les chemins des ressources.
- Les fonctions de transformation métier ne réalisent pas directement les opérations de stockage.
- Le bootstrap construit les composants et injecte leurs dépendances.

Le service constitue le point de coordination des opérations métier, sans prendre en charge directement les détails techniques de stockage ou de communication externe.

---

## 13. Points d'attention pour les évolutions

Les évolutions de l'application doivent préserver les principes suivants :

1. Toute nouvelle ressource doit être déclarée dans `config_app.yaml`.
2. Les chemins ne doivent pas être codés en dur dans les services ou les modèles.
3. Les nouvelles structures de données persistées doivent disposer de schémas JSON adaptés.
4. Les données scraped doivent rester distinctes des données du catalogue.
5. Toute intégration des données externes au catalogue doit passer par le workflow `apply`.
6. Les validations doivent être effectuées avant la sauvegarde.
7. Les transformations entre structures doivent être centralisées.
8. Les adaptateurs doivent conserver des responsabilités techniques précises.
9. Les repositories doivent rester responsables de la persistance et de la cohérence des données stockées.
10. Le bootstrap doit centraliser la construction et l'injection des dépendances.

Cette organisation permet de faire évoluer les fournisseurs, les formats de données et les traitements sans remettre en cause la séparation fondamentale entre collecte externe et référentiel métier.
