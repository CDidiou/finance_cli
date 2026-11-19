# CLI Conventions

## 1. Purpose

This document defines the conventions governing the Patrimonia command-line interface.

The CLI provides a consistent, predictable and explicit interface to application services. Its restricted action vocabulary ensures commands remain easy to discover and aligned with the application architecture.

The CLI does not implement business logic or directly manage data persistence.

## 2. Command Structure

Commands follow this structure:

```bash
patrimonia <RESOURCE> [RESOURCE_OPTIONS] <ACTION> [ACTION_OPTIONS]
```

- **Resource:** object or collection being accessed.
- **Resource options:** identify the target or its context.
- **Action:** operation to perform.
- **Action options:** provide operation-specific parameters.

Examples:

```bash
patrimonia users list
patrimonia assets list --category equity
patrimonia asset --id <ID_ASSET> show
patrimonia wallet --id <ID_WALLET> --user <ID_USER> show
patrimonia balance calculate --date 2026-12-31
```

The resource always precedes the action.

## 3. Resource Naming

### 3.1 Singular and plural

The CLI distinguishes individual resources from collections.

| Form | Meaning | Examples |
|---|---|---|
| Singular | Individual resource | `asset`, `account`, `wallet`, `balance` |
| Plural | Resource collection | `assets`, `accounts`, `wallets`, `users`, `transactions`, `balances` |

Examples:

```bash
patrimonia assets list
patrimonia asset --id <ID_ASSET> show
patrimonia accounts list
patrimonia account --id <ID_ACCOUNT> show
```

Singular commands generally require an identifier when targeting a specific object. Plural commands operate on collections.

### 3.2 Resource relationships

Related resources are identified explicitly through contextual options when necessary.

```bash
patrimonia wallet --id <ID_WALLET> --user <ID_USER> show
```

The CLI must avoid ambiguous implicit relationships.

## 4. Supported Actions

Patrimonia defines seven actions:

| Action | Responsibility |
|---|---|
| `list` | Discover available resources and files |
| `check` | Validate structures and business rules |
| `calculate` | Generate derived data |
| `show` | Display resource information or results |
| `retrieve` | Retrieve information from external providers |
| `extract` | Transform source documents into structured data |
| `upgrade` | Integrate information into the reference catalogue |

Each action represents a distinct user intention.

### 4.1 List

Discovers resources available in application repositories without performing full domain validation.

```bash
patrimonia users list
patrimonia accounts list
patrimonia assets list
patrimonia wallet --id <ID_WALLET> transactions list
patrimonia wallet --id <ID_WALLET> balances list
patrimonia accounts list --type broker
patrimonia assets list --category equity
```

**Purpose:** identify which resources or files are available.

### 4.2 Check

Validates data against its expected model, including:
- File and data structures.
- JSON Schema constraints.
- Types and formats.
- Business rules.
- Referential integrity.

```bash
patrimonia config check
patrimonia asset --id <ID_ASSET> check
patrimonia wallet --id <ID_WALLET> transactions check
patrimonia wallet --id <ID_WALLET> balances check
```

Successful validation confirms compliance with applicable requirements. Errors must identify the affected data and explain the failure.

Validation never modifies original user input files.

**Purpose:** determine whether data is valid and consistent.

### 4.3 Calculate

Generates derived data from validated sources.

```bash
patrimonia wallet --id <ID_WALLET> transaction calculate --year 2025
patrimonia wallet --id <ID_WALLET> balance calculate --date 2026-12-31
```

Calculations include transaction enrichment, balance calculation and portfolio evolution.

Results are regenerated from their validated sources whenever processing is triggered. Previous calculated outputs are not authoritative inputs for full recalculation workflows.

**Purpose:** generate results from validated data.

### 4.4 Show

Displays an individual resource or calculated result without modifying data.

```bash
patrimonia asset --id <ID_ASSET> show
patrimonia account --id <ID_ACCOUNT> show
patrimonia wallet --id <ID_WALLET> --user <ID_USER> show
patrimonia balance show --date 2026-12-31
```

A `--section` option can restrict the display:

```bash
patrimonia asset --id <ID_ASSET> show --section sources
```

**Purpose:** inspect resource information or calculated results.

### 4.5 Retrieve

Retrieves information from supported external providers and stores it in an appropriate intermediate or dedicated data repository.

```bash
patrimonia asset --id <ID_ASSET> retrieve market-data
patrimonia asset --id <ID_ASSET> retrieve quotes
```

Retrieval does not automatically modify the reference catalogue.

**Purpose:** obtain information from external sources.

### 4.6 Extract

Transforms available source documents into structured information.

For example, factsheets are manually downloaded and stored by the administrator. Patrimonia extracts their relevant information for subsequent processing.

Extraction is distinct from retrieving information through an external provider API.

**Purpose:** convert documentary sources into structured data.

### 4.7 Upgrade

Integrates available information into the reference catalogue.

```bash
patrimonia asset --id <ID_ASSET> upgrade factsheet
patrimonia asset --id <ID_ASSET> upgrade market-data
```

The workflow consists of:
1. Loading the existing reference asset.
2. Loading the relevant external or extracted information.
3. Validating the source information.
4. Transforming it into the reference asset representation.
5. Validating the resulting asset.
6. Persisting the updated catalogue entry.

Only validated results are integrated.

**Purpose:** enrich reference catalogue definitions.

## 5. External Data Operations

The supported operations depend on the nature and destination of the information.

### 5.1 Factsheets

Factsheets are manually acquired by the administrator because asset managers do not provide sufficiently standardized APIs for automated retrieval.

Workflow:
- The administrator downloads and stores the PDF.
- `extract` transforms its contents into structured information.
- `upgrade factsheet` integrates the relevant information into the reference catalogue.

There is no `retrieve factsheet` command.

### 5.2 Market data

Market data is retrieved through supported external integrations.

```bash
patrimonia asset --id <ID_ASSET> retrieve market-data
patrimonia asset --id <ID_ASSET> upgrade market-data
```

`retrieve` obtains and validates external information. `upgrade` integrates it into the reference catalogue.

### 5.3 Quotes

Historical prices are retrieved from Yahoo Finance using `yfinance`.

```bash
patrimonia asset --id <ID_ASSET> retrieve quotes
```

Quotes are stored separately from the reference catalogue and user-specific calculated data.

Example structure:

```text
external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/quotes/
    2025_<ID_ASSET>_quote.yaml
    2026_<ID_ASSET>_quote.yaml    
```

Each yearly YAML file contains:
- `header`: asset, provider, currency, frequency, quote field, source and retrieval timestamp.
- `data`: daily price observations.

Example:

```yaml
header:
  asset_id: FR0000032526
  provider: yahoo_finance
  provider_id: GBT.PA
  currency: EUR
  frequency: daily
  quote_field: close
  retrieved_at: '2026-11-16T18:30:00+01:00'

data:
  - date: '2026-01-02'
    close: 14.78
  - date: '2026-01-05'
    close: 14.98
```

The retrieval timestamp (`retrieved_at`) is distinct from each observation date (`data.date`).

A yearly file contains at most 366 observations; non-trading days are omitted.

Quotes are a separate data domain used by portfolio calculations. They do not modify reference asset definitions and therefore have no `upgrade quotes` operation.

### 5.4 Operation Matrix

| Data type | Operations | Destination |
|---|---|---|
| Factsheets | `extract`, `upgrade` | Reference catalogue |
| Market data | `retrieve`, `upgrade` | Reference catalogue |
| Quotes | `retrieve` | Shared quote history |

`retrieve` obtains external information, `extract` transforms documents, and `upgrade` modifies reference catalogue definitions. Retrieved information may also be stored independently of the catalogue.

## 6. Options and Parameters

### 6.1 Naming conventions

Options use lowercase long names with hyphens:

```text
--id
--user
--type
--category
--date
--details
--section
```

### 6.2 Resource options

Identify the target resource or its context.

```bash
patrimonia wallet --id <ID_WALLET> --user <ID_USER> show
```

### 6.3 Action options

Provide operation-specific parameters.

```bash
patrimonia balance calculate --date 2026-12-31
```

Options should be required only when necessary. Important business parameters must not be silently inferred.

### 6.4 Boolean options

Boolean options are flags enabled by their presence:

```bash
patrimonia users list --details
```

Avoid explicit values such as `--details true` unless the option represents a genuinely configurable value.

## 7. Date Conventions

CLI dates use ISO 8601 calendar format:

```text
YYYY-MM-DD
```

Example:

```bash
patrimonia balance calculate --date 2026-12-31
```

Invalid or ambiguous formats must be rejected.

Calculation dates represent business dates and must remain distinct from generation and retrieval timestamps.

## 8. Output and Exit Status

### 8.1 Output

Output must be concise, human-readable and consistent.

```text
Wallet: MY_WALLET
Status: active
Currency: EUR
```

Detailed diagnostics should be available without overwhelming normal output.

### 8.2 Errors

Error messages should identify:
1. The failed operation.
2. The affected resource or file.
3. The cause, when known.
4. Possible corrective actions.

Where applicable, diagnostics should include file path, worksheet, row, field and validation rule.

Internal stack traces should not appear in normal user-facing errors.

### 8.3 Exit status

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Execution error |
| `2` | Usage or argument error |
| `3` | Data validation failure |

Failed or incomplete operations must never report success.

## 9. CLI Responsibilities

The CLI is responsible for:
- Parsing commands and options.
- Validating arguments and command syntax.
- Calling application services.
- Presenting results and errors.
- Returning appropriate exit statuses.

It must not:
- Implement business calculations.
- Read or write YAML and Excel files directly.
- Construct repository or adapter dependencies.
- Duplicate business validation rules.
- Contain provider-specific integration logic.

Business validation, persistence and external integrations belong to the appropriate application layers.

The CLI validates syntax, option values and basic argument constraints; application services handle business rules and data integrity.

## 10. Design Principles

All commands must follow these principles:

1. **Restricted vocabulary:** use the seven defined actions.
2. **Clear semantics:** each action has a distinct responsibility.
3. **Explicitness:** identify resources and important business parameters.
4. **Consistency:** maintain common syntax and terminology.
5. **Separation of concerns:** keep business logic outside the CLI.
6. **Data integrity:** preserve user input and validate before processing.
7. **Simplicity:** avoid exposing internal implementation steps.

New commands should reuse the existing action vocabulary whenever possible. A new action is justified only when a genuinely distinct user-facing responsibility cannot be expressed through the existing seven actions.

**Fundamental rule: Each CLI action represents a distinct user intention, not an internal implementation step.**