# Testing Strategy

## 1. Purpose

Automated tests ensure the reliability, correctness and maintainability of Patrimonia.

The testing strategy aims to:
- Verify domain behavior and business rules.
- Ensure that application components work correctly together.
- Validate data loading, validation and persistence workflows.
- Check CLI commands and their expected behavior.
- Prevent regressions when the application evolves.

Tests should be organized according to the application's architecture and responsibilities.

The testing strategy should remain proportionate to the project's scope. It should provide sufficient coverage without introducing unnecessary testing infrastructure or excessive complexity.

## 2. Testing Principles

The test suite follows these principles.

### 2.1. Test Each Layer Independently

Each application layer should be tested according to its responsibilities.

| Layer | Main testing objectives |
|---|---|
| Models | Domain behavior, attributes and business invariants |
| Repositories | Data loading, validation and persistence |
| Adapters | External integrations and format-specific operations |
| Services | Use-case orchestration and business workflows |
| CLI | Command arguments, execution and terminal output |

A test should focus on the behavior of the component under test rather than reproduce the implementation.

### 2.2. Isolate Tests

Tests must be independent of:
- The developer's personal data.
- Files outside the test environment.
- External services and network availability.
- Execution order.
- Previously generated results.

Temporary directories and test fixtures should be used whenever file access is required.

External services should be replaced with controlled test doubles in unit tests.

### 2.3. Preserve User Data

Tests must never modify actual user input files.

All test data must be created in temporary directories or dedicated test fixtures.

In particular:
- Input Excel files must remain unchanged.
- Reference catalogue fixtures must not be modified unexpectedly.
- Generated files must remain within the test environment.
- Tests must not depend on real user identifiers or financial information.

### 2.4. Test Observable Behavior

Tests should verify public behavior and documented contracts.

They should avoid relying unnecessarily on:
- Private implementation details.
- Internal method call sequences.
- Incidental object representations.
- Specific implementation choices that may change without affecting behavior.

## 3. Types of Tests

Patrimonia uses three main categories of automated tests.

### 3.1. Unit Tests

Unit tests verify individual components in isolation.

They should be fast, deterministic and independent of external systems.

Examples include:

**Model tests**
- Valid and invalid model construction.
- Domain invariants.
- Derived properties.
- Transaction behavior.
- Balance behavior.

**Validation tests**
- JSON Schema validation.
- Business rule evaluation.
- Reference validation.
- Inheritance resolution.
- Error reporting.

**Service tests**
- Use-case orchestration.
- Correct handling of repository results.
- Error propagation.
- Business workflow decisions.

Dependencies should be replaced with mocks, stubs or fakes when isolation is required.

### 3.2. Integration Tests

Integration tests verify that several components work correctly together.

They should cover the main data and application workflows.

Examples include:
- YAML loading and inheritance resolution.
- Repository loading and validation.
- Repository persistence.
- Excel reading and writing.
- Transaction enrichment.
- Balance calculation.
- External data collection and integration.

Integration tests may use real temporary files and real implementations of local components.

External network services should normally be replaced by controlled responses or fixtures.

### 3.3. CLI Tests

CLI tests verify the behavior exposed to users.

They should cover:
- Command availability.
- Argument parsing.
- Required and optional arguments.
- Command execution.
- Terminal output.
- Exit codes.
- Error messages.

CLI tests should invoke commands through the CLI testing facilities rather than directly testing only their underlying Python functions.

The tests should verify that commands delegate work to the appropriate application components.

## 4. Test Organization

Tests are stored in the top-level `tests/` directory.

The test structure should reflect the responsibilities of the application.

An illustrative organization is:

```text
tests/
├── conftest.py
│
├── test_models/
│   ├── test_account.py
│   ├── test_asset.py
│   ├── test_wallet.py
│   ├── test_transaction.py
│   └── test_balance.py
│
├── test_validation/
│   ├── test_schema_loader.py
│   ├── test_schema_validator.py
│   ├── test_rule_loader.py
│   ├── test_rule_validator.py
│   └── test_reference_validator.py
│
├── test_repositories/
│   ├── test_asset_repository.py
│   ├── test_scraped_data_repository.py
│   └── test_wallet_repository.py
│
├── test_adapters/
│   ├── test_yahoo_finance_adapter.py
│   └── test_transaction_excel_reader.py
│
├── test_services/
│   ├── test_asset_service.py
│   ├── test_transaction_service.py
│   └── test_balance_service.py
│
└── test_cli/
    ├── test_asset_commands.py
    ├── test_account_commands.py
    ├── test_user_commands.py
    └── test_wallet_commands.py
```

This structure is a logical organization rather than a requirement to create every directory immediately.

Test modules should be introduced as the corresponding application components are implemented.

### 4.1. Shared Fixtures

The `tests/conftest.py` file contains fixtures shared by multiple test modules.

Typical fixtures include:
- Temporary directories.
- Temporary configuration files.
- Test catalogue definitions.
- Valid and invalid YAML examples.
- Test Excel workbooks.
- Mocked external service responses.

Fixtures used by only one test module should preferably remain local to that module.

## 5. Test Data and Temporary Files

Tests should use small, explicit and representative datasets.

Fixtures should cover both valid and invalid cases.

### 5.1. YAML Fixtures

YAML fixtures should cover:
- Valid catalogue definitions.
- Missing required properties.
- Invalid property types.
- Invalid references.
- Inheritance through `extends`.
- Child properties overriding parent properties.
- Invalid inherited definitions.

Fixtures should be sufficiently small to make test failures easy to understand.

### 5.2. Excel Fixtures

Excel fixtures should be generated or copied into temporary directories.

Transaction workbooks should cover:
- Valid `header` and `data` worksheets.
- Missing worksheets.
- Missing or unexpected columns.
- Invalid dates and numeric values.
- Empty transaction datasets.
- Invalid transaction actions.
- Invalid transaction relationships.

Balance workbooks should cover equivalent structural and data validation cases.

Tests must not depend on manually maintained files outside the test environment.

### 5.3. Deterministic Test Data

Test data should be deterministic.

Tests should avoid depending on:
- Current market prices.
- Live exchange rates.
- Current external API responses.
- The current date, unless the date is explicitly controlled.
- Random values without a fixed seed.

When a test depends on a date, the reference date should be explicitly provided or controlled.

## 6. Domain Model Testing

Domain models should be tested independently of their storage formats.

### 6.1. Asset and Account

Tests should verify:
- Valid model construction.
- Required attributes.
- Expected types.
- Domain invariants.
- Derived properties and helper methods.

### 6.2. Wallet

Tests should verify:
- Valid wallet construction.
- Required attributes.
- Account references.
- Associated wallet information.
- Domain behavior exposed by the model.

Storage-specific behavior should be tested through the appropriate repository or adapter.

### 6.3. Transaction

Transaction tests should cover:
- Supported actions.
- Required attributes.
- Valid and invalid values.
- Transaction relationships.
- Calculated PRU fields in enriched transactions.
- Relevant domain invariants.

The weighted-average cost basis calculation should be tested with representative sequences of purchases and sales.

Expected results should be calculated independently of the implementation under test.

### 6.4. Balance

Balance tests should cover:
- Valid balance construction.
- Position data.
- Balance dates.
- Official and calculated balance distinctions.
- Relevant domain invariants.

The detailed calculation of balances should be tested separately through the corresponding service.

## 7. Data Validation Testing

The catalogue validation pipeline must be tested as a complete sequence and through its individual components.

The expected sequence is:

```text
YAML loading
    |
    v
Inheritance resolution
    |
    v
JSON Schema validation
    |
    v
Business rules validation
    |
    v
Pydantic model construction
    |
    v
Validated application model
```

Tests should verify:
- YAML parsing errors.
- Correct inheritance resolution.
- JSON Schema validation errors.
- Business rule violations.
- Cross-reference validation.
- Pydantic model construction.
- Clear and actionable error messages.

Business rules should only be evaluated when structural validation succeeds.

Repository integration tests should verify that the complete pipeline is correctly orchestrated.

## 8. Transaction and Balance Workflow Testing

Transaction enrichment and balance calculation are important application workflows and require dedicated integration tests.

### 8.1. Transaction Enrichment

Enriched transactions are fully regenerated from validated user input whenever a command triggers the calculation.

Tests should verify:
- Loading of validated source transactions.
- Correct transaction normalization.
- Generation of required counterpart transactions.
- Transaction relationship validation.
- PRU calculation.
- YAML output generation.
- Correct error handling when source data is invalid.

The calculation must not use previously generated enriched transactions as an input.

Tests should also verify that user input files remain unchanged.

### 8.2. Balance Calculation

Balance calculation uses:
- The applicable official balance.
- Enriched transactions.
- The requested target date.

Tests should verify:
- Selection of the appropriate official balance.
- Application of transactions within the relevant date range.
- Correct handling of transactions occurring on the reference date.
- Position calculation.
- Output generation.
- Handling of missing or invalid prerequisites.

The detailed financial calculation rules should be documented in the relevant domain and application documentation.

Tests must verify those documented rules rather than introduce additional assumptions.

## 9. External Integration Testing

External integrations must be tested without depending on live services.

For example, the Yahoo Finance adapter should be tested with controlled responses representing:
- Successful retrieval.
- Empty responses.
- Missing fields.
- Invalid values.
- Network failures.
- Unexpected provider responses.

Tests should verify the conversion of provider data into the application's expected data structures.

The collection and catalogue enrichment workflows should also be tested independently.

An integration test may use a local fixture to simulate collected market data and verify its persistence and subsequent integration into the asset catalogue.

## 10. CLI Testing

CLI tests should verify the public command interface.

For example, asset management tests should cover commands such as:

```bash
patrimonia asset list

patrimonia asset --id <ID_ASSET> show

patrimonia asset --id <ID_ASSET> check

patrimonia asset --id <ID_ASSET> fetch market-data

patrimonia asset --id <ID_ASSET> enrich market-data
```

Tests should verify:
- Correct command registration.
- Correct argument interpretation.
- Expected output for successful operations.
- Clear messages for missing resources.
- Appropriate handling of invalid input.
- Non-zero exit codes when commands fail.
- No unintended modification of user input data.

CLI tests should use temporary configurations and test directories.

They should not require the developer's actual catalogue or user data.

## 11. Test Execution

Tests are executed using the project's configured test runner.

If `pytest` is used, the complete test suite can be run with:

```bash
pytest
```

A specific test module can be executed with:

```bash
pytest tests/test_models/test_transaction.py
```

A specific test can be selected with:

```bash
pytest tests/test_models/test_transaction.py -k weighted_average
```

Coverage can be measured with:

```bash
pytest --cov=finance_cli --cov-report=term-missing
```

These commands assume that `pytest` and the corresponding coverage plugin are configured as project development dependencies.

The exact test commands should remain aligned with `pyproject.toml`.

## 12. Continuous Quality Checks

Before considering a feature complete, the relevant checks should be executed.

The expected quality checks include:
- Automated tests.
- Static analysis and linting.
- Type checking, where configured.
- Formatting checks.
- Validation of relevant resource files.

The exact tools and commands are defined by the project configuration.

A feature should not be considered complete merely because its CLI command works manually.

Its expected behavior, error cases and interactions with other application components must also be tested.

## 13. Testing Priorities

Testing effort should follow the importance and risk of each feature.

The recommended priorities are:

| Priority | Area | Main objective |
|---|---|---|
| Very high | Domain models and validation | Protect data correctness |
| Very high | Repositories | Ensure reliable data access and persistence |
| High | Transaction enrichment | Ensure correct financial processing |
| High | Balance calculation | Ensure reliable position calculations |
| High | CLI | Protect the public command interface |
| High | External adapters | Handle provider failures safely |
| Medium | Dashboard generation | Ensure correct HTML and chart generation |

Critical financial calculations and data validation should receive particular attention.

## 14. Definition of Done

A feature is considered complete when:

- Its responsibilities are consistent with the application architecture.
- Its expected behavior is implemented.
- Relevant unit tests are present.
- Relevant integration tests are present where components interact.
- CLI tests are present when the feature exposes a command.
- Error cases are handled and tested.
- User input data is preserved.
- Documentation is updated when public behavior or architectural decisions change.
- All relevant quality checks pass.

**Guiding principle:** tests are part of the implementation, not a final verification step. Each feature should be developed together with the tests that establish its expected behavior.