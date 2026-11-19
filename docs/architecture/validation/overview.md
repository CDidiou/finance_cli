# RuleValidator

## Purpose

`RuleValidator` evaluates business rules defined in `*.rules.yaml` files against a data document.

It typically validates an asset or contract document after structural validation has succeeded.

Its responsibility is limited to evaluating rules. It does not load rule definitions, resolve inheritance, or merge inherited rules.

## Role in the Validation Architecture

The validation pipeline separates structural validation from business-rule validation:

```text
Repository
    │
    ├── YAML loading and inheritance resolution
    │
    ├── SchemaValidator
    │       └── Structural validation (JSON Schema)
    │
    └── RuleValidator
            └── Business-rule validation (*.rules.yaml)
```

The `Repository` orchestrates the validation pipeline.

The responsibilities of the validation components are distinct:

- `SchemaValidator` checks that the document conforms to its JSON Schema.
- `RuleLoader` loads business-rule definitions, resolves `extends`, and merges inherited rules.
- `RuleValidator` evaluates the resulting rules against the data document.

Business rules are evaluated only after structural validation has succeeded.

## Usage

```python
from finance_cli.validation.rule_validator import RuleValidator

validator = RuleValidator()
issues = validator.validate(data=asset_data, rules=rules)

if issues:
    # Handle validation errors
    ...
```

### Input

| Parameter | Type | Description |
|---|---|---|
| `data` | `dict` | Data document to validate, typically after YAML loading and inheritance resolution. |
| `rules` | `list[dict]` | Business rules returned by `RuleLoader.load(...)`. |

### Return value

The method returns a `list[str]`:

- An empty list indicates that all rules passed.
- A non-empty list contains human-readable validation error messages.

The validator does not raise an exception for ordinary rule violations; it reports them through the returned list.

## Rule Definition Format

Each rule is defined as a YAML mapping.

```yaml
- id: ter_non_negative
  description: "The TER must be greater than or equal to zero"
  path: "general_info.ter"
  type: gte
  value: 0
```

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Unique identifier for the rule within the effective rule set. |
| `description` | Yes | Human-readable explanation of the rule. |
| `path` | Depends on rule type | Path to the data evaluated by the rule. |
| `type` | Yes | Rule type identifying the validation operation. |
| Other fields | Depends on rule type | Parameters required by the selected rule type. |

Rule identifiers must be unique within the effective rule set after inheritance and merging have been resolved by `RuleLoader`.

## Supported Rule Types

The following rule types are supported:

| Type | Parameters | Description |
|---|---|---|
| `sum_equals` | `path`, `fields`, `value`, `tolerance?` | Checks that the sum of the specified values equals the expected value, within an optional tolerance. |
| `required` | `path` | Checks that the specified field exists and is not empty. |
| `gt` | `path`, `value` | Checks that a numeric value is strictly greater than the expected value. |
| `gte` | `path`, `value` | Checks that a numeric value is greater than or equal to the expected value. |
| `lt` | `path`, `value` | Checks that a numeric value is strictly less than the expected value. |
| `lte` | `path`, `value` | Checks that a numeric value is less than or equal to the expected value. |
| `min_items` | `path`, `value` | Checks that a list contains at least the specified number of items. |
| `in` | `path`, `values` | Checks that a value belongs to the specified set of allowed values. |
| `date_before_today` | `path` | Checks that a date is strictly earlier than the current date. |
| `required_with` | `path`, `if_field`, `required_fields` | Requires specified fields when the condition field is present. |

## Rule Examples

### `sum_equals`

Checks that the sum of several values matches an expected total.

```yaml
- id: risk_allocation_sum
  path: "py_finance.risk"
  type: sum_equals
  fields:
    - low_risk
    - mid_risk
    - high_risk
  value: 100
  tolerance: 0.01
```

For each field listed in `fields`:

- If its value is a scalar, that value is added to the total.
- If its value is a mapping, its values are summed and the resulting subtotal is added to the total.

The rule passes when the resulting total matches `value` within the optional `tolerance`.

### `required_with`

Requires one or more fields when a condition field is present.

```yaml
- id: prices_symbol_required_if_provider
  path: "sources.prices"
  type: required_with
  if_field: provider
  required_fields:
    - symbol
```

When `provider` is present in the target mapping, `symbol` must also be present and non-empty.

## Validation Error Messages

Each validation issue is returned as a formatted string.

The general format is:

```text
{id}: {description} ({details})
```

Example:

```text
ter_non_negative: The TER must be greater than or equal to zero (actual=-0.1, expected >= 0)
```

The message identifies the failed rule and provides details about the validation error.

## Extending RuleValidator

To introduce a new rule type:

1. Implement a dedicated handler method following this signature:

   ```python
   def _check_<type>(self, data, rule) -> list[str]:
       ...
   ```

2. Register the handler in the `_handlers` mapping, associating the rule type with its implementation.

3. Add the new rule type to the supported rule definitions and document its required parameters and behavior.

Rule loading and inheritance handling remain the responsibility of `RuleLoader`; new rule handlers should focus exclusively on evaluating their corresponding conditions.