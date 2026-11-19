# SchemaLoader

## Purpose

`SchemaLoader` is responsible for loading JSON Schema definitions from Patrimonia's schema resources.

It provides the schema definition required by `SchemaValidator` to validate a data document.

Its responsibility is limited to schema discovery, loading, and preparation. It does not validate data documents or evaluate business rules.

## Role in the Validation Architecture

`SchemaLoader` is part of the structural validation workflow:

```text
Repository
    │
    ├── YAML loading and inheritance resolution
    │
    ├── SchemaLoader
    │       └── Loads the applicable JSON Schema
    │
    ├── SchemaValidator
    │       └── Validates the data document
    │
    ├── RuleLoader
    │       └── Loads and merges business rules
    │
    ├── RuleValidator
    │       └── Evaluates business rules
    │
    └── Pydantic model construction
            └── Validated application model
```

The responsibilities of the components are distinct:

- `SchemaLoader` locates and loads the applicable JSON Schema definition.
- `SchemaValidator` evaluates the data document against the loaded schema.
- `RuleLoader` loads business-rule definitions and resolves their inheritance.
- `RuleValidator` evaluates the resulting business rules.

The `Repository` orchestrates these components and controls the validation sequence.

## Schema Resources

JSON Schema definitions are stored as YAML resources under:

```text
resources/
└── schemas/
    └── ...
```

Schemas are organized according to the relevant domain and document category.

For example, a catalog schema may be stored at:

```text
resources/schemas/assets/equities/equities.schemas.yaml
```

The exact resource path depends on the catalog category and the schema organization defined by Patrimonia.

Schema definitions use JSON Schema Draft 2020-12, expressed in YAML.

## Responsibilities

`SchemaLoader` is responsible for:

- Locating the schema resource corresponding to a catalog category.
- Reading the schema definition from its YAML file.
- Parsing the YAML content into a Python data structure.
- Returning the loaded schema to the caller.
- Reporting resource-loading and parsing failures.

It must not:

- Validate a data document against the schema.
- Evaluate business rules.
- Resolve catalog document inheritance through `extends`.
- Merge business-rule definitions.
- Construct Pydantic application models.
- Persist catalog data.

Schema inheritance, if required by the schema resource format, must be distinguished from catalog document inheritance. It should only be implemented by `SchemaLoader` if explicitly supported by the schema resource design.

## Usage

A typical usage is:

```python
from finance_cli.validation.schema_loader import SchemaLoader

loader = SchemaLoader()
schema = loader.load(category="equities")
```

The returned object is a Python dictionary representing the loaded JSON Schema.

The exact method signature and category-resolution mechanism depend on the implementation.

## Loading Workflow

The loading process consists of the following steps:

1. Receive the schema identifier or category required by the caller.
2. Resolve the corresponding schema resource path.
3. Read the YAML file.
4. Parse its content into a Python dictionary.
5. Return the schema definition.

```text
Schema identifier / category
          │
          ▼
Resolve resource path
          │
          ▼
Read YAML file
          │
          ▼
Parse YAML content
          │
          ▼
Return schema definition
```

The resulting schema is passed to `SchemaValidator`, which performs the actual structural validation.

## Error Handling

Schema loading failures must be distinguishable from document validation failures.

Typical loading errors include:

- Schema resource not found.
- Schema file cannot be read.
- Invalid YAML syntax.
- Empty or invalid schema definition.

These errors indicate a problem with Patrimonia's schema resources or their configuration, rather than an invalid catalog document.

A schema definition that is syntactically valid YAML may still be an invalid JSON Schema. Its validity should be checked by the schema-validation infrastructure before it is used to validate data documents.

## Responsibilities and Boundaries

The separation between loading and validation keeps the implementation focused:

| Component | Responsibility |
|---|---|
| `SchemaLoader` | Locate and load JSON Schema definitions. |
| `SchemaValidator` | Validate data documents against loaded schemas. |
| `RuleLoader` | Load and merge business-rule definitions. |
| `RuleValidator` | Evaluate business rules against data documents. |
| `Repository` | Orchestrate loading, validation, model construction, and persistence. |

This separation allows schema resources to be loaded independently of the documents being validated and keeps the validation logic reusable.

## Testing

Tests for `SchemaLoader` should cover:

- Successful loading of an existing schema.
- Correct resolution of schema resource paths.
- Missing schema resources.
- Invalid YAML syntax.
- Empty schema files.
- Invalid schema definitions.
- Correct parsing of YAML schema content into Python dictionaries.

Tests should use controlled schema fixtures rather than relying unnecessarily on the complete application catalog.