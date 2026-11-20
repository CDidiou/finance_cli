# Asset Management Architecture

This document describes the application architecture used to manage financial assets in Patrimonia.

It focuses on the responsibilities of the application components and the data flows involved in retrieving, processing, and storing asset information.

It complements the following documentation:

- `architecture/overview.md`: overall application architecture.
- `architecture/layers-and-responsibilities.md`: software layers and dependency rules.
- `data/assets.md`: asset catalogue organization and data conventions.
- `data/yaml-conventions.md`: YAML storage conventions.

The architecture separates five main concerns:

- The internal asset catalogue.
- External information retrieved from data providers.
- Shared asset quote data.
- Application services that orchestrate operations.
- Repositories and adapters that manage persistence and external integrations.

## 1. Asset Data Organization

Patrimonia distinguishes three types of asset-related data.

### 1.1. Asset Catalogue

The asset catalogue contains the reference definitions used by the application.

It is stored under:

```text
data/assets/
```

An asset definition contains its reference information and the properties required by Patrimonia.

The catalogue is the reference source for asset identification and classification.

It is managed separately from external market observations.

### 1.2. External Market Data

External market data consists of information retrieved from external providers and intended to enrich asset definitions.

This data is first collected and stored separately from the catalogue.

It is then processed and, when valid, integrated into the corresponding asset definition.

The separation between collection and enrichment makes it possible to inspect and validate external information before modifying the reference catalogue.

### 1.3. Asset Quotes

Asset quotes are daily closing observations used for portfolio valuation.

They are shared across all Patrimonia users and are stored separately from both the asset catalogue and user-specific data.

Their configured storage location is:

```text
external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/quotes/
```

The filename convention is:

```text
<YYYY>_<ID_ASSET>_quote.yaml
```

Quotes are retrieved from external providers, such as Yahoo Finance.

The selected observation field is `close`, representing the daily closing quote. Quotes are not integrated into the asset catalogue.

The distinction between market data and quotes is important:

| Data type | Purpose | Processing |
|---|---|---|
| Market data | Enrich asset reference information | Fetch, then enrich |
| Quotes | Provide daily closing observations for valuation | Fetch and store separately |

## 2. Application Components

### 2.1. Overall Organization

Asset-related operations are orchestrated by application services.

Repositories encapsulate data access and persistence, while adapters handle communication with external providers.

The following diagram illustrates the main responsibilities and interactions:

```text
                         CLI
                          |
                          v
                     AssetService
                          |
             +------------+-------------+
             |                          |
             v                          v
       AssetRepository          MarketDataRepository
             |                          |
             v                          v
       Asset Catalogue             External Data
             |                          ^
             |                          |
             v                          |
        Asset Model             External Provider Adapter
                                        |
                                        v
                                 External Provider


                     AssetService
                          |
                          v
                 Market Data Transformation
                          |
                          v
                  AssetRepository
                          |
                          v
                   Asset Catalogue
```

The diagram is conceptual. The precise repository and adapter implementations depend on the data type and the current application implementation.

Dependencies are assembled in the bootstrap layer.

### 2.2. Application Service: AssetService

The asset service orchestrates application operations related to assets.

Its responsibilities include:

- Loading an asset from the reference catalogue.
- Providing asset information for display.
- Triggering external market data collection.
- Orchestrating the enrichment of asset definitions.
- Triggering quote retrieval when required.

The service receives its dependencies through dependency injection.

Depending on the operation, these dependencies include:

- The asset repository.
- The repository responsible for intermediate external data.
- External provider adapters.
- Transformation components.

The service does not directly manage filesystem paths, YAML serialization, Excel files, or low-level network communication.

It coordinates the application operations without taking responsibility for their technical implementation.

### 2.3. Asset Repository

The asset repository manages access to the reference asset catalogue.

Its responsibilities include:

- Resolving an asset definition from its identifier.
- Loading asset data from the catalogue.
- Validating loaded data.
- Constructing the corresponding Pydantic `Asset` model.
- Persisting updated asset definitions.
- Resolving the relative category path associated with an asset.

The catalogue is stored in YAML files.

The repository relies on the relevant infrastructure components, including:

- Configuration and path resolution.
- Structural validation.
- Asset models.
- YAML reading and writing mechanisms.

The repository provides the persistence boundary for the asset catalogue.

Application services should not directly manipulate catalogue files.

### 2.4. External Data Repository

The external data repository manages the persistence of intermediate information retrieved from external providers.

Its responsibilities include:

- Resolving the storage location of intermediate data.
- Reading and writing external data files.
- Validating data before it is accepted.
- Applying the relevant persistence and freshness rules.
- Ensuring that invalid incoming data does not replace valid existing data.

External data is stored separately from the reference catalogue.

The repository does not communicate with external providers. It is responsible for persistence, not data acquisition.

The precise file organization and freshness policy depend on the type of external data being stored.

In particular, intermediate market data and daily quotes must not be treated as the same resource:

- Market data is an intermediate input to asset enrichment.
- Quotes are persistent market observations used by valuation calculations.

### 2.5. External Provider Adapters

External provider adapters isolate communication with third-party data sources.

For example, `MarketDataYahooFinance` is responsible for interacting with Yahoo Finance.

Its responsibilities include:

- Requesting information from the provider.
- Retrieving provider responses.
- Extracting relevant information.
- Converting provider-specific responses into application-level data representations.

An adapter must not manage the asset catalogue or its persistence.

It must not decide whether retrieved information should be integrated into an asset definition.

These decisions belong to the application service and the relevant processing components.

Provider adapters should remain independent of the storage format used by Patrimonia.

### 2.6. Data Transformation

External data must be transformed before it can be integrated into the asset catalogue.

This transformation is distinct from both data acquisition and persistence.

For market data enrichment, the transformation component is responsible for:

- Mapping external fields to catalogue fields.
- Transferring compatible information.
- Preserving catalogue information not provided by the external source.
- Converting values into the units and representations expected by the catalogue.
- Updating relevant market data metadata, such as the last update date.

The transformation should be independent of the external provider and should not perform filesystem operations.

It receives structured data and returns a transformed asset representation.

The service orchestrates this transformation and delegates persistence to the asset repository.

### 2.7. Models

Pydantic models provide typed representations of the data manipulated inside Patrimonia.

The asset-related models include:

- `Asset`: the internal representation of an asset definition.
- `AggregatedScrapedAsset`: the representation of aggregated external information, where this model is used by the current implementation.

The models provide:

- Typed fields.
- Consistent object representations.
- Attribute-based access.
- Construction and serialization.
- Validation of model-level constraints.

Models must remain independent of storage and external communication.

They do not resolve filesystem paths, access networks, or read and write files.

Provider-specific representations should be converted before they reach the business models.

### 2.8. Validation

Patrimonia uses JSON Schema and Pydantic for complementary validation purposes.

#### JSON Schema: persisted data validation

JSON Schemas define the expected structure of persisted data.

They are used at data access boundaries to check:

- Required fields.
- Data types.
- Structural constraints.
- Compliance with the expected storage format.

Validation is performed through the application's validation mechanisms, such as `SchemaValidator`.

Schema definitions are resources, separate from the Python code that loads and applies them.

#### Pydantic: internal data representation

Pydantic models define the typed Python objects used inside the application.

They provide a consistent representation and enforce model-level constraints.

They do not replace JSON Schema validation.

The distinction is:

- JSON Schema validates the structure of persisted data.
- Pydantic provides the internal typed representation of application data.

Both mechanisms can be used together at the boundaries between external data and the application.

### 2.9. Configuration and Dependency Injection

The bootstrap layer assembles the dependencies required by asset-related services.

For example, the asset service may require:

- Asset repositories.
- External data repositories.
- Schema loaders and validators.
- External provider adapters.
- Transformation components.
- Configuration and path resolution services.

The bootstrap layer creates these components and injects them into the service.

The service does not instantiate its own infrastructure dependencies.

This approach improves separation of concerns and makes unit testing easier, since concrete dependencies can be replaced with test doubles.

## 3. Application Workflows

### 3.1. Market Data Collection: Fetch

Market data collection retrieves external information from a provider and stores it as intermediate data.

The workflow is:

```text
CLI
 |
 v
AssetService
 |
 +--> AssetRepository
 |       |
 |       +--> Load asset definition
 |       +--> Retrieve provider configuration
 |
 +--> External Provider Adapter
 |       |
 |       +--> Request provider data
 |       +--> Retrieve and normalize response
 |
 +--> External Data Repository
         |
         +--> Validate collected data
         +--> Apply persistence rules
         +--> Store intermediate data
```

The collection operation does not modify the asset catalogue.

It only stores intermediate data when the incoming data satisfies the applicable validation and persistence rules.

### 3.2. Market Data Enrichment: Enrich

Enrichment integrates validated external information into the reference asset catalogue.

The workflow is:

```text
CLI
 |
 v
AssetService
 |
 +--> External Data Repository
 |       |
 |       +--> Load intermediate market data
 |
 +--> AssetRepository
 |       |
 |       +--> Load current asset definition
 |
 +--> Transformation Component
 |       |
 |       +--> Map compatible fields
 |       +--> Preserve existing catalogue information
 |       +--> Normalize values
 |
 +--> AssetRepository
         |
         +--> Validate resulting asset data
         +--> Persist updated asset definition
```

Enrichment is distinct from collection.

The external data is first retrieved and stored. It is then processed and integrated into the catalogue.

The catalogue remains the reference source for asset definitions.

### 3.3. Factsheet Processing: Extract and Enrich

Factsheets follow a different workflow because they are acquired manually rather than through a standardized provider API.

The workflow consists of two separate operations.

**Extract**

The extraction operation reads a locally available factsheet, typically a PDF, and produces structured intermediate data.

```text
Factsheet PDF
     |
     v
Extraction
     |
     v
Intermediate YAML
```

The intermediate YAML can be inspected and corrected before integration.

Extraction does not modify the asset catalogue.

**Enrich**

The enrichment operation reads the intermediate factsheet data, validates it, transforms it into the expected asset representation, and updates the catalogue.

```text
Intermediate YAML
       |
       v
Validation and transformation
       |
       v
Asset model
       |
       v
AssetRepository
       |
       v
Asset Catalogue
```

There is no generic `fetch factsheet` operation because factsheets are manually acquired.

### 3.4. Quote Collection: Fetch

Quotes are retrieved independently from asset enrichment.

The workflow is:

```text
CLI
 |
 v
Quote Service
 |
 +--> AssetRepository
 |       |
 |       +--> Load asset definition
 |       +--> Retrieve provider identifier
 |
 +--> Quote Provider Adapter
 |       |
 |       +--> Retrieve daily closing observations
 |
 +--> Quote Repository
         |
         +--> Validate quote data
         +--> Store annual YAML file
```

The quote repository stores observations under the shared asset directory:

```text
external-data/
└── assets/
    └── <CATEGORY_PATH>/
        └── <ID_ASSET>/
            └── quotes/
                ├── <YYYY>_<ID_ASSET>_quote.yaml
                └── ...
```

The storage convention is configured centrally through `config_app.yaml`.

Each annual file contains a header and a collection of daily observations.

The header records the asset identifier, provider, provider identifier, currency, frequency, quote field, source, and retrieval timestamp.

The observations contain the trading date and the selected closing quote.

Quotes are shared across users and are not copied into individual wallet directories.

Fetching quotes does not modify the asset catalogue.

## 4. Separation of Responsibilities

The following table summarizes the main responsibilities involved in asset management.

| Operation | Responsible component | Responsibility |
|---|---|---|
| Load asset | Asset repository | Read and validate catalogue data |
| Collect market data | Provider adapter | Communicate with the external provider |
| Store market data | External data repository | Validate and persist intermediate data |
| Enrich asset | Service and transformation component | Orchestrate and transform external information |
| Persist enriched asset | Asset repository | Validate and update catalogue data |
| Extract factsheet | Extraction component | Convert a local document into structured data |
| Fetch quotes | Quote provider adapter | Retrieve daily closing observations |
| Store quotes | Quote repository | Validate and persist shared quote data |

The exact component names and implementation boundaries should reflect the current source code. The table describes the intended separation of responsibilities.

## 5. Architectural Guidelines

The following rules should be maintained as the asset management functionality evolves:

1. The asset catalogue remains separate from external market observations.
2. External market data is collected before it is integrated into the catalogue.
3. Factsheet extraction and catalogue enrichment remain separate operations.
4. Quotes are stored independently from asset definitions.
5. Quotes are shared across users and are not stored in user-specific directories.
6. Provider-specific communication remains isolated in adapters.
7. Repositories encapsulate data access and persistence.
8. Services orchestrate application operations without handling low-level I/O.
9. Transformations remain independent of file storage and external providers.
10. Dependencies are assembled in the bootstrap layer.

These principles preserve the separation between reference data, external information, market observations, and application processing.