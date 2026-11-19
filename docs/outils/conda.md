# Conda et ce projet

Conda peut créer des environnements isolés et installer des paquets Python, mais aussi
des bibliothèques et outils non-Python. Poetry gère également l'environnement virtuel
et les dépendances du projet Python.

## Est-ce que Conda est nécessaire ici ?

Pour travailler sur ce projet, **Conda n'est pas nécessaire pour gérer l'environnement
du projet** : c'est Poetry qui s'en charge. Le projet déclare Python `^3.12` et ses
dépendances dans `pyproject.toml`, et les versions résolues sont enregistrées dans
`poetry.lock`.

Depuis la racine du projet, les commandes habituelles sont :

```powershell
poetry install
poetry run pytest
poetry run ruff check .
poetry run finance-cli --help
```

Cependant, Poetry ne fournit pas lui-même l'interpréteur Python. Il faut qu'une version
compatible de Python soit déjà installée sur la machine. Cette version peut provenir
de python.org, du Microsoft Store, de Conda ou d'un autre gestionnaire. Ainsi, Conda
peut rester installé pour fournir Python, même si Poetry crée ensuite l'environnement
virtuel isolé du projet.

Pour vérifier l'environnement employé par Poetry :

```powershell
poetry env info
poetry env list
```

VS Code doit utiliser le même environnement Poetry que les commandes lancées avec
`poetry run`. Sinon, l'éditeur et le terminal peuvent afficher des versions différentes
des dépendances ou du linter.

## Quand utiliser Conda ?

Conda reste pratique si un projet a besoin de bibliothèques natives ou scientifiques
qui sont plus simples à installer via Conda, si plusieurs projets utilisent déjà des
environnements Conda, ou si l'on veut gérer des environnements en dehors de Poetry.
Pour éviter toute confusion, il vaut mieux choisir un gestionnaire d'environnement
principal par projet plutôt que d'installer les mêmes dépendances tantôt dans Conda,
tantôt dans Poetry.

Pour ce projet, les dépendances déclarées dans `pyproject.toml` sont des paquets Python
ordinaires ; Poetry est donc le choix à privilégier pour les installer et les verrouiller.

## Commandes Conda de référence

Ces commandes servent pour d'autres projets ou si l'on choisit explicitement de gérer
un environnement avec Conda :

```powershell
conda create --name mon_env python=3.12
conda activate mon_env
conda deactivate
conda env list
conda remove --name mon_env --all
```

Une fois l'environnement activé, Conda peut gérer les paquets :

```powershell
conda install nom_du_paquet
conda install pandas=2.0
conda list
conda update nom_du_paquet
conda remove nom_du_paquet
```

Pour partager la définition d'un environnement Conda :

```powershell
conda env export > environment.yml
conda env create --file environment.yml
```

Ce fichier `environment.yml` est une méthode de partage propre à Conda. Pour ce projet,
le fichier de référence pour les dépendances Poetry est plutôt `pyproject.toml`, complété
par `poetry.lock`.
