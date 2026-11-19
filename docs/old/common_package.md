# Package `finance_cli.common`

Découpage du module utilitaire historique `generic_functions.py` en briques élémentaires.

---

## 1. Structure

```text
finance_cli/common/
├── __init__.py              # réexporte la façade
├── generic_functions.py     # façade rétro-compatible
├── yaml_io.py               # lecture / écriture YAML
├── merge.py                 # fusion profonde de dicts
├── paths.py                 # résolution des chemins de données
├── inheritance.py           # chaîne extends + chargement cumulatif
├── validate.py              # validation structure vs schéma
├── assets_index.py          # recherche d'une fiche asset par ISIN
└── excel_names.py           # parsing des noms de fichiers Excel
```

---

## 2. Responsabilité de chaque module

| Module | Rôle | Fonctions principales |
|--------|------|------------------------|
| **yaml_io** | I/O YAML pur | `load_yaml_mapping`, `dump_yaml_mapping` |
| **merge** | Fusion de mappings | `deep_merge(target, source, on_conflict=...)` |
| **paths** | Chemins configurés | `get_configured_path`, `configured_data_folder` |
| **inheritance** | Héritage `extends` | `resolve_extends_chain`, `load_merged_data`, `load_merged_schema`, `load_cumulative_data_and_schema` |
| **validate** | Contrôle de structure | `validate_structure` |
| **assets_index** | Index des assets | `find_asset_implementation` |
| **excel_names** | Noms de fichiers Excel | `match_excel_filename` |
| **generic_functions** | Façade | Réexporte les fonctions historiques pour ne pas casser les imports existants |

---

## 3. Détail des modules clés

### 3.1 `yaml_io.py`

- `load_yaml_mapping(path) → dict`  
  Charge un YAML, exige un mapping à la racine, gère les erreurs clairement.
- `dump_yaml_mapping(path, data)`  
  Écrit un mapping (crée les dossiers parents si besoin).

### 3.2 `merge.py`

```python
deep_merge(target, source, *, on_conflict="overwrite" | "raise", context=None)
```

- `"overwrite"` : comportement des données héritées (l’enfant gagne).
- `"raise"` : comportement des schémas (conflit de type → erreur).

Une seule primitive remplace les anciennes `_deep_merge_mapping` et `_deep_merge_schema`.

### 3.3 `paths.py`

- `get_configured_path(category)` → Path (lecture pure de la config).
- `configured_data_folder(category)` → Path + vérification que le dossier existe.

### 3.4 `inheritance.py`

Découpage de l’ancienne `load_cumulative_data_and_schema` :

```text
resolve_extends_chain(file, root)  →  list[Path]     # racine → entité
        ↓
load_merged_data(chain)            →  dict           # données fusionnées
load_merged_schema(chain)          →  dict           # schéma fusionné
        ↓
load_cumulative_data_and_schema()  →  (data, schema) # orchestre le tout
```

### 3.5 `validate.py`

`validate_structure(value, template) → list[str]`  
Inchangé fonctionnellement : retourne la liste des chemins invalides.

### 3.6 `assets_index.py`

`find_asset_implementation(isin, assets_root) → Path`  
Recherche sous `**/implementations/*.yaml` (stem puis champs `id`/`isin`).

### 3.7 `excel_names.py`

`match_excel_filename(filename, pattern, wallet_id, date_format)`  
Spécifique aux fichiers de transactions / balances. Isolé car hors du cœur « catalogue YAML ».

---

## 4. Compatibilité ascendante

Les imports existants continuent de fonctionner :

```python
from finance_cli.common import generic_functions
from finance_cli.common.generic_functions import (
    load_yaml_mapping,
    configured_data_folder,
    load_cumulative_data_and_schema,
    validate_structure,
    find_asset_implementation,
    match_excel_filename,
)
```

En interne, `generic_functions.py` ne fait que réexporterer.

**Nouveau style recommandé :**

```python
from finance_cli.common.yaml_io import load_yaml_mapping
from finance_cli.common.inheritance import load_cumulative_data_and_schema
from finance_cli.common.paths import configured_data_folder
```

---

## 5. Lien avec la classe `Asset` et les commandes CLI

```text
CLI  asset show <ISIN>
  →  Asset.from_isin(isin).load()
       →  configured_data_folder("assets")
       →  find_asset_implementation(isin, root)
       →  load_cumulative_data_and_schema(file, root)

CLI  asset validate <ISIN>
  →  Asset.from_isin(isin).load().validate()
       →  validate_structure(data, schema)
```

---

## 6. Règles de conception

1. **Une responsabilité par module** — plus facile à tester et à faire évoluer.
2. **Pas d’effet de bord caché** — les fonctions de chargement ne modifient pas le disque.
3. **Erreurs explicites** — `ValueError` avec message contextualisé.
4. **Façade de transition** — on ne casse pas le code existant le temps de migrer les imports.
