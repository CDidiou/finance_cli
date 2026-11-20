# Patrimonia — Development Roadmap

## 1. Purpose

This document describes the recommended development roadmap for Patrimonia.

It identifies the main CLI command groups, establishes development priorities and defines the recommended order for implementing application features.

The objective is to build the application progressively, stabilizing the responsibilities and interfaces of each architectural layer before expanding the command set.

Development should follow three principles:

- **Incremental implementation**: develop and validate one feature at a time.
- **Architectural consistency**: preserve the separation between CLI, services, repositories and adapters.
- **Test-driven reliability**: provide appropriate unit, integration and CLI tests for each feature.

The roadmap is indicative and may evolve as the domain model and application requirements become more mature.

## 2. Target CLI Organization

The CLI is expected to cover the following functional areas:

```text
patrimonia
│
├── asset       Asset catalogue and external asset data
├── account     Account and contract definitions
├── user        User management
├── wallet      User financial accounts and their operations
├── valuation   Portfolio valuation
├── dashboard   Financial dashboards and reporting
└── data        Data inspection and maintenance
```

These groups should not all be implemented immediately.

They should be introduced progressively, according to the maturity of the underlying domain models and application services.

In particular, the distinction between wallets and a broader portfolio concept should be clarified before introducing a dedicated `portfolio` command group.

## 3. Phase 1 — Complete Asset Management

<badge color="success">Current priority</badge>

The asset management functionality is the first development priority.

It provides the reference data required by subsequent features, including wallet management, valuation and reporting.

### 3.1. Existing Functionality

The following operations are already part of the asset management workflow:

```bash
patrimonia asset --id <ID_ASSET> show

patrimonia asset --id <ID_ASSET> retrieve market-data

patrimonia asset --id <ID_ASSET> upgrade market-data
```

The `retrieve` operation retrieves external market data.

The `upgrade` operation integrates selected information from the collected data into the asset catalogue.

### 3.2. Recommended Development Order

| Feature | Responsibility | Priority |
|---|---|---|
| `asset list` | List assets in the reference catalogue | Very high |
| `asset --id <ID> check` | Validate an asset definition | High |
| `asset add` | Add a new asset to the catalogue | To be specified |
| `asset retrieve market-data` | Collect external market data | Existing |
| `asset upgrade market-data` | Integrate collected data into the catalogue | Existing |
| Asset deletion | Remove an asset from the catalogue | Later |

The `add` operation requires a separate CLI design decision because it is not part of the currently established public action vocabulary. The preferred approach is to create an asset from a YAML file rather than expose a large number of individual command-line options.

Deletion should remain a later feature because it requires safeguards for assets already referenced by wallets or historical transactions.

### 3.3. First Priority: `asset list`

The next command to implement is:

```bash
patrimonia asset list
```

Its purpose is to display the assets available in the reference catalogue.

Example output:

```text
ID              NAME                 CATEGORY
FR0000120271    TotalEnergies        equity
IE000BI8OT95    iShares Core MSCI    etf
LU0996182563    Bond Fund            fund

3 assets found.
```

Possible future filters include:

```bash
patrimonia asset list --category equity

patrimonia asset list --category etf
```

The implementation can rely on the existing `AssetRepository.load_all()` method, provided its current behavior meets the requirements of the command.

The CLI command should remain responsible for argument handling and result presentation. Data retrieval and business logic should remain delegated to the appropriate application components.

### 3.4. Asset Validation: `check`

The asset validation command should be:

```bash
patrimonia asset --id FR0000120271 check
```

It should verify:

- The existence of the asset definition.
- YAML loading and inheritance resolution.
- JSON Schema compliance.
- Business rule compliance.
- Successful construction of a valid `Asset` model.

The operation must not modify the catalogue.

It should reuse the existing repository validation pipeline rather than implement a separate validation mechanism.

### 3.5. Asset Creation

Creating an asset from a YAML file is preferable to a command requiring numerous individual options.

An example of a possible future interface is:

```bash
patrimonia asset add --file new_asset.yaml
```

The implementation should:
- Load the supplied YAML file.
- Resolve inheritance where applicable.
- Validate the definition.
- Construct the corresponding `Asset` model.
- Persist the new catalogue entry only after successful validation.

The exact command name and interface remain to be specified in accordance with the CLI conventions.

## 4. Phase 2 — Complete External Market Data Collection

Once the basic asset commands are stable, the next step is to improve the market data collection workflow.

The architecture must preserve the separation between the reference catalogue and externally collected data.

### 4.1. Data Collection

The collection operation is initiated through:

```bash
patrimonia asset --id <ID_ASSET> retrieve market-data
```

The workflow is:

```text
AssetService
    |
    v
MarketDataYahooFinance
    |
    v
External market data
    |
    v
ScrapedDataRepository
```

The collected data is stored separately from the reference asset catalogue.

### 4.2. Catalogue Enrichment

Integration into the catalogue is an explicit operation:

```bash
patrimonia asset --id <ID_ASSET> upgrade market-data
```

The workflow is:

```text
ScrapedDataRepository
    |
    v
AssetService
    |
    v
AssetRepository
    |
    v
Updated asset catalogue
```

This separation allows collected data to be inspected and validated before it modifies the reference catalogue.

### 4.3. Bulk Collection

Once individual collection is reliable, bulk collection can be introduced.

A possible interface is:

```bash
patrimonia asset retrieve market-data --all
```

It should collect market data for all eligible assets.

Category filtering could subsequently be supported:

```bash
patrimonia asset retrieve market-data --all --category equity
```

Bulk processing should include:
- Identification of eligible assets.
- Individual collection error handling.
- A summary of successful and failed operations.
- Appropriate logging.
- Integration tests covering multiple assets and partial failures.

Bulk enrichment should be considered separately from bulk collection. Collection must not automatically imply catalogue modification.

## 5. Phase 3 — Account, User and Wallet Management

Once asset management is sufficiently stable, development can move towards the management of users and their financial accounts.

### 5.1. Account Management

The account domain is based on generic contract definitions and broker-specific implementations.

Potential commands include:

```bash
patrimonia account list

patrimonia account --id <ID_ACCOUNT> show
```

The account management functionality should allow users to discover and inspect available account definitions.

It should reuse the existing catalogue loading and validation mechanisms.

### 5.2. User Management

The user domain represents the individuals whose financial data is managed by Patrimonia.

Potential commands include:

```bash
patrimonia user list

patrimonia user --id <ID_USER> show
```

These commands should provide access to user definitions and their associated information.

### 5.3. Wallet Management

A wallet represents a financial account held by a user and references a broker-specific account implementation.

Wallet management should progressively cover:
- Listing a user's wallets.
- Displaying wallet information.
- Inspecting associated assets.
- Accessing transaction and balance data.
- Validating wallet definitions and associated resources.

The wallet domain should be developed before introducing a separate portfolio domain.

A dedicated `portfolio` command group should only be introduced if a distinct portfolio concept and its responsibilities are justified by the domain model.

## 6. Phase 4 — Valuation

Valuation depends on the availability of a consistent model for users, wallets, transactions, balances and asset quotes.

It should therefore be developed after the preceding domains are sufficiently mature.

The main objectives are:
- Determine the value of wallet positions.
- Aggregate values at user level.
- Calculate asset allocation.
- Track valuation over time.
- Support historical valuation at a requested date.

The implementation should rely on the existing domain models and calculated data.

Potential commands include:

```bash
patrimonia valuation calculate

patrimonia valuation show
```

The exact command interface and calculation scope should be defined when the valuation service and its inputs are specified.

Expected valuation capabilities include:

- Position valuation.
- Allocation by asset category.
- Geographic exposure.
- Currency allocation.
- Historical portfolio value evolution.

The calculation logic must remain in the application and domain layers, not in CLI commands or dashboard templates.

## 7. Phase 5 — Dashboards and Reporting

Once valuation results are available, Patrimonia can provide reporting and visualization features.

The dashboard generation architecture is described separately in:

`docs/architecture/dashboard-generation.md`

The objectives include:
- Financial summaries.
- Asset allocation visualizations.
- Geographic and currency exposure.
- Historical valuation charts.
- Exportable financial reports.

A possible future CLI interface is:

```bash
patrimonia dashboard generate
```

The command should delegate HTML generation to the dedicated dashboard application components.

Dashboard generation should consume calculated financial data without reimplementing valuation logic.

Additional export formats may be introduced later if there is a clear requirement.

## 8. Development Roadmap Summary

The recommended development sequence is:

| Step | Scope | Main objectives |
|---|---|---|
| 1 | Asset management | `list`, `check`, asset creation |
| 2 | External market data | Bulk collection, error handling, integration tests |
| 3 | Account management | Account listing and inspection |
| 4 | User and wallet management | User and wallet listing, inspection and associated data |
| 5 | Valuation | Position calculation and portfolio aggregation |
| 6 | Dashboards and reporting | Visualizations, summaries and exports |

Each step should be considered complete only when its main workflows are implemented, tested and documented.

## 9. Immediate Next Step

<badge color="success">Next development task</badge>

Implement:

```bash
patrimonia asset list
```

This command is a good next step because:
- It provides immediate practical value.
- It relies on an existing repository capability.
- It exercises the separation between CLI and repository responsibilities.
- It provides a foundation for subsequent catalogue operations.

The implementation should include:
1. CLI argument and command definition.
2. Service integration, if required by the existing application architecture.
3. Asset retrieval through `AssetRepository`.
4. Clear and consistent terminal output.
5. Unit and CLI tests.

The command should be implemented and validated before moving on to the next feature.

## 10. Development Principles

Throughout the roadmap, the following rules should be maintained:

- Develop one feature at a time.
- Keep CLI commands focused on user interaction and presentation.
- Delegate use-case orchestration to application services.
- Encapsulate data access, validation and persistence in repositories.
- Keep external integrations isolated in adapters.
- Reuse existing validation and data-loading pipelines.
- Add automated tests for each new behavior.
- Update the documentation when architectural decisions or public CLI interfaces change.

**Guiding principle:** stabilize the contracts between application layers before increasing the number of commands and features.

A progressive implementation is preferable to developing a large command set before the underlying architecture and domain models are stable.

# 11 Documentation

Proposition d'arborescence:

docs/
├── index.md
├── getting-started.md
├── architecture/
│   ├── overview.md
│   ├── project-structure.md
│   ├── dependencies.md
│   └── data-flow.md
├── data/
│   ├── yaml-conventions.md
│   ├── contracts.md
│   ├── assets.md
│   └── users-wallets.md
├── domain/
│   ├── account.md
│   ├── wallet.md
│   ├── transaction.md
│   └── balance.md
├── cli/
│   ├── conventions.md
│   ├── configuration.md
│   ├── users.md
│   ├── accounts.md
│   ├── assets.md
│   └── wallets.md
└── development/
    └── testing.md


# 12 Evolution du CLI

## Création de page statique html

Avec plotly

## App Dash

Conversion des commandes CLI en dashboard

## Source d'inspiration
Source d'inspiration: https://librefolio.github.io/LibreFolio/fr/
