# CLI Configuration

## 1. Purpose

The CLI configuration centralizes application settings, storage locations, and file format conventions.

It is loaded once during application startup and used to configure the application components.

The configuration describes **how and where data is stored**. It does not contain business data, reference data, or business rules.

## 2. Configuration File

The main configuration file is:

```text
config/config_app.yaml
```

It is loaded and validated during CLI initialization.

Only the application bootstrap is responsible for:
- Loading the configuration file.
- Validating its structure and values.
- Resolving configured paths.
- Building and injecting application dependencies.

Services, repositories, and adapters must not reload the configuration file independently.

## 3. Design Principles

The configuration follows these principles:

- **Centralization:** application settings and storage conventions are defined in one place.
- **Consistency:** all components use the same configuration.
- **Separation of concerns:** configuration describes storage and application settings, not business rules or business data.
- **Portability:** relative paths are independent of the directory from which the CLI is launched.
- **Explicit formats:** supported file formats and naming conventions are declared.
- **Dependency injection:** components receive the configuration values or dependencies they need rather than accessing the configuration file directly.

## 4. External Data Configuration

The `external` section defines the storage conventions for data shared across users.

### 4.1. Shared Quotes

Historical market quotes are shared across all users and wallets.

They are stored by asset, under the following structure:

```text
external-data/
└── assets/
    └── <CATEGORY_PATH>/
        └── <ID_ASSET>/
            └── quotes/
                └── <YYYY>_<ID_ASSET>_quote.yaml
```

The corresponding configuration is:

```yaml
external:
  assets:
    quotes:
      format: yaml
      filename: <YYYY>_<ID_ASSET>_quote.yaml
      folder: external-data/assets/<CATEGORY_PATH>/<ID_ASSET>/quotes
```

The configuration defines:
- `format`: the storage format.
- `filename`: the naming convention for quote files.
- `folder`: the relative storage path.

These properties describe file storage. The internal structure of quote files is defined separately by the quote data schema.

### 4.2. Quote Data Structure

Each quote file contains a `header` section and a `data` section.

Example:

```yaml
header:
  asset_id: <ID_ASSET>
  provider: yahoo
  provider_id: <PROVIDER_ID>
  currency: EUR
  frequency: daily
  quote_field: close
  source: Yahoo Finance
  retrieved_at: "2025-12-31T18:00:00"

data:
  - date: "2025-12-30"
    close: 123.45
  - date: "2025-12-31"
    close: 124.10
```

The header describes the asset, provider, and retrieval metadata.

The `retrieved_at` timestamp records when the data was retrieved. It is distinct from each observation's `date`, which represents the market date.

Quote data follows these conventions:
- Daily closing prices are stored.
- Non-trading days, such as weekends and market holidays, have no observation.
- Each yearly file contains observations for one calendar year.
- Quote history is shared and is not specific to a user or wallet.

Retrieving quotes updates the shared quote history. It does not automatically modify the reference catalogue.

The detailed quote data schema and validation rules are documented separately.

## 5. Configuration Lifecycle and Application Layers

Configuration handling belongs exclusively to the application bootstrap.

### 5.1. Bootstrap

During startup, the bootstrap:
1. Loads `config/config_app.yaml`.
2. Validates the configuration.
3. Resolves relative paths against `app.base_dir`.
4. Builds repositories, adapters, and services.
5. Injects the required dependencies into the application.

`app.base_dir` is the reference directory for all configured relative paths. Path resolution must therefore produce the same result regardless of the current working directory from which the CLI is launched.

Repositories and adapters receive resolved paths. They must not independently determine the application base directory or resolve configured relative paths.

### 5.2. Services

Services implement application workflows and business rules.

They:
- Use injected repositories and adapters.
- Do not load or parse the configuration file.
- Do not independently resolve storage paths.
- Do not depend on configuration file structure.

### 5.3. Repositories

Repositories are responsible for data access and persistence.

They:
- Use the paths and storage settings provided during initialization.
- Handle the relevant file formats and persistence operations.
- Do not reload the application configuration.
- Do not determine the application base directory.

### 5.4. Adapters

Adapters handle external integrations and technical format conversions.

They receive the configuration values or dependencies required for their responsibilities. They must not independently load the application configuration.

## 6. Configuration Validation

The configuration must be validated during application startup, before application services are used.

Validation covers:

- YAML syntax.
- Required sections and properties.
- Property types and allowed values.
- Supported file formats.
- Filename and folder conventions.
- Consistency between configured storage locations.
- Validity of configured paths.

Configuration properties must be explicitly classified as required, optional, or conditional. Defaults may be used only when documented; they must not silently conceal missing or invalid required values.

Path validation must distinguish between:
- A syntactically valid path.
- An existing directory.
- Read permissions.
- Write permissions.

Directories intended to receive generated files do not necessarily need to exist at startup. They can be created when required by the relevant operation, provided the application has the necessary permissions.

A dedicated command allows users to validate the configuration:

```bash
patrimonia config check
```

Errors must identify the invalid property and explain the expected value or correction. Invalid configuration must not be silently accepted.

## 7. Configuration Evolution

Any change to the configuration must consider:

- The component responsible for using the setting.
- The storage location and file format.
- The impact on existing data.
- Configuration validation requirements.
- Documentation updates.
- Compatibility with existing configurations, where applicable.

New configuration properties should be introduced only when they represent application settings or technical storage conventions.

Business rules, financial calculations, and user-specific financial data must remain outside the configuration.