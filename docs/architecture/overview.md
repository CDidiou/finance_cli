# Patrimonia — Architecture Overview

## 1. Introduction

Patrimonia is a Python command-line application for managing and analysing personal and family financial assets.

Its purpose is to centralise financial information, organise asset and account references, collect external financial data, manage user portfolios and produce financial and wealth analyses.

The architecture is designed around a few principles:

- Clear separation of responsibilities.
- Separation between reference data, user input data and calculated results.
- Validation of data before it is used.
- Preservation of original user data.
- Reusable business logic independent of the command-line interface.
- Controlled access to external providers.
- Simple, traceable and regenerable calculations.

Patrimonia is designed for personal and family use. Its architecture favours reliability, clarity and maintainability over unnecessary technical complexity.

## 2. Architectural Principles

### 2.1 Separation of Data Domains

Patrimonia organises its data into three distinct domains.

| Domain | Location | Purpose |
|---|---|---|
| Reference data | `data/` | Shared financial catalogue: assets, categories, account and contract definitions |
| User input data | `external-data/.../input/` | User-managed information, including transactions and official balances |
| Calculated data | `external-data/.../calculated/` | Derived and regenerable results produced by Patrimonia |

These domains have different responsibilities and write policies.

**Reference data**

The financial catalogue is maintained by the application administrator. It can be enriched through controlled operations using validated external information.

**User input data**

User input files are the original sources of personal financial information. They are managed by users and are never modified by Patrimonia.

**Calculated data**

Calculated data is produced from validated reference and user data. It is stored separately from its sources and can be regenerated.

This separation protects original information and makes the origin of each result easier to understand.

### 2.2 Separation of Responsibilities

The application is organised into layers with distinct responsibilities:

- The CLI handles user interaction.
- Bootstrap assembles application components and injects dependencies.
- Services orchestrate application operations.
- Repositories manage data access, validation and persistence.
- Adapters isolate external providers and technical integrations.
- Models represent business concepts and structured data.
- Validation components implement structural and business validation.
- Resource files define schemas, rules and other application resources.
- Configuration centralises application settings and resource locations.

No application service should directly manage YAML or Excel file paths or perform low-level persistence operations.

### 2.3 Validation Before Use

Data is validated before being used in application processing.

The validation pipeline distinguishes three stages:

1. **JSON Schema validation** checks the structure, required fields, types and supported formats.
2. **Business rules validation** checks domain-specific constraints and consistency.
3. **Pydantic model construction** creates typed application representations from validated data.

JSON Schema and business rules have complementary responsibilities. Pydantic models provide typed representations and can enforce additional model-level constraints.

Validation is orchestrated at the repository boundary, rather than being duplicated throughout the application.

For catalogue definitions, YAML loading and inheritance resolution take place before schema validation.

### 2.4 Regenerable Calculated Results

Calculated data is not an independent source of truth.

It is derived from validated source data and can be regenerated.

For example, enriched transactions are rebuilt completely from validated transaction inputs whenever a command triggers that calculation.

The previous enriched result is not used as an incremental processing base.

This avoids incremental update logic and reduces the risk of stale or inconsistent derived data.

## 3. Application Structure

The Python package is located under `src/finance_cli/`.

The main architectural components are organised as follows:

| Component | Responsibility |
|---|---|
| `cli` | Defines commands, options and command-line interaction |
| `bootstrap` | Creates and assembles application dependencies |
| `services` | Implements application workflows and orchestrates operations |
| `repositories` | Encapsulates data access, validation and persistence |
| `adapters` | Connects to external providers and performs technical integrations |
| `models` | Defines business models and external data representations |
| `validation` | Implements structural and business validation |
| `config` | Loads application configuration and resolves resources |
| `common` | Provides shared technical utilities and transformations |
| `resources` | Contains schemas, rules, templates, styles and other application resources |

### 3.1 CLI

The CLI is the entry point for users and administrators.

It exposes commands for operations such as:

- configuration checks;
- listing and displaying users, accounts and assets;
- wallet consultation;
- transaction and balance validation;
- external financial data collection;
- catalogue enrichment;
- financial calculations and reporting.

The CLI delegates application operations to services. It does not implement business calculations or directly access data files.

The intended user-facing command is `patrimonia`.

### 3.2 Bootstrap

Bootstrap is responsible for constructing the application dependency graph.

It loads the application configuration and creates the required repositories, adapters and services.

Dependencies are injected into services during application assembly.

This keeps services independent of concrete storage implementations and external providers.

Services do not construct their own dependencies.

### 3.3 Services

Services orchestrate application use cases.

Examples include:

- asset data collection and catalogue enrichment;
- factsheet extraction and enrichment;
- transaction validation and enrichment;
- balance calculation;
- wealth evolution generation;
- dashboard generation.

Services coordinate operations but delegate file access, validation and persistence to the appropriate components.

They should not implement low-level file handling or independently resolve storage paths.

### 3.4 Repositories

Repositories encapsulate access to the application's data.

They are responsible for the relevant storage operations, including:

- locating data using the application configuration;
- reading structured data;
- coordinating schema and business rule validation;
- constructing validated application models;
- persisting validated data;
- replacing calculated results when a new calculation succeeds.

Repositories hide the underlying storage format from services.

The repository is the data-access boundary for catalogue and user data. Dedicated validation components are used by repositories to implement the validation pipeline.

### 3.5 Adapters

Adapters isolate external communication and technical integrations.

Examples include:

- financial provider adapters, such as Yahoo Finance;
- external service integrations;
- format-specific operations where a dedicated adapter is justified.

Adapters prevent provider-specific protocols and technical details from spreading throughout application services.

Catalogue loading, inheritance resolution, validation and persistence belong to repositories and their supporting components. They are not responsibilities of a separate catalogue adapter.

### 3.6 Models

Models represent business concepts independently of their physical storage.

Important concepts include:

- `Asset`: a financial instrument or asset definition;
- `Account`: a financial account or contract definition;
- `Wallet`: a user's portfolio associated with an account;
- `Transaction`: an individual financial operation;
- `Balance`: a portfolio valuation at a given date;
- external data models representing information collected from providers.

A model should not be responsible for resolving arbitrary filesystem paths or implementing repository persistence.

Models represent validated application data and domain concepts, not the details of YAML or Excel storage.

### 3.7 Validation and Resources

Validation code and validation resources are kept separate.

The `validation/` package contains Python components responsible for loading and evaluating schemas and business rules.

The `resources/` directory contains the corresponding resource files, including:

- `schemas/`: JSON Schema definitions;
- `rules/`: business validation rules;
- `templates/`: document and dashboard templates;
- `styles/`: presentation resources.

This separation allows validation logic to evolve independently from the definitions it evaluates.

### 3.8 Configuration

The `config/` package handles application configuration and resource resolution.

Configuration is loaded during application startup and passed to components that need it.

Repositories and services use injected configuration or resolved resources rather than independently loading the global configuration.

This centralises path resolution and keeps application components independent of the physical project layout.

## 4. Data Architecture

### 4.1 Reference Catalogue

The `data/` directory contains the shared financial catalogue.

It includes:

- asset categories and asset definitions;
- financial instruments;
- account and contract definitions;
- broker-specific implementations;
- supporting reference data.

Catalogue entries are stored primarily as YAML files.

Definitions can inherit from other definitions through the `extends` property.

Inheritance follows these rules:

- Paths are relative to the YAML file declaring `extends`.
- Child properties override parent properties.
- Nested objects are replaced as a whole; recursive merging is not performed.

This provides reusable definitions while allowing broker-specific or instrument-specific variations.

The catalogue contains reference and descriptive information. Historical quotes and intermediate external collection data are stored separately.

### 4.2 External Financial Data

External financial data is kept separate from the reference catalogue.

It includes different types of resources with distinct purposes:

| Data type | Purpose |
|---|---|
| Scraped data / market data | Intermediate information collected from external providers |
| Factsheets | Source documents and information extracted from financial product documents |
| Quotes | Historical market prices used for financial valuation |

External data is collected and processed through resource-specific workflows.

The main workflows are:

| Resource | Workflow |
|---|---|
| Factsheets | `extract` → `upgrade` |
| Market data | `retrieve` → `upgrade` |
| Quotes | `retrieve` |

Collecting external data does not automatically modify the reference catalogue.

For market data and factsheets, enrichment is a separate operation that validates and integrates selected information into the catalogue.

Quotes are different: they are stored separately from the catalogue and are used as valuation data. They are shared across users and organised by asset and year.

### 4.3 User Data

User information is stored under:

```text
external-data/users/
```

Each user has an identity file and references to their wallets.

A wallet is associated with an account definition through `account_ref`.

Held financial assets can reference catalogue entries through `asset_ref`.

These references use paths relative to the application's data directory.

User data is kept separate from the shared financial catalogue.

This allows multiple users to share the same financial reference definitions while keeping their personal financial information independent.

### 4.4 Input and Calculated Data

Within a user's data directory, Patrimonia distinguishes original input files from calculated results.

A simplified wallet structure is:

```text
external-data/
└── users/
    └── <USER_ID>/
        ├── <USER_ID>.yaml
        ├── input/
        │   └── <WALLET_ID>/
        │       ├── transactions/
        │       │   └── <YEAR>_<WALLET_ID>_tx.xlsx
        │       └── balances/
        │           └── <DATE>_<WALLET_ID>_balance.xlsx
        └── calculated/
            └── <WALLET_ID>/
                ├── transactions_enriched/
                │   └── <YEAR>_<WALLET_ID>_tx_enriched.yaml
                └── balances/
                    └── <DATE>_<WALLET_ID>_balance.xlsx
```

This structure illustrates the separation between user-managed source data and calculated results.

User input files include:

- transaction workbooks;
- official balance workbooks.

Calculated wallet data includes:

- enriched transactions in YAML;
- calculated balances in Excel.

Calculated data is regenerated from validated source data. It does not replace the original input files.

Actual filenames and directory resolution are controlled by the application configuration.

User-level calculated resources, such as wealth evolution and dashboards, may be organised separately from wallet-level results.

## 5. Configuration and Resources

The application configuration is centralised in `config/config_app.yaml`.

It defines:

- application settings;
- logging configuration;
- catalogue locations;
- external data locations;
- user input and calculated data locations;
- supported file formats and naming conventions;
- JSON Schema locations;
- business rule locations;
- other application resource locations, including dashboard resources where configured.

The configuration is loaded during application startup and passed to components that require it.

Components such as models and readers should not independently reload the global application configuration.

This keeps resource resolution consistent across the application.

See [CLI Configuration](../cli/configuration.md) for configuration details.

## 6. Main Application Workflows

### 6.1 Asset Data Collection and Catalogue Enrichment

Asset data workflows depend on the type of external information being processed.

**Factsheets**

Factsheet processing follows two distinct steps:

1. `extract` obtains structured information from a source document, typically a PDF.
2. `upgrade` validates and integrates selected information into the corresponding catalogue definition.

Extraction produces intermediate data that can be checked and corrected before integration.

**Market data**

Market data processing follows two distinct steps:

1. `retrieve` retrieves information from an external provider.
2. `upgrade` validates and integrates selected information into the asset catalogue.

The retrieve operation:

1. Loads the relevant asset definition.
2. Identifies the configured provider and provider symbol.
3. Calls the appropriate provider adapter.
4. Builds an intermediate external data document.
5. Delegates validation and persistence to the relevant repository.

The catalogue is not modified by `retrieve`.

The enrichment operation:

1. Loads the asset and the relevant external data.
2. Validates the external data.
3. Transforms the selected information into catalogue data.
4. Validates the resulting asset definition.
5. Persists the updated catalogue entry through `AssetRepository`.

**Quotes**

Quotes are collected through `retrieve` and stored separately from the catalogue.

They are shared across users and organised by asset and year. They are used for financial valuation and are not integrated into the asset catalogue through `upgrade`.

### 6.2 Transaction Processing

Transactions are entered by users in Excel files stored under the wallet's `input/transactions/` directory.

The workbook contains:

- a `header` worksheet with metadata;
- a `data` worksheet with transaction records.

The input is validated using JSON Schemas and business rules before processing.

Patrimonia then generates `transactions_enriched` as a YAML result.

The enrichment process is a **complete recalculation from validated source data** whenever a command triggers it.

The existing calculated result is not used as an incremental processing base.

The generated YAML is a derived result, not an independent source of truth.

It is used as an input for subsequent wallet balance calculations.

### 6.3 Balance Processing

Patrimonia distinguishes official balances from calculated balances.

**Official balance**

An official balance is an Excel file stored under the wallet's `input/balances/` directory.

It is the reference state used for subsequent calculations.

It can originate from the broker or from a balance previously calculated by Patrimonia and explicitly copied into the input directory by the user.

Its `provenance` metadata indicates `broker` or `patrimonia`.

Official balance files are user-managed source data and are never modified by Patrimonia.

**Calculated balance**

A calculated balance is an Excel result stored under `calculated/balances/`.

It is produced for a user-selected date using:

- the latest available official balance;
- validated enriched transactions after that balance, up to the requested calculation date.

A calculated balance does not automatically become official.

The user decides whether to promote it to official status by copying it into the input directory.

This preserves user control over the reference state of the portfolio.

### 6.4 Wealth Evolution

Wealth evolution represents a time series of the value of a wallet or a consolidated user portfolio.

It is a derived result that can be regenerated from the relevant financial data.

The intended data organisation is YAML, with files organised by year and evolution available at wallet and user level.

This section describes the wealth evolution data concept and its intended organisation. The availability of the complete generation workflow depends on the current application implementation.

### 6.5 Dashboards

Dashboards provide visual representations of financial information and wealth evolution.

The dashboard generation architecture uses Plotly to produce static HTML documents that can be viewed in a web browser.

A dashboard can be accompanied by a YAML metadata file containing information such as:

- generation date;
- calculation scope;
- references to source data.

The metadata provides source traceability without imposing an artificial data structure on the HTML document.

The dashboard generation design is described separately in [Dashboard Generation](dashboard-generation.md). Its architecture should not be interpreted as proof that every dashboard workflow is already implemented.

## 7. Validation and Data Integrity

Validation is applied at the relevant boundaries of the application.

### 7.1 Validation Pipeline

For catalogue definitions, the processing sequence is:

1. Load the YAML document.
2. Resolve inheritance through `extends`, where applicable.
3. Validate the resulting structure using JSON Schema.
4. Evaluate the applicable business rules.
5. Construct the corresponding Pydantic model.

For user transaction and balance files, the processing sequence is adapted to their storage format:

1. Read the source workbook.
2. Extract the relevant data.
3. Validate its structure using JSON Schema.
4. Validate business constraints.
5. Make validated data available to application processing.

Invalid source data must not be used to produce a new calculated result.

Catalogue data, external data and user input data have distinct schemas and business rules, reflecting their different roles and structures.

### 7.2 Schema and Business Rule Validation

JSON Schema defines structural constraints, including:

- required fields;
- data types;
- formats;
- allowed values;
- references to other definitions.

Patrimonia uses JSON Schema Draft 2020-12.

The `x-reference` keyword is a Patrimonia-specific extension used to express cross-reference validation. It is not part of the standard JSON Schema specification.

Business rules define additional domain constraints that cannot be expressed adequately through structural schemas alone.

Rules are evaluated only after successful schema validation.

Pydantic models then provide typed representations of the validated data.

### 7.3 Source Traceability

Calculated results may include metadata describing their generation and source data.

Depending on the result type, metadata can include:

- generation timestamp;
- calculation date;
- calculation scope;
- user or wallet identifier;
- application name and version;
- source references;
- source data fingerprints and their roles.

Where source fingerprints are implemented, they are calculated from normalised business data rather than raw Excel file bytes.

This makes source traceability less dependent on irrelevant workbook changes, such as formatting.

The objective is to identify changes in source data and understand which inputs were used to generate a result, without implementing a complex reproducibility framework.

The exact metadata and fingerprint implementation depends on the calculated resource.

## 8. Command-Line Interface Conventions

The CLI follows a common command structure:

```text
patrimonia <RESOURCE> [--id <RESOURCE_ID>] <ACTION> [OPTIONS]
```

Collections use plural resource names, while individual objects use singular resource names.

The main public action vocabulary includes:

- `list`: list a collection;
- `show`: display an object or result;
- `check`: perform a diagnostic or validation;
- `calculate`: generate calculated results;
- `extract`: extract information from source documents;
- `retrieve`: retrieve external data;
- `upgrade`: integrate validated information into the catalogue.

Not every action applies to every resource.

The CLI is an interface to application services, not a separate implementation of business logic.

See [CLI Conventions](../cli/conventions.md) and the resource-specific CLI documentation for command details.

## 9. Testing Strategy

Tests are organised separately from the application package under `tests/`.

The test suite should cover the main architectural layers and application workflows.

An illustrative organisation is:

```text
tests/
├── conftest.py
├── test_models/
├── test_validation/
├── test_repositories/
├── test_adapters/
├── test_services/
└── test_cli/
```

Tests use temporary directories and controlled YAML, Excel and external provider fixtures.

The main testing objectives are:

- verify model behaviour and domain constraints;
- verify YAML loading, inheritance and validation;
- verify repository access and persistence;
- verify external provider integrations using controlled responses;
- verify transaction enrichment and balance calculation;
- verify CLI commands and their outputs;
- ensure that source data is not modified by application processing.

End-to-end tests can additionally verify complete workflows, from user input files to calculated portfolio results.

This structure is an architectural recommendation and does not imply that every directory or test module already exists.

See [Testing Strategy](../development/testing.md).

## 10. Architectural Boundaries and Evolution

Patrimonia is designed to evolve without compromising its core data principles.

Potential extensions include:

- additional financial providers;
- new asset categories and instruments;
- additional account and contract definitions;
- richer portfolio valuation;
- more detailed historical analysis;
- consolidated family wealth analysis;
- additional dashboard and reporting capabilities.

These extensions should follow the existing separation of responsibilities.

New providers should be introduced through adapters. New application workflows should be orchestrated by services. New data structures should be defined through models and validation resources.

The application should remain proportionate to its intended personal and family use.

The architecture favours explicit workflows, validated data and regenerable results over unnecessary infrastructure or complex processing mechanisms.

## 11. Summary

Patrimonia is built around three complementary data domains:

1. **Reference data**: the shared financial catalogue.
2. **User input data**: the original sources of personal financial information.
3. **Calculated data**: validated, traceable and regenerable results.

Its software architecture separates command-line interaction, application orchestration, data access, external communication, business models and validation.

The central architectural rule is simple:

**Preserve original data, validate before processing, and keep calculated results separate and regenerable.**

This principle provides the foundation for a reliable and maintainable family wealth management application.