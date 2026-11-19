# SchemaValidator

## Purpose

`SchemaValidator` validates the structure of a data document against a JSON Schema.

It ensures that a document conforms to its expected structure before business rules are evaluated or a typed application model is constructed.

Typical use cases include validating asset and contract catalog documents.

Its responsibility is limited to structural validation. It does not load schemas, resolve YAML inheritance, or evaluate business rules.

## Role in the Validation Architecture

Structural validation is one step in the catalog validation pipeline:

```text
Repository
    │
    ├── YAML loading and inheritance resolution
    │
    ├── SchemaLoader
    │       └── Loads the applicable JSON Schema
    │
    ├── SchemaValidator
    │       └── Structural validation (JSON Schema)
    │
    ├── RuleLoader
    │       └── Loads and merges business rules
    │
    ├── RuleValidator
    │       └── Business-rule validation
    │
    └── Pydantic model construction
            └── Validated application model
```

The `Repository` orchestrates the pipeline and ensures that each validation step is executed in the appropriate order.

The responsibilities of the components are distinct:

- `SchemaLoader` loads the JSON Schema applicable to the document.
- `SchemaValidator` checks the document against that schema.
- `RuleLoader` loads business-rule definitions, resolves inheritance, and merges inherited rules.
- `RuleValidator` evaluates business rules against the document.

Business-rule validation is performed only if structural validation succeeds.

## Schema Format

Schemas are defined using JSON Schema Draft 2020-12.

Although JSON Schema is a JSON-based specification, schema definitions are stored in YAML files in Patrimonia.

The schema resources are organized under:

```text
resources/
└── schemas/
    └── ...
```

For catalog documents, schemas are organized according to the relevant domain and document category.

A schema defines the expected structure of a document, including:

- Required properties.
- Property types.
- Allowed values and enumerations.
- Nested object structures.
- Array item definitions.
- Numeric and string constraints.
- Additional-property restrictions.

Example:

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
type: object

required:
  - isin
  - general_info

properties:
  isin:
    type: string
    minLength: 1

  general_info:
    type: object
    required:
      - name
    properties:
      name:
        type: string
      ter:
        type: number
        minimum: 0

additionalProperties: false
```

The schema describes structural constraints. Domain-specific conditions that cannot be adequately expressed through JSON Schema belong in business rules.

## Usage

```python
from finance_cli.validation.schema_validator import SchemaValidator

validator = SchemaValidator()
issues = validator.validate(data=asset_data, schema=schema)

if issues:
    # Handle validation errors
    ...
```

### Input

| Parameter | Type | Description |
|---|---|---|
| `data` | `dict` | Data document to validate, typically after YAML loading and inheritance resolution. |
| `schema` | `dict` | JSON Schema definition, typically returned by `SchemaLoader`. |

### Return value

The method returns a `list[str]`:

- An empty list indicates that the document conforms to the schema.
- A non-empty