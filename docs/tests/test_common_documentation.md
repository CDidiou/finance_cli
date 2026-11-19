# Tests du package `finance_cli.common`

## Organisation

```text
tests/
└── test_common/
    ├── test_yaml_io.py
    ├── test_merge.py
    ├── test_validate.py
    ├── test_inheritance.py
    ├── test_assets_index.py
    ├── test_excel_names.py
    └── test_paths.py
```

Tous ces tests sont **unitaires** : ils utilisent `tmp_path` et ne dépendent pas du catalogue réel ni de la config de production.

---

## 1. `test_yaml_io.py`

| Test | Cas couvert |
|------|-------------|
| `test_load_yaml_mapping_ok` | Chargement nominal |
| `test_load_yaml_mapping_empty_file` | Fichier vide → `{}` |
| `test_load_yaml_mapping_missing_file` | Fichier absent → `ValueError` |
| `test_load_yaml_mapping_invalid_yaml` | YAML mal formé → `ValueError` |
| `test_load_yaml_mapping_root_not_mapping` | Racine liste → `ValueError` |
| `test_dump_yaml_mapping_creates_parents` | Écriture + création des dossiers parents |

---

## 2. `test_merge.py`

| Test | Cas couvert |
|------|-------------|
| `test_deep_merge_overwrite_simple` | Fusion plate, overwrite |
| `test_deep_merge_nested` | Fusion récursive |
| `test_deep_merge_raise_on_conflict` | Conflit scalaire → `ValueError` |
| `test_deep_merge_raise_identical_ok` | Valeurs identiques acceptées |
| `test_deep_merge_raise_nested_conflict` | Conflit imbriqué + context |
| `test_deep_merge_adds_nested_dict` | Création de sous-dicts absents |

---

## 3. `test_validate.py`

| Test | Cas couvert |
|------|-------------|
| Types scalaires | `string`, `integer`, `number`, `boolean` |
| Bool rejeté comme integer | `True` n’est pas un `integer` |
| Dict — champ manquant | Chemin signalé |
| Dict imbriqué | `general_info.name` |
| Liste | Index de l’élément fautif |
| Nullable | `None` accepté si `nullable: true` |
| Template invalide | `ValueError` |

---

## 4. `test_inheritance.py`

| Test | Cas couvert |
|------|-------------|
| `test_resolve_extends_chain_simple` | Chaîne parent → enfant |
| `test_resolve_extends_chain_cycle` | Cycle détecté |
| `test_resolve_extends_outside_catalogue` | Sortie du data_root interdite |
| `test_load_merged_data` | Fusion des données + suppression de `extends` |
| `test_load_merged_schema` | Union des `required_structure` |
| `test_load_merged_schema_conflict` | Types incompatibles → erreur |
| `test_load_cumulative_data_and_schema` | Orchestration complète |

---

## 5. `test_assets_index.py`

| Test | Cas couvert |
|------|-------------|
| `test_find_by_stem` | Match sur le nom de fichier |
| `test_find_by_id_field` | Match sur le champ `id` |
| `test_find_not_found` | Aucune fiche → `ValueError` |
| `test_find_duplicate` | Plusieurs fiches → `ValueError` |
| `test_find_ignores_schema_and_category_files` | Ignore `*.schemas.yaml` et définitions de catégorie |

---

## 6. `test_excel_names.py`

| Test | Cas couvert |
|------|-------------|
| Pattern `<year>` | Extraction de l’année |
| Pattern `<date>` | Extraction d’une date complète |
| Mauvais wallet_id | `None` |
| Nom non conforme | `None` |
| Placeholder inconnu | `ValueError` |

---

## 7. `test_paths.py`

| Test | Cas couvert |
|------|-------------|
| Config + dossier OK | Retourne le Path |
| Config absente | `ValueError` |
| Dossier configuré absent | `ValueError` |

Utilise `monkeypatch` pour injecter `DEFAULT_CONFIG_PATH` et le cwd.

---

## 8. Lancer les tests

```bash
# Tout le package common
poetry run pytest tests/test_common/ -v

# Un module précis
poetry run pytest tests/test_common/test_merge.py -v
poetry run pytest tests/test_common/test_inheritance.py -v
```

---

## 9. Principes

1. **Aucun accès au catalogue réel** — tout est construit dans `tmp_path`.
2. **Cas d’erreur testés** — chaque `ValueError` documenté a son test.
3. **Une responsabilité par fichier de test** — miroir des modules `common/`.
4. **Rapides et déterministes** — adaptés au TDD et à la CI.
