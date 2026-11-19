# Software Architecture: Layers and Responsibilities

## 1. Architectural Principles

Patrimonia follows a layered architecture that separates business logic from technical implementation details.

Each component has a clearly defined responsibility. Dependencies are oriented towards abstractions wherever practical, allowing business operations to remain independent of storage formats and external providers.

The main principles are:

| Layer | Responsibility |
|---|---|
| Common infrastructure | Provides generic, low-level technical utilities |
| YAML infrastructure | Implements reusable YAML-specific mechanisms |
| Configuration | Loads and exposes application settings |
| Models | Represent business concepts and structured application data |
| Validation | Implements structural and business-data validation |
| Adapters | Handle technical integration with storage formats and external providers |
| Repositories | Provide the application's data access and persistence boundary |
| Services | Implement and orchestrate application use cases |
| CLI | Exposes application use cases to users |
| Bootstrap | Assembles application components and injects dependencies |

### Dependency direction

The intended dependency structure is:

```text
                       CLI
                        |
                        v
                     Services
                        |
                        v
             Repository / Provider
                  abstractions
                        ^
                        |
                 Implementations
                  /           \
           Repositories      Adapters
                  |             |
                  +------ +-----+
                         |
                  Technical I/O
                 YAML / Excel / APIs

             Models and Validation
             are used at the
             appropriate boundaries.

             Bootstrap assembles
             the application graph.
```

The diagram illustrates architectural dependencies rather than a strict runtime call sequence.

Services depend on repository or provider abstractions, not on concrete storage implementations. Repositories coordinate data access and persistence, delegating format-specific operations to adapters where appropriate.

Adapters translate between external representations and application data structures. Validation components enforce structural and business constraints at the relevant data boundaries.

The bootstrap layer is responsible for connecting concrete implementations to the abstractions used by application services.

## 2. Project Package Structure

The following structure describes the logical organization of the `finance_cli` package.

```text
finance_cli/
│
├── bootstrap/                  # Application assembly and dependency injection
│   └── ...
│
├── config/                     # Application configuration
│   ├── app_config.py           # Configuration loading and access
│   └── ...
│
├── common/                     # Generic technical utilities
│   ├── yaml_io.py              # YAML serialization and deserialization
│   ├── merge.py                # Generic dictionary operations
│   └── ...
│
├── yaml/                       # YAML-specific infrastructure
│   ├── inheritance.py          # YAML inheritance resolution
│   └── ...
│
├── models/                     # Business and application data models
│   ├── asset.py
│   ├── account.py
│   ├── wallet.py
│   ├── transaction.py
│   └── ...
│
├── validation/                 # Structural and business validation
│   ├── schema_loader.py
│   ├── schema_validator.py
│   └── ...
│
├── adapters/                   # Storage and external integrations
│   ├── yaml/
│   │   └── ...
│   ├── excel/
│   │   └── ...
│   ├── api/
│   │   └── ...
│   └── ...
│
├── repositories/               # Data access and persistence
│   └── ...
│
├── services/                   # Application use cases
│   ├── asset_service.py
│   ├── portfolio_service.py
│   ├── calculation_service.py
│   └── ...
│
└── cli/                        # Command-line interface
    └── ...
```

The corresponding `resources/` directory contains non-code application resources, such as:

```text
resources/
├── schemas/
├── rules/
├── templates/
└── styles/
```

This is a logical organization. Packages should only be introduced when they provide a clear separation of responsibilities. Unnecessary package fragmentation should be avoided.

## 3. Layer Responsibilities

### 3.1 Common

`common` contains generic, low-level technical utilities.

Examples include:

- YAML serialization and deserialization.
- Generic dictionary operations.
- Reusable technical helpers.

These utilities must not depend on Patrimonia business models or application services.

They should remain independent of the rest of the application and reusable wherever appropriate.

### 3.2 YAML Infrastructure

The `yaml` package contains reusable YAML-specific mechanisms that go beyond basic serialization.

Examples include:

- Resolving `extends` references.
- Loading inherited YAML definitions.
- Applying the project's YAML inheritance conventions.

It may use utilities from `common`, such as YAML loading and dictionary merging.

It must not depend on business models, adapters, repositories or services.

Its responsibility is to resolve YAML structures, not to interpret their business meaning.

### 3.3 Configuration

`config` handles application configuration loading and access.

Its responsibilities include:

- Loading the application configuration.
- Exposing validated configuration values.
- Providing configuration structures to the bootstrap layer.

Configuration is loaded once during application startup.

The bootstrap layer is the sole component responsible for resolving configured relative paths against `app.base_dir`. It passes resolved absolute paths to the components that need them.

Repositories, services and adapters must not independently reload the global configuration or determine the application base directory.

### 3.4 Models

`models` contains business and application data models.

Examples include:

- Assets.
- Accounts.
- Wallets.
- Transactions.
- Balances.
- External data representations.

Models represent business concepts independently of their physical storage.

They may enforce domain invariants and provide typed representations of application data.

They must remain independent of:

- Filesystems.
- YAML and Excel formats.
- External APIs.
- Adapters.
- Repositories.
- Application services.
- Application configuration.

Where external data requires a separate representation, dedicated data models should be used rather than coupling business models to provider-specific structures.

A model should not need to know where or how its data is stored.

### 3.5 Validation

`validation` provides structural and business-data validation mechanisms.

Its responsibilities include:

- Loading JSON Schema definitions.
- Performing structural validation.
- Evaluating business validation rules.
- Supporting cross-reference validation where required.

JSON Schema definitions and other validation resources are stored separately from the Python implementation, under `resources/schemas/` and `resources/rules/`.

Patrimonia uses JSON Schema Draft 2020-12. The `x-reference` keyword is a Patrimonia-specific extension.

Validation components may use models or model abstractions where necessary, but must not depend on adapters, repositories or services.

Repositories invoke the relevant validation components at data-access boundaries. Validation logic itself remains separate from repository persistence logic.

### 3.6 Adapters

`adapters` isolate external systems, storage formats and technical integrations from the rest of the application.

Their responsibilities include:

- Reading and writing external representations.
- Translating external data into application representations.
- Translating application data into external representations.
- Communicating with external providers and APIs.
- Handling provider-specific protocols and technical details.

Examples include:

- YAML format adapters.
- Excel readers and writers.
- External financial data provider integrations.

Adapters may use `common`, YAML infrastructure, configuration values, models and validation mechanisms as required.

They must not depend on application services or orchestrate complete business use cases.

An adapter focuses on technical translation and integration, not on deciding which application workflow should be executed.

### 3.7 Repositories

Repositories provide the application's data access and persistence boundary.

They encapsulate the retrieval and persistence of application data and hide underlying storage mechanisms from services.

Their responsibilities include:

- Locating and retrieving data using injected storage configuration.
- Delegating format-specific operations to adapters.
- Coordinating structural and business validation at data boundaries.
- Returning validated application representations.
- Persisting validated data.
- Managing replacement of calculated results after successful processing.

Repositories must preserve the distinction between reference data, user input data and calculated data.

They receive resolved paths and storage settings during application assembly. They must not independently load the global configuration or resolve paths against the current working directory.

Repositories do not implement application workflows or financial calculations.

### 3.8 Services

`services` implements application use cases.

Their responsibilities include:

- Orchestrating business operations.
- Applying business rules.
- Coordinating repositories and external provider abstractions.
- Triggering financial calculations.
- Managing the sequence of operations required by a use case.

Examples include:

- Asset data collection and catalogue enrichment.
- Factsheet extraction and catalogue enrichment.
- Transaction validation and enrichment.
- Balance calculation.
- Wealth evolution generation.
- Dashboard generation.

Services receive their dependencies through dependency injection.

They must not:

- Construct their own infrastructure dependencies.
- Directly read or write YAML or Excel files.
- Resolve filesystem paths.
- Reload application configuration.
- Depend on concrete storage implementation details.

Services focus on what the application needs to accomplish, not on the technical details of how data is accessed.

### 3.9 CLI

`cli` provides the user-facing command-line interface.

Its responsibilities include:

- Defining commands and options.
- Parsing user input.
- Performing basic command and argument checks.
- Calling the appropriate application services.
- Displaying results and errors.
- Returning appropriate exit codes.

The CLI follows the public action vocabulary defined in CLI Conventions:

- `list`
- `show`
- `check`
- `calculate`
- `retrieve`
- `extract`
- `upgrade`

Not every action applies to every resource.

The CLI must not implement business logic, perform financial calculations or access repositories and adapters directly.

### 3.10 Bootstrap

`bootstrap` is the application's composition root: the single place responsible for assembling the application dependency graph.

Its responsibilities include:

- Loading and validating application configuration.
- Resolving configured relative paths against `app.base_dir`.
- Creating repositories and adapters.
- Creating services and factories where required.
- Injecting dependencies.
- Providing configured application entry points to the CLI.

Bootstrap is the only component responsible for constructing the application's infrastructure dependencies and connecting concrete implementations to their abstractions.

Services and CLI commands must not construct their own dependencies.

## 4. Dependency Rules

The following table summarizes the intended dependency constraints.

| Component | May depend on | Must not depend on |
|---|---|---|
| `common` | Standard library and generic technical libraries | Business and application packages |
| `yaml` | `common`, generic YAML libraries | Models, adapters, repositories, services |
| `config` | `common`, generic configuration libraries | Models, adapters, repositories, services |
| `models` | Standard library and minimal generic dependencies | I/O, adapters, repositories, services, config |
| `validation` | `common`, schema libraries, model abstractions where necessary | Adapters, repositories, services |
| `adapters` | Models, common, YAML infrastructure, configuration values, validation | Services, repositories |
| `repositories` | Models, adapters, validation, storage abstractions | Services and CLI |
| `services` | Models, repository and provider abstractions, factories where required | Concrete I/O implementation details |
| `cli` | Services and application entry points | Adapters and repositories directly |
| `bootstrap` | Components required to assemble the application | Business workflow implementation |

These rules describe architectural dependencies, not necessarily the exact Python import graph.

Interfaces should be placed where they can be used without introducing circular dependencies. For example, repository and provider contracts should be accessible to services without requiring them to import concrete infrastructure implementations.

## 5. Factories

### 5.1 Purpose

A Factory is a construction component responsible for creating objects according to defined construction rules.

It is useful when object creation:

- Requires several coordinated steps.
- Involves non-trivial configuration or dependency resolution.
- Must consistently enforce construction rules.
- Is repeated across several parts of the application.

A Factory should not be introduced simply because two services contain a few similar lines of code.

The objective is to centralize genuinely reusable construction logic without adding unnecessary abstractions.

### 5.2 Factory vs. Service

A Service and a Factory have different responsibilities.

| Aspect | Service | Factory |
|---|---|---|
| Main role | Execute an application use case | Construct an object |
| Main question | How should this operation be performed? | How should this object be created correctly? |
| Business logic | Orchestration, rules and calculations | Construction rules and initialization |
| Side effects | May read, write or call external systems through dependencies | Preferably limited to object construction |
| Lifetime | Usually associated with the application lifecycle or a use case | Used when an object needs to be created |
| Dependencies | Repositories, providers and other services | Configuration and construction dependencies |

A Factory may perform controlled reference resolution or initialization when these operations are necessary to construct a valid object. It must not become responsible for orchestrating an entire application workflow.

### 5.3 When to Introduce a Factory

Introduce a Factory when it provides a clear benefit, for example:

- Several services need to construct the same complex object.
- Construction requires resolving references or inheritance.
- Object creation follows a multi-step process.
- Construction rules would otherwise be duplicated or scattered.

Do not introduce a Factory when:

- Object creation is straightforward.
- A simple constructor is sufficient.
- The abstraction would only move a few lines of code without improving clarity.

### 5.4 Factory and Dependency Injection

Factories do not replace dependency injection or bootstrap.

The bootstrap layer remains responsible for creating the Factory and injecting its dependencies.

A Factory may itself be injected into a service when object construction is part of a use case.

For example:

```text
Bootstrap
   |
   +--> AssetFactory
   |       |
   |       +--> Required construction dependencies
   |
   +--> AssetRepository
   |
   +--> AssetService
           |
           +--> AssetFactory
           |
           +--> AssetRepository
```

The service uses the Factory to create an object when required, while bootstrap remains responsible for assembling the Factory and its dependencies.

A Factory must not independently reload application configuration, resolve global filesystem paths or construct unrelated infrastructure components.

The distinction is:

- **Bootstrap:** constructs and wires application dependencies.
- **Factory:** constructs specific business or application objects.
- **Service:** orchestrates application use cases.
- **Repository:** manages data access and persistence.
- **Adapter:** handles technical integration and translation.

This separation keeps object construction explicit without introducing unnecessary architectural complexity.