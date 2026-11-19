# Liste des commandes disponibles

> conda deactivate
> poetry install
> poetry run finance-cli


## Conventions

La CLI suit une convention de commande: 
    ressource → identifiant éventuel → action → options de l'action
    ex: patrimonia <RESOURCE> [--id <ID_RESOURCE>] <ACTION> [OPTIONS]

L'objet est toujours identifié avant l'action.
L'identifiant est immédiatement visible.
Les commandes sont prévisibles.
L'ajout de nouvelles actions ne modifie pas la convention.
La documentation est plus facile à organiser.

Ex:
    # Collections : pas d'identifiant
    patrimonia users list
    patrimonia accounts list
    patrimonia assets list

    # Objets : identifiant obligatoire
    patrimonia user --id <ID_USER> show
    patrimonia account --id <ID_ACCOUNT> show
    patrimonia asset --id <ID_ASSET> show
    patrimonia wallet --id <ID_WALLET> --user <ID_USER> show
    patrimonia asset --id <ID_ASSET> fetch
    patrimonia asset --id <ID_ASSET> apply
    patrimonia asset --id <ID_ASSET> refresh
    patrimonia asset --id <ID_ASSET> history

Règles:
- nom pluriel pour les collections ;
- nom singulier pour un objet ;
- --id pour identifier un objet ;
- actions communes (show, list, check) lorsque leur sens est identique.

Actions - Il faut distinguer systématiquement trois opérations :
1. **Check** : vérifier la conformité des données.
2. **Calculate** : produire un résultat calculé.
3. **Show** : consulter les données ou les résultats.

## Commandes générales

### check

| Commande	| Responsabilité |
| --- | --- |
| config check	| Configuration applicative |
| system check	| Cohérence globale de l'environnement Patrimonia |

Pour system check, les contrôles sont :
1. Existence et accessibilité des répertoires.
2. Présence des référentiels attendus.
3. Validité des schémas.
4. Cohérence des relations entre référentiels.
5. Cohérence des fichiers utilisateurs.
6. Cohérence des fichiers calculés.
7. Cohérence des métadonnées et des références aux sources.

### list 

patrimonia users list
    Liste les utilisateurs configurés
patrimonia accounts list
    Liste les accounts (contrats+broker) définis
patrimonia assets list
    Liste les actifs définis

Avec filtrage:
    patrimonia users list --details
    patrimonia accounts list --type broker
    patrimonia assets list --category equity


## Domaine assets

patrimonia asset --id <ID_ASSET> show
    Affiche general_info / market_data
patrimonia asset --id <ID_ASSET> show --section sources
    Afficher les sources configurées    
patrimonia asset --id <ID_ASSET> check
    Commande de diagnostic. Elle vérifie la présence de la fiche, le json schema, les règles métier, la construction du modèle Pydantic.
patrimonia asset --id <ID_ASSET> fetch market-data
patrimonia asset --id <ID_ASSET> apply market-data
patrimonia asset --id <ID_ASSET> refresh market-data

refresh enchaîne fetch et apply. L'historique sera ajouté ultérieurement.
asset --id <ID_ASSET> history    Contrôle les historiques de cours
ou asset --id <ID_ASSET> history Consulter l'historique des cours (choix en cours)

## Domaine account

patrimonia account --id <ID_ACCOUNT> show
    Affiche general_info


## Domaine wallet

wallet --id : --user facultatif uniquement si la recherche permet de résoudre un identifiant unique ; sinon erreur d'ambiguïté

| Situation	| Comportement |
| --- | --- |
| Wallet trouvé avec --id seul	| Accepté si unique |
| Wallet trouvé avec --id et --user	| Accepté si correspondance |
| Plusieurs wallets avec le même ID	| Erreur d'ambiguïté |
| Aucun wallet trouvé	| Erreur explicite |
| --user incompatible avec le wallet	| Erreur de cohérence |

patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] show
    Affiche la fiche du wallet (il peut y avoir le même ID_WALLEt dispersé sur plusieurs users!)
patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] transactions show
    Consulter les transactions
patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] transaction show --date YYYY-MM-DD
    Consulter les transactions
patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] transactions check
    Vérifie les transactions 

patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] balances list
    Donne la liste des dates où une balance est disponible
patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] balances check    
patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] balance show --date YYYY-MM-DD
patrimonia wallet --id <ID_WALLET> [--user <ID_USER>] balance calculate  --date YYYY-MM-DD
    Calcule la balance à la date donnée


## Domaine user
user --id <ID_USER> show 
    Afficher un utilisateur

user --id <ID_USER> wallets list
    Lister les wallets d'un utilisateur

## Arborescence des commandes

patrimonia
│
├── config
│   └── check
│
├── users
│   └── list
│
├── user --id ID
│   ├── show
│   ├── wallets
│   │   └── list
│
├── accounts
│   └── list
│
├── account --id ID
│   └── show
│
├── assets
│   └── list
│
├── asset --id ID
│   ├── show
│   ├── check
│   ├── fetch
│   │   └── market-data
│   ├── apply
│   │   └── market-data
│   ├── refresh
│   │   └── market-data
│   └── history
│
└── wallet --id ID [--user ID]
    ├── show
    ├── transactions
    │   ├── list
    │   ├── show
    │   └── check
    ├── transaction
    │   └── show --date YYYY-MM-DD
    ├── balances
    │   ├── list
    │   └── check
    └── balance
        ├── calculate
        └── show

## Codes de retour

Code de sortie:
0 : succès.
1 : erreur d'exécution.
2 : erreur d'utilisation ou d'arguments.
3 : échec de validation des données.

Message de diagnostic:
- ERROR : traitement impossible.
- WARNING : anomalie non bloquante.
- INFO : information de contrôle.

