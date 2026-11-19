# Getting Started — Patrimonia

Patrimonia is a command-line application designed to centralize, organize and analyze personal and family financial assets.

This guide presents its main concepts, data organization and usage. Detailed information is available in the dedicated documentation.

## 1. Overview

Patrimonia organizes financial data into three areas:

| Area | Location | Purpose |
|---|---|---|
| Reference catalogue | `data/` | Shared definitions of assets, contracts and reference data |
| User input | `external-data/.../input/` | User-managed financial source data |
| Calculated data | `external-data/.../calculated/` | Derived and regenerable results |

Key principles:
- Catalogue data contains shared reference definitions.
- Input data is the source of truth for personal financial information.
- Calculated data is generated from validated sources.
- **Patrimonia never modifies user source files.**

## 2. Prerequisites and Installation

Requirements:
- Python 3.12 or later (`^3.12`).
- Poetry for dependency and virtual environment management.

Dependencies are declared in `pyproject.toml` and locked in `poetry.lock`. Main packages include Click, PyYAML, OpenPyXL, pypdf, yfinance, curl_cffi, jsonschema, referencing and python-dotenv.

Install and launch:

```bash
conda deactivate
poetry install
poetry run finance-cli
```

The intended user-facing command is `patrimonia`, depending on the console script configured in `pyproject.toml`.

## 3. Configuration

The main configuration file is:

`config/config_app.yaml`

It defines application settings, logging, catalogue and user-data locations, file conventions, validation schemas and report resources.

Paths are resolved relative to the configured base directory. Configuration is loaded at startup and injected into the relevant application components.

See [CLI Configuration](cli/configuration.md).

## 4. Data Organization

### 4.1 Reference catalogue

The `data/` directory contains shared definitions for:
- Asset categories and financial instruments.
- Contracts and accounts.
- Financial institutions and data providers.

Definitions can inherit from other definitions through `extends`.

See [Asset Catalogue](data/assets.md) and [Contracts](data/contracts.md).

### 4.2 Users and wallets

Personal data is organized by user and wallet:

```text
external-data/
└── users/
    └── <USER_ID>/
        ├── <USER_ID>.yaml
        ├── input/
        │   └── <WALLET_ID>/
        │       ├── transactions/
        │       └── balances/
        └── calculated/
            └── <WALLET_ID>/
                ├── transactions_enriched/
                └── balances/
```

A user references wallets, each associated with a financial account definition in the reference catalogue.

### 4.3 Source and calculated data

| Data | Format | Location |
|---|---|---|
| Transaction sources | Excel | `input/` |
| Official balances | Excel | `input/` |
| Enriched transactions | YAML | `calculated/` |
| Calculated balances | Excel | `calculated/` |

Input files are user-managed and read-only for Patrimonia. Calculated results are stored separately and can be regenerated.

### 4.4 Validation

Before processing, data can undergo:
1. YAML loading and inheritance resolution.
2. Structural validation using JSON Schema.
3. Business-rule validation.
4. Typed model construction using Pydantic.

See [Validation Architecture](architecture/validation/overview.md).

## 5. Command-Line Interface

The general command convention is:

```text
patrimonia <RESOURCE> [--id <RESOURCE_ID>] <ACTION> [OPTIONS]
```

Resources include users, accounts, assets and wallets.

Main actions:

| Action | Purpose |
|---|---|
| `list` | List resources |
| `show` | Display information |
| `check` | Validate data |
| `calculate` | Generate results |
| `extract` | Extract document information |
| `retrieve` | Retrieve external data |
| `upgrade` | Enrich catalogue definitions |

Examples:

```bash
patrimonia users list
patrimonia accounts list
patrimonia assets list
patrimonia asset --id <ASSET_ID> show
patrimonia wallet --id <WALLET_ID> show
```

Exact syntax and availability depend on the implemented CLI version.

See [CLI Conventions](cli/conventions.md), [User Commands](cli/users.md), [Account Commands](cli/accounts.md), [Asset Commands](cli/assets.md) and [Wallet Commands](cli/wallets.md).

## 6. Transactions

Transactions are entered in Excel workbooks stored in each wallet's `input/transactions/` directory.

Each workbook contains:
- `header`: metadata.
- `data`: transaction records.

Supported actions include `cash_in`, `cash_out`, `buy`, `sell`, `yield`, `fees` and `gift`.

Example commands:

```bash
patrimonia wallet --id <WALLET_ID> transactions check
patrimonia wallet --id <WALLET_ID> transactions show
patrimonia wallet --id <WALLET_ID> transaction show --date <DATE>
```

### Enrichment

The transaction processing workflow is:
1. Read source Excel files.
2. Validate structure and business consistency.
3. Enrich validated transactions.
4. Generate YAML results in `calculated/transactions_enriched/`.

**Enriched transactions are fully recalculated whenever processing is triggered.** They are derived data, not an independent source of truth.

They are also used as input for wallet balance calculations.

See [Transaction Domain](domain/transaction.md).

## 7. Balances

Patrimonia distinguishes official and calculated balances.

### 7.1 Official balances

Official balances are Excel snapshots stored in:

`input/<WALLET_ID>/balances/`

They originate from financial institutions or from calculated balances explicitly adopted by the user. Their provenance is recorded in file metadata.

Official files are user-managed and never modified by Patrimonia.

### 7.2 Calculated balances

Calculated balances are generated for a user-selected date using:
- The latest available official balance.
- Validated enriched transactions occurring after that balance and up to the requested date.

Results are stored in:

`calculated/<WALLET_ID>/balances/`

A calculated balance never becomes official automatically. The user must explicitly adopt it by copying it into the input directory.

Example commands:

```bash
patrimonia wallet --id <WALLET_ID> balances list
patrimonia wallet --id <WALLET_ID> balances check
patrimonia wallet --id <WALLET_ID> balance show --date <DATE>
patrimonia wallet --id <WALLET_ID> balance calculate --date <DATE>
```

See [Balance Domain](domain/balance.md).

## 8. Market Data and Asset Information

Asset definitions belong to the reference catalogue, while external market data is retrieved and processed separately.

Quotes are shared across users and stored by asset and year. They support financial valuation using the latest available quote on or before the requested valuation date.

See [Asset Management Architecture](architecture/asset-management.md).

## 9. Financial Restitutions and Dashboards

### 9.1 Wealth evolution

Wealth evolution tracks changes in financial asset values at:
- Wallet level: individual wallet evolution.
- User level: consolidated financial wealth.

Results are stored in yearly YAML files.

### 9.2 Dashboards

The planned dashboard architecture uses Plotly to generate static HTML reports viewable in a browser.

Each dashboard can include a YAML metadata file describing its generation date, data scope and source references.

Example:

```text
<WALLET_ID>_dashboard.html
<WALLET_ID>_dashboard.meta.yaml
```

See [Dashboard Generation](architecture/dashboard-generation.md).

## 10. Data Integrity and Reproducibility

Data validation and traceability are central to Patrimonia.

- Input data is validated before processing.
- Calculated results are derived from validated sources and can be regenerated.
- Generation metadata and source fingerprints can identify the data underlying a result.
- Fingerprints are based on normalized business data rather than physical Excel files, reducing sensitivity to formatting changes.

These mechanisms support data integrity and reproducibility without requiring complex versioning infrastructure.

## 11. Key Principles

1. `data/` contains shared financial reference definitions.
2. `input/` contains user-managed source data.
3. Patrimonia never modifies user source files.
4. `calculated/` contains derived and regenerable results.
5. Official balances are the reference points for balance calculations.
6. Calculated balances become official only through explicit user adoption.
7. Enriched transactions are fully recalculated from validated sources.
8. Validation precedes processing.
9. Calculated results should remain traceable to their sources.

---

**Patrimonia follows three fundamental principles: preserve source data, validate before processing, and keep calculated results traceable and reproducible.**