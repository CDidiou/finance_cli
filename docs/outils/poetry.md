# Poetry

Poetry est un outil de gestion de projets Python. Il aide à déclarer les dépendances,
créer un environnement virtuel, installer le projet et ses dépendances, et construire
des paquets distribuables. Conda couvre aussi la gestion d'environnements et peut gérer
des paquets non-Python ; les deux outils ont donc des rôles qui se recoupent, sans être
interchangeables dans tous les cas.

## Les fichiers du projet

### `pyproject.toml`

Ce fichier utilise le format TOML, standard en Python pour les métadonnées et la
configuration des projets. Poetry y déclare notamment :

- les métadonnées du projet (nom, version, description) ;
- la version de Python et les dépendances ;
- les groupes de dépendances, par exemple les outils réservés au développement ;
- la commande installée par le projet ;
- la configuration des outils comme Ruff, pytest et mypy.

Dans ce projet, les dépendances principales et celles de développement sont définies
dans `pyproject.toml`. Par exemple, `ruff` est dans le groupe `dev` : il est utile pour
développer et vérifier le code, mais n'est pas une dépendance nécessaire à l'utilisation
de la CLI.

### `poetry.lock`

Le fichier de verrouillage enregistre les versions exactes résolues pour les
dépendances, y compris leurs dépendances indirectes. Il rend les installations plus
reproductibles d'une machine à l'autre. Il faut le conserver et le partager avec le
projet ; on ne le modifie généralement pas à la main.

`pyproject.toml` exprime les versions autorisées, tandis que `poetry.lock` indique les
versions précises choisies. Par exemple, `ruff = ">=0.5.3"` autorise 0.5.3 et les
versions ultérieures compatibles avec les autres dépendances ; le verrouillage fixe la
version effectivement installée jusqu'à une mise à jour.

## Environnement virtuel

Par défaut, Poetry crée ou réutilise un environnement virtuel pour le projet. Les
commandes `poetry run ...` exécutent un programme dans cet environnement, sans qu'il
soit nécessaire de l'activer manuellement :


La commande poetry install vérifie l’environnement et installe ce qui manque, en s’appuyant sur les versions verrouillées dans poetry.lock. Elle ne met pas spontanément toutes les dépendances à jour.

poetry update a un autre rôle : chercher des versions plus récentes autorisées par les contraintes du projet, puis actualiser poetry.lock. C’est utile quand tu veux mettre à jour les dépendances, pas à chaque retour dans le projet.

```powershell
poetry install
poetry run pytest
poetry run ruff check .
poetry run finance-cli --help
```

Pour savoir quel environnement est utilisé :

```powershell
poetry env info
poetry env list
```

Poetry et Conda peuvent créer des environnements distincts. Une mise à jour de Ruff
dans l'un ne met donc pas automatiquement à jour Ruff dans l'autre. Il est préférable
de savoir quel interpréteur VS Code et quelle commande de test ou de lint utilisent.

## Commandes courantes

Installer le projet et les dépendances déclarées :

```powershell
poetry install
```

Ajouter ou supprimer une dépendance :

```powershell
poetry add pyyaml
poetry add --group dev ruff
poetry remove pyyaml
```

Mettre à jour les dépendances autorisées par `pyproject.toml` et réécrire le fichier
`poetry.lock` :

```powershell
poetry update
```

Mettre à jour une seule dépendance :

```powershell
poetry update ruff
```

Une contrainte de version limite ce que Poetry peut sélectionner. Par exemple,
`^0.5.3` signifie `>=0.5.3,<0.6.0`, alors que `>=0.5.3` ne fixe pas de borne supérieure.
Après avoir modifié une contrainte, exécuter `poetry update <paquet>` permet de
recalculer la version verrouillée correspondante.

Pour ajouter automatiquement dans pyproject.toml avec la bonne version:
> poetry add python-dotenv


## Commande de l'application

La section `[tool.poetry.scripts]` de `pyproject.toml` déclare une commande et la
fonction Python appelée :

```toml
[tool.poetry.scripts]
finance-cli = "finance_cli.cli:main"
```

Cela signifie que `finance-cli` appelle la fonction `main` du module
`finance_cli.cli`. Après `poetry install`, on peut la lancer ainsi :

```powershell
poetry run finance-cli --help
```

Quand le bon environnement virtuel est activé, la commande peut aussi être lancée
directement. `poetry run` est toutefois plus explicite et évite de dépendre de
l'environnement actuellement activé dans le terminal.

`poetry install` installe le projet courant et ses dépendances dans l'environnement
Poetry. `pip install -e .` est une autre façon d'installer un projet local en mode
éditable, mais ce n'est pas la même commande : elle ne gère pas à elle seule
l'environnement virtuel ni le verrouillage des dépendances de Poetry.

## Outils de développement

- **pytest** exécute les tests automatisés.
- **Ruff** détecte des problèmes de code (lint) et peut aussi formater le code.
- **mypy** vérifie statiquement la cohérence de nombreuses annotations de type. Il ne
  modifie pas le code et ne remplace pas les tests.

Les règles et options de ces outils sont configurées dans `pyproject.toml`. Par exemple,
Ruff y lit la longueur de ligne, la version Python ciblée et les règles de lint activées.