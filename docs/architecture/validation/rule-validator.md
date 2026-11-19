# RuleValidator

Évalue des **règles métier** (fichiers `*.rules.yaml`) contre un document de données
(typiquement une fiche asset / contract déjà validée structurellement).

## Rôle dans l’architecture

```
SchemaValidator  → structure (JSON Schema)
RuleValidator    → métier  (*.rules.yaml + extends)
```

Le chargement des règles (résolution `extends`, concaténation, override par `id`)
est la responsabilité de `RuleLoader`.  
`RuleValidator` ne fait **que** l’évaluation.

## Utilisation

```python
from finance_cli.validation.rule_validator import RuleValidator

validator = RuleValidator()
issues = validator.validate(data=asset_data, rules=rules)

if issues:
    # list[str] — messages déjà formatés
    ...
```

- `data` : `dict` (fiche YAML fusionnée)
- `rules` : `list[dict]` (sortie de `RuleLoader.load(...)`)
- retour : liste vide si OK, sinon messages d’erreur lisibles

## Format d’une règle

```yaml
- id: ter_non_negative          # obligatoire, unique dans la chaîne
  description: "Le TER doit être >= 0"
  path: "general_info.ter"      # chemin pointé dans les données
  type: gte                     # type de règle
  value: 0                      # selon le type
```

## Types supportés

| Type | Paramètres | Description |
|------|------------|-------------|
| `sum_equals` | `path`, `fields`, `value`, `tolerance?` | Somme des valeurs (ou des sous-dicts) = `value` |
| `required` | `path` | Champ présent et non vide |
| `gt` / `gte` / `lt` / `lte` | `path`, `value` | Comparaison numérique |
| `min_items` | `path`, `value` | Liste avec au moins `value` éléments |
| `in` | `path`, `values` | Valeur dans l’ensemble autorisé |
| `date_before_today` | `path` | Date strictement avant aujourd’hui |
| `required_with` | `path`, `if_field`, `required_fields` | Si `if_field` présent → champs obligatoires |

### Exemple `sum_equals`

```yaml
- id: risk_allocation_sum
  path: "py_finance.risk"
  type: sum_equals
  fields: [low_risk, mid_risk, high_risk]
  value: 100
  tolerance: 0.01
```

Pour chaque `field`, si la valeur est un objet, on somme ses valeurs ;
sinon on ajoute la valeur scalaire.

### Exemple `required_with`

```yaml
- id: prices_symbol_required_if_provider
  path: "sources.prices"
  type: required_with
  if_field: provider
  required_fields: [symbol]
```

## Messages d’erreur

Format :

```text
{id}: {description} ({détail})
```

Exemple :

```text
ter_non_negative: Le TER doit être >= 0 (obtenu=-0.1, attendu >= 0)
```

## Extension

Pour ajouter un type :

1. Implémenter `_check_<type>(self, data, rule) -> list[str]`
2. L’enregistrer dans `_handlers`
