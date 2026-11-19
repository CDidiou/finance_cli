# Patrimonia — Technical Foundations

## 1. Project Structure

Patrimonia is a Python package managed with Poetry.

The application source code is located in `src/finance_cli/`, while automated tests are maintained separately in `tests/`.

The project separates application code, reference data, configuration and external user data.

The `pyproject.toml` file defines:
- Package metadata and dependencies
- The `finance-cli` command-line entry point
- Development dependencies and tooling
- Project build configuration

Application configuration is loaded at CLI startup through `load_app_config` and injected into the components that require it.

Components such as services, repositories and file readers receive their configuration through dependency injection. They do not independently reload the application configuration.

## 2. YAML Data Organization

### 2.1. Reference Catalogue

Reference data is stored under `data/`.

The main catalogue areas include:

- `data/contracts/`: generic financial contract definitions and broker-specific implementations.
- `data/assets/`: financial asset categories and concrete asset implementations.
- `data/economy/`: reference economic data.

Contract definitions describe generic products such as PEA, LDDS and life insurance.

Broker-specific implementations are stored in an `implementations/` subdirectory and inherit from their generic contract definition using `extends`.

The combination of a contract definition and a broker-specific implementation describes an account offering. A user's wallet references the appropriate implementation.

### 2.2. Asset Catalogue

The asset catalogue is organized by category under `data/assets/`.

Each category has a YAML definition file named after its directory. For example:

```text
assets/
├── savings_accounts/
│   ├── savings_accounts.yaml
│   └── implementations/
└── etc/
    ├── etc.yaml
    └── implementations/
```

Specialized categories can inherit from parent categories through `extends`.

Concrete financial instruments are stored in an `implementations/` directory under their final category and inherit from that category's definition.

For example:

```text
assets/
└── mutual_funds/
    └── opcvm/
        └── fcp/
            ├── fcp.yaml
            └── implementations/
                └── FR0007018239.yaml
```

Euro-denominated life insurance funds remain a distinct category from savings accounts and exchange-traded commodities (ETCs).

### 2.3. YAML Inheritance

The `extends` property references another YAML file using a path relative to the file declaring it.

The child definition inherits the properties of its parent. When a property is defined in both files, the child's value takes precedence.

Nested objects are replaced as a whole when overridden. They are not recursively merged.

This inheritance mechanism is resolved before catalogue validation.

### 2.4. YAML Naming Conventions

YAML field names use English `snake_case`.

Each record starts with a stable identifier:

- `id` for users, wallets, contracts and asset categories;
- `isin` for financial instruments that have an ISIN;
- `id` for instruments without an ISIN.

References to catalogue resources use paths relative to the `data/` directory.

Examples:

```yaml
account_ref: contracts/LDDS/implementations/la-banque-postale.yaml

asset_ref: assets/mutual_funds/opcvm/fcp/implementations/FR0007018239.yaml
```

### 2.5. User and Wallet References

User-specific data is stored under:

```text
external-data/users/<USER_ID>/
```

A user references their wallets by their stable identifiers.

Each wallet has its own YAML definition and references an account implementation through `account_ref`.

A wallet represents an account held by a specific user. It is therefore distinct from the generic contract definition or broker-specific account offering in the reference catalogue.

The wallet also identifies the resources associated with its financial activity, including transactions and balances.

## 3. Domain Model

### 3.1. Account

An account definition describes a financial product or account offering, such as a PEA, securities account or savings account.

Generic contract definitions and broker-specific implementations are stored in `data/contracts/`.

A wallet references the relevant account implementation through `account_ref`.

The `Account` model represents the loaded and validated account definition. It is independent of the underlying YAML storage format.

Catalogue loading, inheritance resolution, validation and persistence are handled by the relevant repository and its specialized validation components.

### 3.2. Wallet

A `Wallet` represents a financial account held by a user.

For example, a user may have a PEA with a particular broker.

A wallet definition includes information such as:

- A stable identifier (`id`)
- A name
- An account reference (`account_ref`)
- A currency
- An opening date
- An active or inactive status
- References to the assets held in the wallet

Transactions and balances associated with the wallet are stored separately from its descriptive YAML definition.

Wallet definitions are stored under:

```text
external-data/users/<USER_ID>/
```

The `Wallet` model represents wallet data independently of its storage format.

### 3.3. Transaction

A `Transaction` represents a single financial operation affecting a wallet.

The supported transaction actions include:

- `cash_in`: cash deposit
- `cash_out`: cash withdrawal
- `buy`: asset purchase
- `sell`: asset sale
- `yield`: income or investment return
- `fees`: fees
- `gift`: gift or donation

A transaction contains information such as its date, action, asset identifier, asset name, quantity, price and operation value.

The enriched transaction data can also contain calculated fields such as:

- `pru_shares`: unit cost basis
- `pru_value`: total cost basis

The `Transaction` model is independent of Excel and YAML storage formats.

Source transactions are provided by users in Excel files. After validation, Patrimonia generates enriched transaction data in YAML.

The enriched data is fully recalculated from the validated source transactions whenever a command triggers the calculation. It is a derived result, not an independent source of truth.

### 3.4. Balance

A `Balance` represents the positions held in a wallet at a given date.

Patrimonia distinguishes two types of balances:

- **Official balance**: a reference snapshot supplied by the user, stored in the input area.
- **Calculated balance**: a snapshot generated by Patrimonia from an official balance, enriched transactions and the requested calculation date.

Official balances are never modified by Patrimonia. A calculated balance does not automatically become an official balance: the user must explicitly copy it into the input area if they want to use it as a new reference snapshot.

The `Balance` model represents balance data independently of its storage format.

## 4. User Financial Data Files

### 4.1. Transaction Source Files

User-provided transaction data is stored in Excel files under:

```text
external-data/users/<USER_ID>/input/<WALLET_ID>/transactions/
```

Each transaction workbook contains two worksheets:

- `header`: metadata represented as key-value pairs in columns A and B.
- `data`: transaction records, with column names on the first row and records starting on the second row.

The header contains metadata such as the relevant year and wallet identifier.

The Excel files are user-managed input sources. Patrimonia validates and reads them but does not modify them.

### 4.2. Enriched Transactions

Validated source transactions are used to generate enriched transaction data in YAML.

The enriched data is stored under:

```text
external-data/users/<USER_ID>/calculated/<WALLET_ID>/transactions_enriched/
```

It includes calculated information such as the unit cost basis (PRU).

The calculation is a full regeneration from validated input sources. Previous enriched results are not used as the basis for subsequent calculations.

### 4.3. Balance Files

Official balance files are stored under:

```text
external-data/users/<USER_ID>/input/<WALLET_ID>/balances/
```

They are supplied and maintained by the user and are read-only from Patrimonia's perspective.

Calculated balance files are stored under:

```text
external-data/users/<USER_ID>/calculated/<WALLET_ID>/balances/
```

They are generated by Patrimonia from the latest applicable official balance, enriched transactions and the requested target date.

The Excel format is used for both official and calculated balance files.

## 5. Automated Tests

Automated tests are maintained in the `tests/` directory.

The test suite should cover the main application layers and their responsibilities:

- **Model tests**: domain behavior, data structures and business invariants.
- **Repository and validation tests**: data loading, validation and persistence.
- **Reader tests**: reading and writing supported file formats, including Excel.
- **Service tests**: application workflows and orchestration.
- **CLI tests**: command behavior, arguments and output.

Shared fixtures and test configuration can be defined in `tests/conftest.py`.

An illustrative test organization is:

```text
tests/
├── conftest.py
├── test_models/
│   ├── test_account.py
│   ├── test_wallet.py
│   ├── test_transaction.py
│   └── test_balance.py
├── test_repositories/
├── test_readers/
│   └── test_transaction_excel_reader.py
├── test_services/
└── test_cli/
    ├── test_account_commands.py
    └── test_wallet_commands.py
```

The actual test structure should follow the organization of the implemented code. The example above describes a logical organization and does not imply that every listed test module already exists.

## 6. Related Documentation

This document provides a technical overview. Detailed specifications are maintained in dedicated documents:

| Subject | Reference |
|---|---|
| Overall architecture | `architecture/overview.md` |
| Python project structure | `architecture/project-structure.md` |
| Application layers and responsibilities | `architecture/layers-and-responsibilities.md` |
| Data flow | `architecture/data-flow.md` |
| YAML conventions | `data/yaml-conventions.md` |
| Asset catalogue | `data/assets.md` |
| User and wallet data | `data/users-wallets.md` |
| Transaction domain model | `domain/transaction.md` |
| Balance domain model | `domain/balance.md` |
| Testing strategy | `development/testing.md` |