# Asset Data Structure

## 1. Purpose and Scope

This document describes how data related to an `Asset` is organized and stored in Patrimonia.

It covers four complementary dimensions:

1. **Asset catalog**: the reference YAML document describing the asset.
2. **Factsheets**: source documents used to extract structured information.
3. **Market data**: external information collected to complete or update the asset catalog.
4. **Quotes**: historical market prices used for portfolio valuation.

These dimensions have different purposes, lifecycles, and storage locations.

Their locations and file naming conventions are defined through the application configuration, notably `config_app.yaml`.

## 2. Overview of Asset Data

| Data dimension | Required | Storage location | Main purpose |
|---|---|---|---|
| Asset catalog | Yes | `data/assets/` | Asset identity, descriptive information, classification, and source configuration |
| Factsheets | Optional | `external-data/assets/` | Primary documentary sources for extracting structured information |
| Market data | Optional | `external-data/assets/` | Intermediate data collected from external providers to complete or update the catalog |
| Quotes | Optional | `external-data/assets/` | Historical daily closing prices used for portfolio valuation |

The asset catalog is the reference definition of an asset.

External data provides additional information but does not replace the catalog as the reference source.

## 3. Directory Structure

### 3.1 Reference Catalog

Asset definitions are stored under `data/assets/`.

```text
data/
└── assets/
    ├── <category>/
    │   ├── <category>.yaml
    │   ├── implementations/
    │   │   ├── <ASSET_ID>.yaml
    │   │   └── ...
    │   └── ...
    └── ...
```

The category definition file provides default properties for assets belonging to that category.

Concrete asset definitions are stored in the category's `implementations/` directory.

Specialized categories may inherit from parent categories through `extends`.

### 3.2 External Asset Data

External data is stored separately from the reference catalog.

```text
external-data/
├── assets/
│   └── <CATEGORY_PATH>/
│       └── <ASSET_ID>/
│           ├── factsheets/
│           │   └── ...
│           ├── scraped_data/
│           │   └── ...
│           └── quotes/
│               ├── 2025_<ASSET_ID>_quote.yaml
│               ├── 2026_<ASSET_ID>_quote.yaml
│               └── ...
└── ...
```

The exact directory and file naming conventions are defined by the application configuration.

The main principles are:

- Reference catalog files are versioned and maintained as part of the project.
- External data is stored separately from the reference catalog.
- Intermediate data can be regenerated from its original sources.
- Quote files are organized by asset and calendar year.
- External data is not considered an independent source of truth for the asset definition.

## 4. Asset Catalog Structure

### 4.1 Category Inheritance

Asset definitions can inherit properties from parent category definitions.

A typical inheritance chain may look like:

```text
assets.yaml
└── mutual_funds.yaml
    └── opcvm.yaml
        └── european_etf.yaml
            └── implementations/<ISIN>.yaml
```

Other asset categories, such as shares or euro funds, follow their own inheritance chains.

Inheritance is expressed through the `extends` property.

The inheritance rules are:

- A child inherits properties from its parent.
- A property explicitly defined by the child replaces the corresponding parent property.
- Nested objects are replaced as a whole; they are not recursively merged.
- The final document is obtained after resolving the complete inheritance chain.

The detailed inheritance and merge conventions are described in `yaml-conventions.md`.

### 4.2 Source Configuration

The asset catalog may contain a `sources` section describing the external sources associated with the asset.

These declarations identify the providers and provider-specific identifiers required by the corresponding workflows.

Typical source categories include:

| Source | Purpose | Workflow |
|---|---|---|
| `factsheet` | Identify the documentary source and extraction mechanism | `extract`, then `enrich` |
| Market data provider | Identify the external provider and asset identifier | `fetch`, then `enrich` |
| Quote provider | Identify the provider used to retrieve historical quotes | `fetch` |

The precise configuration fields depend on the source type and its implementation.

For example, a provider-specific symbol may differ from the asset's ISIN:

```yaml
sources:
  factsheet:
    provider: amundi_factsheet

  market_data:
    provider: yahoo_finance
    symbol: CW8.PA
```

This example illustrates the distinction between the asset's reference identity and the identifier used by an external provider.

A source declaration describes how external information can be obtained. It does not mean that the corresponding external data is already available.

### 4.3 Asset Lifecycle Information

The asset catalog may contain lifecycle information in its `general_info` section.

Typical fields include:

```yaml
general_info:
  inception_date: "2015-01-01"
  closed_date: null
  status: active
```

| Field | Meaning |
|---|---|
| `inception_date` | Date on which the asset was created or launched |
| `closed_date` | Date on which the asset ceased to exist or was closed, if applicable |
| `status` | Current lifecycle status, such as `active` or `closed` |

The actual field definitions and constraints are determined by the relevant catalog schema.

## 5. Factsheets

### 5.1 Purpose

A factsheet is a documentary source, typically a PDF published by an asset management company.

It provides information that can be extracted and incorporated into an asset catalog.

Factsheets are particularly useful for ETFs and mutual funds, for which they may contain:

- Fund characteristics.
- Investment objectives.
- Risk information.
- Asset allocation.
- Fees and charges.
- Performance information.
- Other descriptive or financial information.

### 5.2 Storage

Factsheets are stored under the corresponding asset directory:

```text
external-data/assets/<CATEGORY_PATH>/<ASSET_ID>/factsheets/
```

The acquisition of a factsheet is an administrative operation. The document is made available to Patrimonia before the extraction workflow is executed.

The original document is a source, not a generated catalog file.

Retention and archival policies are independent of the extraction process. Older factsheets may be retained when historical traceability is useful.

### 5.3 Processing Workflow

The factsheet workflow consists of two distinct operations:

**1. Extract**

- Reads the available PDF document.
- Uses the configured extraction provider.
- Extracts relevant information.
- Produces structured intermediate data.

**2. Enrich**

- Uses the extracted information to propose or apply updates to the asset catalog.
- Applies the catalog's validation rules.
- Keeps the catalog as the reference definition.

The extraction step does not directly modify the asset catalog.

The separation between extraction and enrichment allows extracted information to be reviewed before it is integrated.

## 6. Market Data

### 6.1 Purpose

Market data is external information collected from providers to complete or update an asset catalog.

It may include information such as:

- Net asset value (NAV).
- Assets under management (AUM).
- Market capitalization.
- Other provider-supplied descriptive or financial information.

Market data is distinct from the historical daily quotes used for portfolio valuation.

### 6.2 Storage

Collected market data is stored as intermediate external data:

```text
external-data/assets/<CATEGORY_PATH>/<ASSET_ID>/scraped_data/
```

The intermediate representation separates provider-specific data from the reference catalog.

It allows the collected information to be inspected, transformed, and reused during enrichment.

### 6.3 Processing Workflow

Market data processing consists of two operations:

**1. Fetch**

- Contacts the configured external provider.
- Retrieves the available information for the asset.
- Converts the response into Patrimonia's intermediate representation.
- Stores the collected data in the external-data area.

**2. Enrich**

- Reads the intermediate market data.
- Maps the available information to the corresponding catalog fields.
- Applies the enrichment rules.
- Validates the resulting catalog document before it is persisted.

The enrichment process must distinguish between missing catalog information and existing reference information.

Existing catalog values must not be overwritten indiscriminately. In particular, discrepancies between external information and already maintained reference values should be handled according to explicit enrichment rules.

The precise update policy belongs to the asset management workflow and should not be inferred solely from the presence of a market data provider.

### 6.4 Provider Selection

The choice of provider depends on the asset category and the availability and quality of its data.

For example:

| Asset category | Possible provider | Considerations |
|---|---|---|
| European ETFs | Yahoo Finance | Useful coverage for listed ETFs |
| Mutual funds | Yahoo Finance | Coverage varies depending on the fund |
| Shares | Yahoo Finance or another financial data provider | Depends on the required market information |
| Euro funds | Often not applicable | External market data may provide limited additional value |
| Savings accounts | Not applicable in the usual market-data sense | These assets are not market-traded instruments |

Provider selection is a configuration and integration concern. A provider should only be declared when the required integration is supported.

## 7. Historical Quotes

### 7.1 Purpose

Quotes represent the historical market prices of an asset.

They are used to calculate the historical value of portfolios and support long-term wealth monitoring.

Patrimonia uses daily closing prices rather than intraday market data.

The selected Yahoo Finance field is `close`, not `adjclose`.

Quotes are optional because some asset categories do not have market quotations.

Examples include:

- Savings accounts.
- Euro funds without a market quotation.

### 7.2 Storage

Quotes are shared across users and are stored by asset and calendar year:

```text
external-data/assets/<CATEGORY_PATH>/<ASSET_ID>/quotes/
    <YYYY>_<ASSET_ID>_quote.yaml
```

A separate YAML file is used for each asset and year.

The files contain daily observations, generally limited to business days for traded assets.

### 7.3 YAML Format

A quote file follows this structure:

```yaml
header:
  asset_id: FR0000032526
  provider: yahoo_finance
  provider_id: GBT.PA
  currency: EUR
  frequency: daily
  quote_field: close
  source: https://finance.yahoo.com/quote/GBT.PA/history/
  fetched_at: '2026-11-16T18:30:00+01:00'

data:
  - date: '2026-01-02'
    close: 14.78
  - date: '2026-01-05'
    close: 14.92
```

The `header` section describes the source and characteristics of the collected data.

| Field | Description |
|---|---|
| `asset_id` | Patrimonia asset identifier |
| `provider` | External data provider |
| `provider_id` | Provider-specific asset identifier |
| `currency` | Currency of the quoted price |
| `frequency` | Observation frequency, currently `daily` |
| `quote_field` | Selected price field, currently `close` |
| `source` | Source URL |
| `fetched_at` | Timestamp of data retrieval |

The `data` section contains the daily observations.

Each observation contains its date and closing price.

`fetched_at` records when the data was retrieved. It must not be confused with the observation date stored in `data[].date`.

### 7.4 Retrieval Workflow

Quotes are retrieved through the `fetch` operation.

Unlike factsheets and market data, quotes do not require a subsequent `enrich` operation.

They remain separate from the asset catalog because they represent time-series market observations rather than reference information about the asset.

The quote workflow must preserve the distinction between:

- The asset's reference identity.
- The provider-specific identifier.
- The observation date.
- The retrieval timestamp.

## 8. Asset Categories and External Data

The following table illustrates the typical availability of external data by asset category.

| Category | Quotes | Factsheets | Market data |
|---|---|---|---|
| `european_etf` | Yes | Generally applicable | Depending on provider coverage |
| `share` | Yes | Generally not applicable | Depending on provider coverage |
| `euro_funds` | No | Generally not applicable | Usually not applicable |
| `savings_accounts` | No | Not applicable | Not applicable |
| `mutual_funds` | Depending on the instrument | Depending on the fund | Depending on provider coverage |

These are typical characteristics, not unconditional rules.

The actual availability of each data source is determined by the asset definition, category, and supported integrations.

## 9. Related CLI Operations

Asset-related operations follow the common Patrimonia CLI vocabulary.

| Operation | Purpose |
|---|---|
| `list` | Discover available asset definitions |
| `show` | Display an asset and its available associated data |
| `check` | Validate an asset catalog definition |
| `extract` | Extract structured information from a factsheet |
| `fetch` | Retrieve external market data or historical quotes |
| `enrich` | Integrate extracted or collected information into the asset catalog |

The exact command syntax and available options are documented in the CLI reference.

The distinction between these operations is important:

- `extract` produces structured intermediate information from a documentary source.
- `fetch` retrieves information from an external provider.
- `enrich` integrates intermediate information into the reference catalog.
- `check` verifies catalog validity.
- `show` displays information without changing the underlying data.

Quotes are retrieved through `fetch` and are not integrated into the asset catalog through `enrich`.

## 10. Data Management Principles

The organization of asset data follows these principles:

1. **The asset catalog is the reference definition.** It contains the maintained identity, classification, descriptive information, and source configuration of each asset.

2. **External data remains separate from the catalog.** Factsheets, collected market data, and quotes are stored under `external-data/`.

3. **Original sources are preserved.** Downloaded documents and user-provided source material must not be silently replaced by derived information.

4. **Intermediate data is distinct from final reference data.** Extracted or fetched information is stored separately before any catalog enrichment.

5. **Enrichment is controlled.** External information must not silently overwrite existing reference information without an explicit update policy.

6. **Quotes are independent time series.** They are shared across users, organized by asset and year, and used for historical valuation.

7. **Calculated and collected data must remain reproducible where possible.** Derived data should be regenerable from its original sources and the applicable processing workflow.