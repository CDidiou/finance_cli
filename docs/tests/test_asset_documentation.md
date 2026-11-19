# Tests du modèle Asset

## Organisation

```text
tests/
├── conftest.py                 # fixtures globales
└── test_models/
    └── test_asset.py           # tests du modèle Asset
```

---

## 1. Fixtures (`conftest.py`)

| Fixture | Rôle |
|---------|------|
| `setup_test_environment` | Isole le test dans un `tmp_path` (chdir) |
| `mock_config` | Crée un `config/config_app.yaml` minimal dans tmp |
| `cli_runner` | `CliRunner` Click prêt à l’emploi |
| `real_app_config` | Charge le **vrai** `config/config_app.yaml` du projet |

Les tests d’intégration catalogue s’appuient sur `real_app_config`.  
Les tests unitaires purs n’en ont pas besoin (ils injectent `_data` / `_schema` directement).

---

## 2. Découverte dynamique des assets réels

`get_real_asset_cases()` parcourt le catalogue configuré et retourne  
`list[tuple[isin, filepath]]`.

Filtres appliqués :
- fichier sous un dossier `implementations/`
- pas de `*.schemas.yaml`
- stem ≠ nom du dossier parent (exclut les définitions de catégorie)
- présence d’un champ `id` ou `isin`

Cette liste alimente les tests paramétrés d’intégration.

---

## 3. Tests d’intégration (catalogue réel)

| Test | Ce qu’il vérifie |
|------|------------------|
| `test_assets_using_real_config` | Au moins un asset est découvert |
| `test_asset_can_be_instantiated_and_loaded` | `from_isin` + `load()` → `data` et `schema` non vides |
| `test_asset_yaml_conformance_to_schema` | `validate()` ne retourne aucune erreur |

Ces tests garantissent que **tout le catalogue versionné** reste cohérent avec les schémas.

---

## 4. Tests unitaires simples (sans I/O catalogue)

| Test | Ce qu’il vérifie |
|------|------------------|
| `test_asset_not_loaded_raises` | Accès à `.data` avant `load()` → `RuntimeError` |
| `test_asset_isin_is_normalized` | ISIN normalisé en majuscules |
| `test_asset_repr_not_loaded` | `__repr__` contient l’ISIN et `"not loaded"` |
| `test_asset_helpers_defaults_when_empty_sources` | Helpers sources sûrs si bloc absent |
| `test_asset_helpers_with_full_sources` | Lecture correcte de `factsheet` / `aggregator` / `prices` |
| `test_asset_closed_status` | `status=closed` → `is_closed is True` |
| `test_asset_quote_always_one_disables_prices` | Fonds euros : `has_prices() is False` |
| `test_asset_sections_default` | `sections()` retourne les sections attendues |
| `test_asset_validate_returns_list` | `validate()` → liste vide si conforme |
| `test_asset_validate_detects_missing_field` | Champ manquant détecté |

Ces tests injectent `_data` et `_schema` directement sur l’instance  
→ **rapides, déterministes, sans dépendance au disque**.

---

## 5. Lancer les tests

```bash
# Tous les tests Asset
poetry run pytest tests/test_models/test_asset.py -v

# Uniquement les unitaires (pas de catalogue)
poetry run pytest tests/test_models/test_asset.py -v -k "not real_config and not instantiated and not conformance"

# Avec affichage des prints de debug
poetry run pytest tests/test_models/test_asset.py -v -s
```

---

## 6. Bonnes pratiques respectées

1. **Séparation intégration / unitaire** — le catalogue réel n’est touché que par les tests paramétrés.
2. **Pas de `load()` dans les unitaires de helpers** — on mocke l’état interne.
3. **Messages d’assertion explicites** — ISIN + nom de fichier en cas d’échec de schéma.
4. **Paramétrisation dynamique** — tout nouvel asset ajouté au catalogue est automatiquement testé.
