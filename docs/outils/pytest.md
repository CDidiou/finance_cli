# Utiliser pytest

`pytest` est l'outil de tests automatisés utilisé dans ce projet. Il découvre et
exécute les tests, puis indique ceux qui réussissent ou échouent. Les tests vérifient
le comportement du code ; ils ne remplacent ni Ruff (lint et formatage), ni mypy
(vérification statique des types).

## Lancer les tests

Avec Poetry, exécuter pytest dans l'environnement du projet :

```powershell
poetry run pytest
```

Pour cibler un fichier, une classe ou un test :

```powershell
poetry run pytest tests/test_cli.py
poetry run pytest tests/test_cli.py::test_help_is_available_inside_prompt
```

Options utiles :

```powershell
poetry run pytest -s                 # on voit les print de debug!
poetry run pytest -v                 # détail de chaque test
poetry run pytest -x                 # arrête à la première erreur
poetry run pytest -k "config and not invalid"  # sélection par nom
```

Le projet configure `tests/` comme répertoire de tests dans `pyproject.toml`.
Par défaut, pytest y recherche les fichiers nommés `test_*.py` ou `*_test.py`, les
fonctions commençant par `test_` et les méthodes `test_` de classes nommées
`Test...`.

## Écrire un test

Un test appelle le code à vérifier puis exprime le résultat attendu avec `assert` :

```python
def test_total_is_calculated() -> None:
    assert 10 + 5 == 15
```

Un test doit être indépendant et vérifier un comportement identifiable. Des noms
explicites facilitent la lecture des rapports, par exemple
`test_total_is_calculated`.

Pour vérifier qu'un appel échoue comme prévu, utiliser `pytest.raises` :

```python
def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("b ne peut pas être nul")
    return a / b


def test_dividing_by_zero_is_rejected() -> None:
    with pytest.raises(ValueError, match="nul"):
        divide(10, 0)
```

On peut préciser un fragment du message d'erreur avec `match="..."` lorsque ce
message fait partie du comportement attendu.

## Fixtures et données de test

Une fixture prépare une valeur ou une ressource nécessaire à un test. On la déclare
avec `@pytest.fixture`, puis pytest la fournit par son nom dans les paramètres du test.
Un fichier `tests/conftest.py` peut contenir des fixtures partagées par les tests
du répertoire. Il n'est nécessaire que lorsqu'on a réellement des préparations à
réutiliser.

pytest fournit aussi des fixtures utiles sans déclaration préalable :

- `tmp_path` fournit un répertoire temporaire unique pour un test ;
- `monkeypatch` permet de modifier temporairement une variable d'environnement,
  un attribut ou un élément du chemin de recherche, puis restaure son état ;
- `capsys` permet de lire la sortie standard et la sortie d'erreur capturées.

Utilise `tmp_path` pour créer des fichiers temporaires plutôt que de modifier des
fichiers réels du projet.

Les fixtures sont isolées par test par défaut. Cette isolation évite qu'un test
influence le résultat d'un autre. Utiliser une portée plus large (`module` ou
`session`) seulement si le partage est nécessaire et sans effets de bord.

## Tester plusieurs cas

`@pytest.mark.parametrize` exécute le même test pour plusieurs entrées :

```python
import pytest


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [(2, 3, 5), (10, 5, 15)],
)
def test_sum(a: int, b: int, expected: int) -> None:
    assert a + b == expected
```

Cela évite de dupliquer un test lorsque seule la donnée d'entrée change.

## Tester la CLI

La CLI utilise Click. Les tests peuvent l'invoquer sans lancer un processus externe,
avec `CliRunner` de Click :

```python
from click.testing import CliRunner

from finance_cli.cli import main


def test_prompt_help_and_exit() -> None:
    result = CliRunner().invoke(main, [], input="help\nexit\n")

    assert result.exit_code == 0
    assert "Commandes de l'invite" in result.output
```

Les tests de [`tests/test_cli.py`](../tests/test_cli.py) vérifient le prompt interactif,
son aide et sa sortie sur `exit` ou `quit`.

## Lire un échec

Dans le rapport pytest :

- `PASSED` indique un test réussi ;
- `FAILED` indique qu'une assertion ou une exception inattendue a échoué ;
- la trace indique le fichier, la ligne et les valeurs comparées ;
- `ERROR` signale généralement un problème pendant la préparation d'une fixture ou
  la collecte, avant même l'exécution du test.

Commencer par lire l'assertion et la première ligne de code du projet dans la trace.
Corriger le code ou le test selon le comportement attendu, puis relancer le test ciblé
et enfin la suite complète.

## Bonnes pratiques

- Tester les comportements observables, y compris les entrées invalides et les cas
  limites importants.
- Préférer des fichiers et répertoires temporaires (`tmp_path`) aux données réelles.
- Éviter les dépendances entre tests et les états globaux persistants.
- Garder les tests rapides et déterministes ; isoler les appels externes si nécessaire.
- Relancer le test ciblé pendant le développement, puis `poetry run pytest` avant de
  considérer le changement terminé.
