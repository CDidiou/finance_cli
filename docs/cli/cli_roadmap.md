# **Avis sur Patrimonia**

**Patrimonia repose sur de bons choix d'architecture, et surtout sur une philosophie adaptée à son objectif.** Tu construis un outil de gestion patrimoniale familial, pas un progiciel bancaire. C'est une distinction importante : il faut rechercher la fiabilité, la lisibilité et la facilité de maintenance, sans transformer le projet en usine à gaz.

Ce qui est pertinente, c'est la séparation entre :

- le catalogue financier administré ;
- les données saisies par les utilisateurs ;
- les résultats calculés par l'application.

Il permet de faire évoluer les fonctionnalités sans mélanger les responsabilités ni mettre en danger les données sources.


## **1. Les points forts du projet**

### **1.1 Une bonne séparation entre sources et résultats**

Référentiel
`data/`
Catalogue des actifs et contrats financiers, maintenu et enrichi de façon contrôlée.

Sources utilisateur
`external-data/.../input/`
Transactions, balances et informations personnelles. Les sources sont préservées.

Résultats dérivés
`external-data/.../calculated/`
Données enrichies, balances calculées, évolutions et dashboards régénérables.

Cette séparation est excellente pour trois raisons :
1. On sait toujours quelle est la source de vérité.
2. On peut supprimer et reconstruire les résultats calculés.
3. On peut faire évoluer les calculs sans modifier les données originales.


### **1.2 Une architecture Python adaptée**

La séparation `CLI / bootstrap / services / repositories / adapters / models` est saine.

Elle permet notamment de :

- remplacer un fournisseur financier sans modifier les services ;
- faire évoluer le stockage sans réécrire les commandes ;
- tester les traitements indépendamment de la CLI ;
- centraliser la construction des dépendances.


### **1.3 Une bonne utilisation de YAML et Excel**

Le choix des formats est cohérent avec les usages :

| Format        | Usage                                                                  | Mon avis                              |
| ------------- | ---------------------------------------------------------------------- | ------------------------------------- |
| YAML          | Référentiels, configurations, données structurées et résultats simples | Très adapté                           |
| Excel         | Saisie des transactions et balances                                    | Très adapté à un usage familial       |
| HTML / Plotly | Dashboards                                                             | Excellent pour une restitution locale |
| PDF           | Factsheets et documents fournisseurs                                   | Naturel                               |

Il n'y a pas de raison de migrer vers une base SQL ou un format plus complexe tant que le volume et les usages ne le justifient pas.

### **1.4 Un cycle de calcul volontairement simple**

Le recalcul complet des transactions enrichies est un très bon choix.

Pour un patrimoine familial, le volume de transactions reste généralement raisonnable. La simplicité d'un recalcul complet est plus intéressante que les optimisations prématurées d'un traitement incrémental.


## **2. Propositions d'amélioration prioritaires**

### **2.1 Formaliser les contrats entre les étapes de calcul**

Priorité élevée

Chaque étape devrait avoir un contrat clair :

| Traitement                  | Entrées                                              | Sortie                      |
| --------------------------- | ---------------------------------------------------- | --------------------------- |
| Validation transactions     | Excel input                                          | Transactions validées       |
| Enrichissement transactions | Transactions validées + référentiel nécessaire       | YAML transactions enrichies |
| Calcul balance              | Dernière balance officielle + transactions enrichies | Excel balance calculée      |
| Calcul évolution            | Historique des balances de référence                 | YAML évolution              |
| Génération dashboard        | Résultats calculés                                   | HTML + métadonnées          |

Pour chaque traitement, il faut documenter :

- les entrées obligatoires ;
- les validations effectuées ;
- les règles de calcul ;
- les sorties produites ;
- les erreurs possibles.

L'objectif n'est pas de créer une documentation volumineuse, mais d'éviter les ambiguïtés entre composants.

### **2.2 Bien distinguer validation et calcul**

Priorité élevée

Il faut distinguer systématiquement trois opérations :

1. **Check** : vérifier la conformité des données.
2. **Calculate** : produire un résultat calculé.
3. **Show** : consulter les données ou les résultats.

Par exemple :

```
patrimonia wallet --id W001 transactions check
patrimonia wallet --id W001 transactions calculate
patrimonia wallet --id W001 transactions show
```

`calculate` pourrait déclencher le recalcul complet des transactions enrichies, tandis que `check` ne devrait pas modifier de données.

Il faut surtout éviter qu'une commande de consultation déclenche silencieusement des écritures ou des calculs coûteux. Si une commande doit régénérer un résultat, son comportement devrait être explicite et documenté.

### **2.3 Sécuriser les écritures des résultats calculés**

Priorité élevée

Même si les résultats sont régénérables, il faut éviter qu'un calcul interrompu laisse un fichier incomplet.

Il faut utiliser le mécanisme simple de l'écriture atomique:

1. Calculer le résultat en mémoire.
2. Valider le résultat.
3. Écrire dans un fichier temporaire situé dans le même répertoire.
4. Remplacer le fichier cible uniquement lorsque l'écriture est terminée.

C'est le principe d'une écriture atomique.
Cela évite notamment de perdre un résultat précédent valide en cas d'erreur pendant le nouveau calcul.
Egalement, on ne remplace pas un résultat existant si la validation des entrées échoue.

### **2.4 Formaliser la gestion des balances**

Priorité élevée

C'est probablement le domaine métier qui mérite le plus de précision.

Il faut conserver strictement la distinction entre :

- **Balance officielle** : référence de calcul, située dans `input`.
- **Balance calculée** : résultat produit par Patrimonia, situé dans `calculated`.

Il faut documenter trois règles :
- La balance calculée ne devient jamais officielle automatiquement.
- L'utilisateur décide explicitement de son officialisation.
- Une balance calculée doit toujours pouvoir identifier la balance officielle et les transactions qui ont servi à la produire.

Un point métier important reste à définir : que se passe-t-il lorsqu'une transaction est antidatée, corrigée ou supprimée après le calcul d'une balance ?
Détection via les hash des metadonnées. Le recalcul écrase l'ancienne balance calculated.

Quand des transactions permettent un calcul correct de balance officielle en balance officielle, ces transactions avec leur hash doivent avoir un status particulier de type conforme!

### **2.5 Renforcer la traçabilité sans la compliquer**

Il ne faut pas construire un système de reproductibilité trop sophistiqué.
Il faut conserver le modèle commun de métadonnées et normaliser quelques éléments :

- `generated_at` : date et heure de génération ;
- `calculation_date` : date métier du calcul, lorsqu'elle existe ;
- `scope` : `wallet` ou `user` ;
- `generator` : application et version ;
- `sources` : fichiers utilisés, rôle et hash des données ;
- `data_hash` : hash du résultat produit, éventuellement.

header:
  generated_at: "2026-11-16T10:30:00"
  calculation_date: "2026-11-15"

  scope: wallet
  wallet_id: W001

  generator:
    application: patrimonia
    version: "1.0.0"

  sources:
    - path: input/W001/balances/2026-10-31_W001_balance.xlsx
      data_hash: "..."
      role: reference_balance

    - path: input/W001/transactions/2026_W001_tx.xlsx
      data_hash: "..."
      role: transactions


Il faut faire la distinction entre deux choses :
- **Hash des sources** : permet de savoir si les données utilisées ont changé.
- **Hash du résultat** : permet de savoir si le contenu calculé a changé.

Ce deuxième hash est facultatif, mais peut être utile pour diagnostiquer des écarts.

Il faut définir une seule fonction technique de calcul du hash, utilisée partout. Elle doit normaliser les données avant calcul : ordre des champs, dates, nombres, valeurs nulles et ordre des enregistrements lorsque cet ordre n'a pas de sens métier.


### **2.6 Définir une politique d'identification des erreurs**

Priorité moyenne

Les erreurs financières doivent être compréhensibles par un utilisateur non développeur.

Je proposerais trois catégories :

| Catégorie           | Exemple                                          | Comportement                     |
| ------------------- | ------------------------------------------------ | -------------------------------- |
| Erreur de données   | Date ou quantité invalide                        | Bloquer le calcul et expliquer   |
| Erreur de référence | Actif inconnu dans une transaction               | Signaler l'identifiant concerné  |
| Erreur technique    | Fichier inaccessible ou fournisseur indisponible | Expliquer l'opération impossible |

Les messages devraient indiquer autant que possible :

- le fichier concerné ;
- la feuille Excel ;
- la ligne ;
- le champ ;
- la valeur problématique ;
- la correction attendue.

C'est un investissement qui améliore fortement l'expérience utilisateur.

## **3. Quelques sujets métier à surveiller**

### **3.1 Les montants financiers**

Il faut utiliser `Decimal` pour les calculs monétaires, plutôt que les nombres flottants Python (`float`).

Cela évite les imprécisions binaires dans les additions, soustractions et calculs de prix de revient.

Il faut également définir clairement :

- la devise de chaque wallet ;
- la devise des actifs ;
- la conversion éventuelle ;
- les règles d'arrondi ;
- la précision des quantités de titres.

### **3.2 Les dates et les opérations**

Il faudra être rigoureux sur la distinction entre :

- date de transaction ;
- date de valeur ;
- date d'exécution ;
- date de calcul ;
- date de balance.

Il n'est pas nécessaire d'utiliser toutes ces dates partout. Mais il faut définir celles qui sont réellement utiles pour chaque type d'opération.

### **3.3 Le prix de revient unitaire**

Le PRU mérite une attention particulière, car c'est une donnée calculée qui peut avoir des conséquences sur les analyses.

Il faut formaliser une fois pour toutes :

- les règles de calcul pour les achats ;
- les règles de traitement des ventes ;
- le traitement des frais ;
- les apports et retraits de liquidités ;
- les dividendes et intérêts ;
- les dons ou transferts de titres ;
- les cas où le PRU est inconnu.

Il ne faut pas confondre une valeur inconnue avec zéro. Un PRU non déterminable doit rester explicitement non renseigné.

### **3.4 Les transactions et les actifs inconnus**

Si une transaction contient un code actif qui ne correspond à aucun élément du catalogue, Patrimonia devrait signaler l'anomalie et demander une correction ou une intégration au référentiel.
C'est préférable à une association automatique susceptible de fausser le patrimoine.

## **4. A ne pas faire**

Il faut résister à plusieurs tentations techniques.

| Fonctionnalité                                  | Mon avis                                                 |
| ----------------------------------------------- | -------------------------------------------------------- |
| Base de données SQL                             | Pas nécessaire actuellement                              |
| Traitement incrémental des transactions         | À éviter : le recalcul complet est plus simple           |
| Versionnement complet des règles et algorithmes | Disproportionné à ce stade                               |
| Architecture distribuée / microservices         | Aucun intérêt ici                                        |
| Interface web complète                          | Pas prioritaire, les dashboards HTML suffisent           |
| Synchronisation bancaire automatique            | À envisager seulement si le besoin devient réel          |
| Gestion multi-devises complexe                  | À développer uniquement si le patrimoine le nécessite    |
| Moteur de règles générique                      | Éviter de créer un framework pour quelques règles métier |

Le meilleur indicateur de réussite ne sera pas le nombre de fonctionnalités, mais la capacité à obtenir une valorisation fiable et compréhensible avec un minimum d'interventions.

## **5. Les améliorations techniques à ajouter**

### **5.1 Sauvegarde et restauration**

Les données patrimoniales sont précieuses. Une erreur humaine, une mauvaise manipulation Excel ou une suppression accidentelle peut avoir des conséquences importantes.

Il est recommandé :
- une sauvegarde régulière du répertoire `external-data/` ;
- une sauvegarde du catalogue `data/` ;
- une conservation de plusieurs versions ;
- une procédure de restauration documentée.

Les résultats `calculated/` peuvent être reconstruits, mais les sources `input/` doivent être protégées.

### **5.2 Tests de bout en bout**

Pour les tests, il faut prévoir quelques scénarios complets :
- création d'un wallet de test ;
- chargement de transactions Excel ;
- validation des données ;
- génération des transactions enrichies ;
- calcul d'une balance ;
- génération de l'évolution patrimoniale ;
- génération du dashboard.

L'objectif est de vérifier que toute la chaîne fonctionne correctement, et pas uniquement que chaque composant fonctionne isolément.

Il faut créer aussi quelques jeux de données de référence avec des résultats financiers attendus, notamment pour le calcul du PRU et des balances.

### **5.3 Commande de diagnostic global**

Une commande du type :

```
patrimonia system check
```

pourrait vérifier :

- la configuration ;
- la structure des répertoires ;
- les schémas disponibles ;
- la cohérence des référentiels ;
- les fichiers utilisateurs ;
- les résultats calculés et leurs métadonnées.

Ce serait très utile pour diagnostiquer rapidement un problème sans devoir lancer plusieurs commandes.

### **5.4 Séparer clairement les erreurs et les avertissements**

Une donnée invalide doit bloquer le calcul. En revanche, une donnée simplement incomplète ne devrait pas forcément empêcher toute analyse.

Par exemple :

- actif absent du catalogue : erreur bloquante ;
- cours de marché indisponible : avertissement, selon le calcul concerné ;
- métadonnée facultative absente : avertissement ou information ;
- source modifiée depuis le dernier calcul : information de recalcul nécessaire.

Cette distinction rendrait l'application plus agréable à utiliser.

### **5.5 Fiabilité financière**

Il faudra définir une règle générale pour les actifs dont le cours est indisponible.

Trois comportements sont possibles :
1. Bloquer toute la valorisation.
2. Valoriser uniquement les actifs disposant d'un cours et signaler les autres.
3. Utiliser le dernier cours connu, en indiquant sa date et son ancienneté.

On privilégie le choix 3, avec une approche qui permet une valorisation partielle, mais qui ne masque jamais l'absence ou l'ancienneté d'un cours.
La date du dernier cours utilisé doit être visible dans les résultats.
A voir code retour et message (niveau warning).

## **6. La feuille de route à suivre**

Il ne faut pas développer toutes les fonctionnalités en parallèle. Voici l'ordre à privilégier.

1. **Consolider les fondations**
   - Finaliser les modèles et les schémas.
   - Stabiliser les règles `extends`.
   - Harmoniser les conventions YAML.
   - Finaliser les commandes de validation.
2. **Fiabiliser le cycle transactions / balances**
   - Transactions enrichies en YAML.
   - Recalcul complet systématique.
   - Calcul des balances à une date donnée.
   - Officialisation volontaire des balances.
   - Métadonnées et hashes.
3. **Construire les analyses patrimoniales**
   - Évolution quotidienne par wallet.
   - Consolidation au niveau utilisateur.
   - Évolution du patrimoine global.
   - Gestion des liquidités et des positions.
4. **Développer les restitutions**
   - Dashboards wallet.
   - Dashboard global utilisateur.
   - Fichiers HTML et companions YAML.
   - Graphiques de répartition et d'évolution.
5. **Améliorer l'expérience utilisateur**
   - Diagnostic global.
   - Messages d'erreur explicites.
   - Sauvegardes.
   - Documentation utilisateur.
6. **Étendre progressivement les fonctionnalités**
   - Nouveaux fournisseurs financiers.
   - Importation de factsheets.
   - Nouveaux types d'actifs.
   - Analyses patrimoniales plus avancées.

## **7. Avis final**

Patrimonia a une vraie cohérence architecturale. Il y a une bonne adéquation entre les outils techniques, les formats de données et le besoin fonctionnel.

Les trois décisions à préserver :

1. **Les données sources ne sont jamais modifiées par les traitements de calcul.**
2. **Tous les résultats calculés sont régénérables à partir de sources validées.**
3. **La complexité technique doit rester proportionnée à l'usage familial.**

**La prochaine étape concrète** : construire une spécification fonctionnelle et technique du moteur de calcul des balances, avec ses entrées, ses règles, ses sorties, ses validations et ses cas particuliers. Ce document pourrait ensuite servir directement de référence pour le développement et les tests.