# Patrimonia — Project Structure

## 1. Introduction

This document describes the physical organisation of the Patrimonia project.

The project structure separates application source code, configuration, validation resources, financial data, external data and tests.

The main objectives are:

- Keep application code independent from business data.
- Organise components according to their responsibilities.
- Separate shared reference data from user-specific information.
- Centralise configuration and resource definitions.
- Facilitate testing, maintenance and future extensions.

Patrimonia uses a Python `src` layout and Poetry for dependency management and packaging.

## 2. Repository structure

The project follows this general organisation:

```text
finance-cli/
│
├── src/
│   └── finance_cli/
│       ├── cli/
│       ├── bootstrap/
│       ├── services/
│       ├── repositories/
│       ├── adapters/
│       ├── models/
│       ├── validation/
│       ├── config/
│       └── common/
│
├── tests/
│   ├── conftest.py
│   ├── test_models/
│   ├── test_readers/
│   └── test_cli/
│
├── config/
│   └── config_app.yaml
│
├── data/
│   ├── contracts/
│   ├── assets/
│   └── economy/
│
├── external-data/
│   ├── assets/
│   └── users/
│
├── resources/
│   ├── schemas/
│   ├── rules/
│   ├── templates/
│   └── styles/
│
├── pyproject.toml
├── poetry.lock
└── README.md
```

This tree represents the main architectural organisation. Some subdirectories are created or populated according to the configuration and the data available.

## 3. Application source code

The Python application is located under:

```text
src/finance_cli/
```

The `src` layout keeps the installable package separate from project-level configuration and data.

### 3.1 `cli/`

Contains the command-line interface.

Responsibilities:

- Define commands and command groups.
- Parse arguments and options.
- Display results and diagnostics.
- Delegate operations to application services.

The CLI must not contain business calculations, direct YAML persistence or provider-specific communication logic.

### 3.2 `bootstrap/`

Contains application assembly and dependency injection.

Responsibilities:

- Load the application configuration.
- Instantiate repositories and adapters.
- Construct application services.
- Inject dependencies into services.
- Initialise the application context.

Bootstrap is the composition point of the application.

### 3.3 `services/`

Contains application services and use-case orchestration.

Responsibilities:

- Coordinate application operations.
- Apply business workflows.
- Call repositories and adapters through their defined interfaces.
- Manage the sequence of validation, transformation and calculation operations.

Services do not construct their own infrastructure dependencies and do not directly manage filesystem paths.

### 3.4 `repositories/`

Contains data access and persistence components.

Responsibilities:

- Locate and load data.
- Encapsulate storage operations.
- Apply structural and business validation.
- Persist validated catalogue data and calculated results.
- Manage replacement of existing derived data.

Repositories hide storage details from application services.

### 3.5 `adapters/`

Contains integrations with external providers and storage-specific implementations.

Examples include:

- Financial data provider adapters.
- YAML adapters for resolving account definitions and inheritance.
- Excel readers for user transactions and balances.

Adapters isolate external interfaces and file-format-specific operations from business logic.

### 3.6 `models/`

Contains the application's business and data models.

Examples include:

- `Account`
- `Wallet`
- `Transaction`
- `Balance`
- Asset catalogue models.
- Scraped and external data models.

Models represent business concepts independently of their physical storage.

### 3.7 `validation/`

Contains validation-related application components.

It provides the mechanisms used to validate data against the schemas and business rules defined in the project resources.

Validation distinguishes structural conformity from business consistency.

### 3.8 `config/`

Contains configuration loading and resource resolution components.

Responsibilities:

- Load application configuration.
- Interpret configured data locations.
- Resolve resource paths.
- Provide configuration information to components that need it.

The global configuration is loaded during application startup and passed to dependent components.

### 3.9 `common/`

Contains shared technical utilities and transformations.

Examples include:

- Shared data transformations.
- Common normalisation functions.
- Hashing utilities.
- Reusable technical helpers.

This package should remain focused on genuinely shared functionality and should not become a repository for unrelated application logic.

## 4. Tests

Tests are located in the top-level `tests/` directory.

The test structure follows the main application responsibilities:

```text
tests/
├── conftest.py
├── test_models/
│   ├── test_account.py
│   ├── test_wallet.py
│   └── test_transaction.py
├── test_readers/
│   └── test_transaction_excel_reader.py
└── test_cli/
    ├── test_account_commands.py
    └── test_wallet_commands.py
```

### 4.1 `conftest.py`

Contains shared pytest fixtures.

Examples:

- Temporary directories.
- Test configuration.
- Sample YAML files.
- Sample Excel workbooks.
- Reusable test objects.

### 4.2 `test_models/`

Tests business model behaviour, construction and data consistency.

### 4.3 `test_readers/`

Tests file readers and format-specific input processing.

For example, transaction Excel reader tests verify:

- Workbook structure.
- `header` and `data` worksheets.
- Metadata extraction.
- Transaction data loading.
- Data validation.

### 4.4 `test_cli/`

Tests command-line behaviour, including command execution, options, output and error handling.

Tests should use temporary data and controlled fixtures rather than modifying real financial data.

## 5. Configuration directory

The top-level `config/` directory contains application configuration files.

Main configuration:

```text
config/
└── config_app.yaml
```

`config_app.yaml` centralises:

- Application settings.
- Logging configuration.
- Catalogue locations.
- External data locations.
- User input and calculated data locations.
- File formats and naming conventions.
- Schema and business rule locations.
- Dashboard templates and styles.

Configuration defines where resources are located and how they are organised.

Application components should receive configuration through dependency injection rather than independently loading the global configuration.

## 6. Reference data directory

The `data/` directory contains the shared financial catalogue.

```text
data/
├── contracts/
├── assets/
└── economy/
```

### 6.1 `contracts/`

Contains financial account and contract definitions.

Examples include:

- PEA.
- LDDS.
- Assurance-vie.
- Other financial account types.

Broker-specific implementations are stored in an `implementations/` subdirectory associated with the relevant contract.

### 6.2 `assets/`

Contains asset categories and individual financial instrument definitions.

The catalogue is organised by asset category.

Examples include:

- Savings accounts.
- Mutual funds.
- ETFs.
- ETCs.
- Euro-denominated life insurance funds.
- Other financial instruments.

Each category contains its category definition. Concrete instruments are stored under the `implementations/` directory of the relevant category.

Specialised categories can inherit from parent categories using `extends`.

### 6.3 `economy/`

Contains shared economic reference data used by financial analysis and other application features.

The exact contents depend on the reference datasets maintained by the project.

## 7. External data directory

The `external-data/` directory contains data collected from external providers and data specific to application users.

```text
external-data/
├── assets/
└── users/
```

### 7.1 `assets/`

Contains external information associated with catalogue assets.

Examples include:

- Scraped financial data.
- Historical quotes.
- Original PDF factsheets.
- Extracted factsheet information.

External data is kept separate from the authoritative asset catalogue.

The `fetch` operation collects and validates external information. The `apply` operation is responsible for controlled updates to the catalogue.

### 7.2 `users/`

Contains user profiles, wallets, original input files and calculated results.

Each user has a dedicated directory:

```text
external-data/users/
└── USER001/
    ├── USER001.yaml
    ├── input/
    │   └── W001/
    │       ├── transactions/
    │       └── balances/
    └── calculated/
        ├── global/
        └── W001/
            ├── transactions/
            ├── balances/
            ├── W001_evolution.yaml
            ├── W001_dashboard.html
            └── W001_dashboard.meta.yaml
```

The actual file names and directory locations are resolved through `config_app.yaml`.

#### Input data

Contains original user-managed information:

- User profiles.
- Transaction workbooks.
- Official balance workbooks.

Patrimonia reads and validates these files but does not modify them.

#### Calculated data

Contains results generated by Patrimonia:

- Enriched transactions.
- Calculated balances.
- Wallet and user wealth evolution.
- HTML dashboards and companion metadata files.

Calculated data is derived from validated inputs and can be regenerated.

## 8. Resources directory

The `resources/` directory contains supporting resources used by application components.

```text
resources/
├── schemas/
├── rules/
├── templates/
└── styles/
```

### 8.1 `schemas/`

Contains JSON Schema definitions.

Schemas are organised according to the data domains they validate.

Examples:

- Asset catalogue schemas.
- Scraped asset schemas.
- Contract schemas.
- User schemas.
- Wallet schemas.
- Calculated result schemas.

Common schemas can be shared through the `common/` subdirectory.

### 8.2 `rules/`

Contains business validation rules.

Rules complement JSON Schema validation by checking domain-specific constraints and relationships.

They are organised according to the relevant data domains.

### 8.3 `templates/`

Contains templates used to generate calculated documents, particularly HTML dashboards.

### 8.4 `styles/`

Contains visual resources, including stylesheets used by generated dashboards.

## 9. Project configuration and packaging

### `pyproject.toml`

Defines project metadata, package configuration, dependencies and development tools.

Patrimonia uses Poetry for dependency management and packaging.

The application requires Python `^3.12`.

Main application dependencies include:

| Dependency | Purpose |
|---|---|
| `click` | Command-line interface |
| `pyyaml` | YAML processing |
| `openpyxl` | Excel processing |
| `pypdf` | PDF reading |
| `yfinance` | Yahoo Finance integration |
| `curl_cffi` | HTTP communication |
| `jsonschema` | JSON Schema validation |
| `referencing` | JSON Schema reference resolution |
| `python-dotenv` | Environment variable loading |

### `poetry.lock`

Locks the resolved dependency versions to support consistent project installations.

### `README.md`

Provides the project introduction and entry points to the documentation.

## 10. Naming and organisation conventions

Patrimonia follows a consistent set of conventions.

### 10.1 Python code

- Package and module names use lowercase `snake_case`.
- Classes use `PascalCase`.
- Functions and methods use `snake_case`.
- Tests follow the `test_*.py` naming convention.

### 10.2 YAML data

- Field names use English `snake_case`.
- Each record starts with a stable identifier.
- Users, wallets, contracts and categories use `id`.
- Financial instruments use `isin` when available.
- Instruments without an ISIN use `id`.

### 10.3 References

References between YAML records use paths relative to the configured data root.

For example:

```yaml
account_ref: contracts/LDDS/implementations/la-banque-postale.yaml
```

An asset held in a wallet can be referenced as:

```yaml
asset_ref: assets/mutual_funds/opcvm/fcp/implementations/FR0007018239.yaml
```

### 10.4 Inheritance

The `extends` property identifies a parent YAML definition.

Paths are relative to the file declaring the inheritance.

Child properties override parent properties. Nested objects are replaced as a whole rather than recursively merged.

## 11. Structural principles

The project structure should preserve the following boundaries:

| Rule | Expected behaviour |
|---|---|
| CLI to services | CLI delegates operations to services |
| Bootstrap to components | Bootstrap constructs and injects dependencies |
| Services to repositories | Services delegate persistence and data access |
| Services to adapters | Services use adapters through defined interfaces |
| Models and storage | Models remain independent of physical storage |
| Configuration | Configuration is loaded centrally and injected |
| User input | Original user files are never modified |
| Calculated data | Results are stored separately and can be regenerated |
| Validation | Data is validated before being used in processing |

New components should be placed according to their responsibility rather than the file format they happen to manipulate.

## 12. Summary

The Patrimonia repository is organised around a clear separation between:

- Python application code;
- automated tests;
- application configuration;
- financial reference data;
- external and user-specific data;
- validation and presentation resources.

This organisation supports a modular application while keeping its data flows understandable.

The key principle is to keep application logic, reference data, user sources and calculated results independent, with explicit responsibilities and controlled interactions between them.