# Atelier 5 : Réindexation et Recherche sur Elasticsearch

Ce document combine théorie approfondie et pratique appliquée sur la console Dev Tools de Kibana. Vous y découvrirez comment Elasticsearch stocke, analyse, indexe, recherche et évalue la pertinence de vos données de sécurité et applicatives.

---

## Section 1 : Sous le capot d'Elasticsearch (Analyse du texte & Mapping)

Pour formuler des requêtes performantes et pertinentes, il est indispensable de comprendre la mécanique d'indexation d'Elasticsearch.

### 1.1 L'Index Inversé (Inverted Index)

Contrairement aux bases de données relationnelles (SQL) qui scannent les lignes de manière séquentielle ou utilisent des index B-Tree, Elasticsearch repose sur une structure de données appelée **Index Inversé**.

Lorsqu'un document contenant du texte est ingéré, Elasticsearch extrait chaque mot, le normalise, et l'ajoute à un dictionnaire géant. Pour chaque mot (ou token), l'index inversé stocke la liste ordonnée des identifiants de documents dans lesquels il apparaît, ainsi que sa position exacte.

**Exemple conceptuel :**

Soit deux documents à indexer :

- Doc 1 : *"Alerte de sécurité sur le serveur"*
- Doc 2 : *"Tentative de connexion sur le serveur"*

L'index inversé généré ressemble à ceci :

| Token (Terme) | Documents associés | Fréquence | Positions |
|---|---|---|---|
| alerte | Doc 1 | 1 | [0] |
| connexion | Doc 2 | 1 | [2] |
| de | Doc 1, Doc 2 | 2 | D1:[1], D2:[1] |
| sécurité | Doc 1 | 1 | [2] |
| sur | Doc 1, Doc 2 | 2 | D1:[3], D2:[3] |
| serveur | Doc 1, Doc 2 | 2 | D1:[5], D2:[5] |

> **Force de l'index inversé :** Une recherche sur le terme `serveur` ne nécessite aucun parcours de table. Elasticsearch accède directement à l'entrée `serveur` dans l'index inversé et sait instantanément que les documents 1 et 2 correspondent.

### 1.2 Fonctionnement des Analyzers et des Token Filters

Le traitement qui transforme un texte brut en une série de termes normalisés dans l'index inversé s'appelle l'**Analyse**. Ce processus est piloté par un **Analyzer**, qui est composé de trois briques séquentielles :

1. **Character Filters** : Traitent le flux de caractères initial. Ils peuvent supprimer des balises (ex: `html_strip`) ou remplacer des motifs de texte.
2. **Tokenizer** : Découpe la chaîne de caractères propre en termes individuels (Tokens). Le tokenizer le plus courant est le `standard` tokenizer, qui découpe au niveau des espaces et des signes de ponctuation.
3. **Token Filters** : Reçoivent les tokens et appliquent des modifications. Les plus importants sont :
   - `lowercase` : Convertit tous les caractères en minuscules.
   - `asciifolding` : Supprime les signes diacritiques (les accents). Exemple : *sécurité → securite*.
   - `stop` : Supprime les mots vides sans valeur sémantique (ex: "le", "la", "de", "sur", "en").
   - `stemmer` (Racinisation) : Réduit un mot à sa racine morphologique pour regrouper les déclinaisons. Exemple : *connexions, connecté, connecter → connect*.

#### Test pratique dans Kibana : L'Analyze API

L'API `_analyze` permet de tester le comportement d'un analyseur en temps réel.

```json
POST /_analyze
{
  "analyzer": "french",
  "text": "L'administrateur s'est connecté sur le serveur de production !"
}
```

Le résultat de cette commande montre l'exclusion complète des mots vides (*le, sur, de*) et la réduction des mots significatifs à leur racine sémantique (*administrat, connect, serveur, product*).

### 1.3 Le Mapping : Typage Strict vs Dynamique

Le **Mapping** est l'équivalent du schéma de table SQL pour Elasticsearch. Il définit le type de chaque champ (`integer`, `date`, `boolean`, `text`, `keyword`, etc.).

- **Dynamic Mapping** : Par défaut, si vous insérez un document sans index préalable, Elasticsearch devine les types. Bien que pratique en phase de maquettage, le dynamic mapping est fortement déconseillé en production car il consomme des ressources et commet parfois des erreurs de typage (ex: une adresse IP typée en `text` au lieu de `ip`).
- **Explicit Mapping** : Vous déclarez vous-même la structure de votre index.

#### La distinction fondamentale : `text` contre `keyword`

Le choix entre ces deux types de chaînes de caractères est capital :

| Caractéristique | Type `text` | Type `keyword` |
|---|---|---|
| **Analyse** | Passe par un Analyzer (découpé en tokens) | Stocké tel quel (chaîne brute non modifiée) |
| **Cas d'usage** | Recherche plein texte (corps d'email, logs bruts) | Identifiants, statuts, tags, adresses IP, emails |
| **Opérations** | Recherche floue, recherche par mots-clés | Filtres stricts, tris (`sort`), agrégations (`aggs`) |

### 1.4 Les Multi-champs (Multi-fields)

Il est fréquent de vouloir utiliser un même champ textuel à la fois pour de la recherche plein texte (nécessitant un type `text`) et pour du tri ou des agrégations statistiques (nécessitant un type `keyword`).

C'est là qu'interviennent les **Multi-champs**. Ils permettent d'indexer une même donnée brute de plusieurs manières différentes sous des sous-champs distincts.

#### Exercice : Définition d'un mapping optimisé avec multi-champs

Créons notre index `emails_v2` doté d'un analyseur personnalisé et d'une structure de données robuste :

- Le champ `subject` peut être recherché en mode plein texte (ex: `subject = "alerte"`).
- Le champ virtuel `subject.raw` contient le sujet exact non analysé, permettant de trier les résultats par ordre alphabétique de sujet ou de faire des statistiques de volumétrie.

### 1.5 Changement de Mapping, d'Analyse (Analysis) et gestion des Alias en production

> **Règle d'or absolue :** Sur Elasticsearch, les configurations de mapping (types de champs) et de filtres d'analyse (`analysis`) existants ne peuvent pas être modifiées à chaud pour des données déjà indexées. Si vous modifiez un analyseur sur un index actif, Lucene sera incapable de lire correctement son propre index inversé historique.

Pour appliquer un nouveau mapping ou un nouvel analyseur sans interruption de service, vous devez utiliser la stratégie du **Reindex via un Alias**.

#### Étape par Étape : Processus de Migration Sans Coupure

**1. Concevoir l'index initial (v1) et lui attribuer un Alias dès le premier jour**

En production, vos applications ne doivent jamais requêter l'index physique directement (`emails` - atelier 3/4). Elles doivent requêter un pointeur logique appelé Alias (`emails_alias`).

```json
// Association de l'alias emails_alias à l'index emails_v1
POST /_aliases
{
  "actions": [
    {
      "add": {
        "index": "emails",
        "alias": "emails_alias"
      }
    }
  ]
}
```

**2. Créer le nouvel index (v2) avec la nouvelle configuration de Mapping et d'Analyse**

Lorsque vous devez ajouter un nouvel analyseur (par exemple, notre `email_analyzer` personnalisé avec `asciifolding`), vous déclarez le nouvel index physique `emails_v2` :

```json
PUT /emails_v2
{
  "settings": {
    "analysis": {
      "analyzer": {
        "email_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding"
          ]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "subject": {
        "type": "text",
        "analyzer": "email_analyzer",
        "fields": {
          "raw": {
            "type": "keyword"
          }
        }
      },
      "sender": {
        "type": "keyword"
      },
      "date": {
        "type": "date"
      },
      "body": {
        "type": "text",
        "analyzer": "email_analyzer"
      },
      "attack_type": {
        "type": "keyword"
      }
    }
  }
}
```

**3. Copier les données de l'index v1 vers l'index v2 (Reindex)**

Utilisez l'API `_reindex` d'Elasticsearch. Cette opération va lire chaque document de `emails_v1`, le faire passer par les nouveaux analyseurs de `emails_v2` et l'indexer proprement.

```json
POST /_reindex?wait_for_completion=false
{
  "source": {
    "index": "emails"
  },
  "dest": {
    "index": "emails_v2"
  }
}
```

Le paramètre `wait_for_completion=false` renvoie un ID de tâche (Task ID). Cela permet de suivre le processus en arrière-plan sans bloquer votre console Kibana si vous avez des millions de documents.

**4. Basculer l'Alias de manière atomique**

Une fois la réindexation terminée, vous devez rediriger le trafic de lecture et d'écriture vers le nouvel index de manière atomique (instantanée, en une seule transaction).

```json
POST /_aliases
{
  "actions": [
    {
      "remove": {
        "index": "emails",
        "alias": "emails_alias"
      }
    },
    {
      "add": {
        "index": "emails_v2",
        "alias": "emails_alias"
      }
    }
  ]
}
```

Grâce à cette opération atomique, aucune requête applicative n'est perdue. Les applications continuent de viser `emails_alias` sans savoir que sous le capot, elles interrogent désormais `emails_v2` configuré avec le nouvel analyseur.

**5. Supprimer l'ancien index**

Une fois les vérifications effectuées, vous pouvez libérer l'espace disque du cluster en supprimant l'ancien index physique :

```json
DELETE /emails_*
```

### 1.5 (bis) Méthode 2 : Alimentation des Données de Test (Bulk API) et Réindexation

Pour exécuter les requêtes des sections suivantes, injectons ce jeu de données :

```json
POST /emails_v2/_bulk
{ "index": { "_id": "1" } }
{ "sender": "admin@wevops.com", "subject": "Alerte Securité : Activité suspecte !", "body": "Nous avons détecté une tentative d'accès suspecte. Le mot de passe a été compromis sur la machine de test.", "date": "2024-02-15T08:30:00Z", "attack_type": "Brute Force" }
{ "index": { "_id": "2" } }
{ "sender": "phisher@fakebank.com", "subject": "URGENT : Mettez à jour votre mot de passe banque !", "body": "Votre compte bancaire est suspendu. Veuillez réinitialiser votre mot de passe immédiatement sur notre portail sécurisé.", "date": "2024-03-01T10:15:00Z", "attack_type": "Phishing" }
{ "index": { "_id": "3" } }
{ "sender": "support@wevops.com", "subject": "Maintenance hebdomadaire de la base de données", "body": "La maintenance classique aura lieu ce soir. Aucun impact majeur attendu.", "date": "2024-03-05T22:00:00Z", "attack_type": "None" }
{ "index": { "_id": "4" } }
{ "sender": "security-bot@wevops.com", "subject": "Rapport hebdomadaire - Phishing simulé", "body": "Le test d'intrusion mensuel montre que 5 utilisateurs ont cliqué sur le faux lien de la banque.", "date": "2024-04-10T14:00:00Z", "attack_type": "Phishing" }
```

---

## Section 2 : Requêtage de Données (Query DSL)

Le Query DSL d'Elasticsearch permet de formaliser des intentions de recherche très fines.

### 2.1 Recherche de termes exacts (`term` & `terms`)

La requête de terme recherche une valeur exacte dans l'index inversé. Elle n'analyse pas la chaîne de recherche fournie. Elle est donc particulièrement performante pour filtrer les champs de type `keyword`.

```json
GET /emails_v2/_search
{
  "query": {
    "term": {
      "attack_type": "Phishing"
    }
  }
}
```

Si vous souhaitez faire correspondre plusieurs valeurs possibles (équivalent du `IN` en SQL), utilisez `terms` :

```json
GET /emails_v2/_search
{
  "query": {
    "terms": {
      "attack_type": ["Phishing", "Brute Force"]
    }
  }
}
```

### 2.2 Recherche Plein Texte (`match`)

La requête `match` analyse la chaîne de recherche avec le même analyseur que celui configuré sur le champ cible avant d'interroger l'index inversé.

```json
GET /emails_v2/_search
{
  "query": {
    "match": {
      "subject": "sécurité suspecte"
    }
  }
}
```

Ici, Elasticsearch cherche les documents contenant le token *securite* **OR** le token *suspecte*. Les deux documents contenant l'un ou l'autre (ou les deux) seront renvoyés.

Pour forcer la présence de tous les termes de la recherche (opérateur logique **AND**), utilisez l'option `operator` :

```json
GET /emails_v2/_search
{
  "query": {
    "match": {
      "subject": {
        "query": "sécurité suspecte",
        "operator": "and"
      }
    }
  }
}
```

### 2.3 Recherche de phrases exactes (`match_phrase`)

Si l'ordre des mots et leur proximité immédiate revêtent une importance sémantique, la requête `match_phrase` est indispensable.

```json
GET /emails_v2/_search
{
  "query": {
    "match_phrase": {
      "body": "mot de passe"
    }
  }
}
```

Le document 1 et le document 2 seront renvoyés car ils contiennent l'expression exacte *"mot de passe"*.

#### Paramètre `slop` (Proximité tolérée)

Le paramètre `slop` autorise un certain nombre d'écarts de mots ou d'inversions par rapport à la phrase recherchée.

```json
GET /emails_v2/_search
{
  "query": {
    "match_phrase": {
      "body": {
        "query": "tentative suspecte",
        "slop": 2
      }
    }
  }
}
```

Trouvera *"tentative d'accès suspecte"* (Doc 1) car l'écart de 1 mot (*"d'accès"*) est inclus dans la limite du slop (2).

### 2.4 Recherche dans les plages de dates et valeurs (`range`)

La requête `range` s'applique aux types numériques, IP ou temporels (`date`).

```json
GET /emails_v2/_search
{
  "query": {
    "range": {
      "date": {
        "gte": "2024-02-15T00:00:00Z",
        "lt": "2024-04-01T00:00:00Z"
      }
    }
  }
}
```

---

## Section 3 : Combiner et Filtrer (Boolean Queries)

Pour élaborer des scénarios de filtrage complexes, la structure logique `bool` combine plusieurs requêtes élémentaires.

### 3.1 Anatomie du bloc `bool`

Une requête `bool` accepte quatre types de clauses :

- **`must`** : Les clauses doivent obligatoirement correspondre au document. Ces clauses participent activement au calcul du score de pertinence (`_score`).
- **`filter`** : Les clauses doivent obligatoirement correspondre au document. Cependant, contrairement au `must`, le `filter` s'exécute de manière binaire (vrai/faux) et n'impacte pas le score.
- **`should`** : Clauses facultatives (sauf s'il s'agit de la seule structure présente, auquel cas au moins une doit matcher). Si un document correspond à une clause `should`, sa pertinence (`_score`) est boostée.
- **`must_not`** : Exclut strictement les documents correspondants (n'influence pas le score).

### 3.2 Requêtes de recherche vs Filtrage des recherches : Le Cache

Il est capital de distinguer l'utilisation de `must` et de `filter` pour optimiser les performances de vos requêtes.

**Pourquoi privilégier `filter` ?**

Lorsqu'une clause de filtrage s'exécute dans un bloc `filter`, Elasticsearch évalue la correspondance sous forme de tableau binaire (un *Bitset* : 1 si le document matche, 0 sinon). Ces bitsets sont mis en cache en mémoire vive par Elasticsearch.

Si la même requête de filtrage est exécutée par un autre utilisateur, Elasticsearch récupère le résultat instantanément depuis le cache, évitant ainsi un accès disque ou des calculs de filtres coûteux.

#### Exemple d'optimisation (Requête combinée complexe)

```json
GET /emails_v2/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "body": "mot de passe" } }
      ],
      "filter": [
        { "term": { "attack_type": "Phishing" } },
        { "range": { "date": { "gte": "2024-03-01" } } }
      ],
      "must_not": [
        { "term": { "sender": "support@wevops.com" } }
      ]
    }
  }
}
```

---

## Section 4 : Algorithmique du Score & Optimisation de la Pertinence

Le moteur de recherche d'Elasticsearch ne se contente pas de trouver des documents, il les trie par ordre décroissant de pertinence via le champ de métadonnées `_score`.

### 4.1 Comprendre le calcul du Score (L'algorithme BM25)

Par défaut, Elasticsearch évalue la pertinence à l'aide de l'algorithme mathématique **Okapi BM25**. La formule générale s'appuie sur trois facteurs fondamentaux :

**1. La Fréquence du Terme (TF — Term Frequency)**

Plus le terme recherché apparaît de nombreuses fois dans un champ spécifique d'un document, plus le score de ce document augmente.

> **Spécificité BM25 :** Contrairement à l'ancienne méthode TF-IDF où le score augmentait de façon linéaire infinie, BM25 applique une courbe de saturation logarithmique. Au-delà d'un certain seuil d'occurrences d'un mot dans un même champ, l'impact sur le score plafonne.

**2. La Fréquence Inverse du Document (IDF — Inverse Document Frequency)**

Plus un terme est commun et répandu dans l'ensemble de votre index, moins il apporte de points au score final du document (ex: le mot "serveur" ou "compte"). À l'inverse, si un mot recherché est très rare dans l'index global (ex: "compromis" ou "exfiltration"), sa présence attribue un score très élevé au document.

La formule simplifiée de l'IDF dans Elasticsearch s'exprime de manière générale comme le logarithme du rapport entre le nombre total de documents de l'index et le nombre de documents contenant le terme recherché.

**3. La Longueur du Champ (Field Length Normalization)**

Si un terme recherché est localisé dans un champ court (comme un `subject` de 5 mots), il possède un poids sémantique bien plus important que s'il est noyé dans un champ extrêmement long (comme un `body` de 1000 mots). BM25 pénalise ainsi les documents dont le champ contenant la correspondance est exagérément long par rapport à la moyenne globale des documents de l'index.

### 4.2 Amélioration de la Pertinence (Techniques de Boost)

Vous pouvez configurer Elasticsearch pour influencer le calcul naturel du score afin de refléter des logiques métier précises.

#### Technique 1 : Le Boosting de champs à la recherche (`^`)

Dans une recherche multi-champs (`multi_match`), vous pouvez spécifier qu'un champ a plus d'importance qu'un autre en utilisant le caractère circonflexe `^` suivi d'un multiplicateur.

```json
GET /emails_v2/_search
{
  "query": {
    "multi_match": {
      "query": "compromis",
      "fields": ["subject^4", "body"]
    }
  }
}
```

Dans cet exemple, une correspondance trouvée dans le champ `subject` donne un score de pertinence 4 fois supérieur à une correspondance localisée dans le `body`.

#### Technique 2 : La requête `constant_score`

Parfois, la pertinence statistique (BM25) n'a aucun sens. Par exemple, si vous cherchez tous les serveurs critiques de l'entreprise, vous voulez simplement les lister sans qu'un calcul de score complexe ne soit effectué. Vous souhaitez attribuer un score fixe et égal à tous les résultats correspondants.

```json
GET /emails_v2/_search
{
  "query": {
    "constant_score": {
      "filter": {
        "term": { "attack_type": "Brute Force" }
      },
      "boost": 1.5
    }
  }
}
```

---

## Section 5 : Requêtage Avancé

Pour traiter des cas d'usage réels, nous devons manipuler des requêtes multi-champs complexes, du tri strict, de l'exclusion de résultats et de la pagination de gros volumes de données.

### 5.1 Recherche Multi-champs (`multi_match`)

La requête `multi_match` permet d'exécuter une recherche plein texte sur plusieurs champs cibles simultanément (ex: chercher "suspecte" à la fois dans le `subject` et le `body`).

```json
GET /emails_v2/_search
{
  "query": {
    "multi_match": {
      "query": "activité suspecte",
      "fields": ["subject", "body"],
      "type": "best_fields"
    }
  }
}
```

Le type `best_fields` (par défaut) calcule le score de chaque champ individuellement et utilise le score du champ le plus pertinent pour évaluer le document.

### 5.2 Recherche Exclusive (`must_not`)

La clause `must_not` agit comme une barrière logique stricte. Tout document matchant un critère défini dans ce bloc est banni des résultats de recherche. Elle n'applique aucun calcul de score et tire profit des caches de filtres.

```json
GET /emails_v2/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "body": "sécurité" } }
      ],
      "must_not": [
        { "term": { "attack_type": "None" } }
      ]
    }
  }
}
```

### 5.3 Tri des Résultats (`sort`)

Par défaut, Elasticsearch trie les résultats par ordre décroissant de pertinence (`_score`). Cependant, vous pouvez forcer un tri sur des champs de type `keyword`, `date` ou numériques.

> **Attention :** Dès qu'un tri explicite est configuré, la pertinence (`_score`) n'est plus calculée (elle sera retournée à `null` ou `0.0`) pour maximiser la vitesse d'exécution de la requête.

```json
GET /emails_v2/_search
{
  "query": {
    "match_all": {}
  },
  "sort": [
    {
      "date": {
        "order": "desc"
      }
    },
    {
      "sender": {
        "order": "asc"
      }
    }
  ]
}
```

### 5.4 Les Paginations

En production, il est interdit de récupérer des millions de résultats d'un coup, sous peine de saturer la mémoire (JVM OutOfMemory). Elasticsearch propose deux méthodes majeures de pagination.

#### Méthode 1 : La pagination classique (`from` / `size`)

La méthode historique, simple mais limitée.

- **`size`** : Nombre de documents à retourner (équivalent de `LIMIT` en SQL).
- **`from`** : Index de départ (offset) (équivalent de `OFFSET` en SQL).

```json
GET /emails_v2/_search
{
  "query": { "match_all": {} },
  "from": 10,
  "size": 5
}
```

Cette requête récupère les documents de la 11ème à la 15ème position.

> **Le piège de la pagination profonde (Deep Pagination) :** Par défaut, Elasticsearch limite la somme de `from + size` à 10 000 documents (`index.max_result_window`). Pourquoi ? Si vous demandez `from: 9990` et `size: 10` sur un index à 5 shards, chaque shard doit extraire ses 10 000 meilleurs résultats, les envoyer au nœud coordonnateur qui devra trier et fusionner 50 000 résultats en mémoire pour ne vous en renvoyer que 10. C'est un goulot d'étranglement dramatique pour le cluster.

#### Méthode 2 : La pagination infinie (`search_after`)

Pour paginer au-delà de 10 000 documents, il faut utiliser la pagination par curseur : `search_after`. Le principe : vous devez trier vos documents de manière unique (ex: par `date` puis par `_id` comme clé de départage). Elasticsearch utilise la valeur de tri du dernier document retourné comme curseur pour la page suivante.

**Étape 1 : Première requête pour obtenir la première page**

```json
GET /emails_v2/_search
{
  "size": 2,
  "query": { "match_all": {} },
  "sort": [
    { "date": "asc" },
    { "_id": "asc" }
  ]
}
```

Imaginons que le dernier document renvoyé possède les valeurs de tri suivantes : `[ "2024-03-01T10:15:00.000Z", "2" ]`.

**Étape 2 : Requête suivante en injectant le curseur**

```json
GET /emails_v2/_search
{
  "size": 2,
  "query": { "match_all": {} },
  "sort": [
    { "date": "asc" },
    { "_id": "asc" }
  ],
  "search_after": [ "2024-03-01T10:15:00.000Z", "2" ]
}
```

Cette technique est sans limite de profondeur et extrêmement économe en ressources pour le cluster.

---

## Section 6 : Meilleures Pratiques en Production (Best Practices)

Pour assurer la stabilité, les performances et l'évolutivité de vos clusters Elasticsearch en production, appliquez scrupuleusement ces règles empiriques :

### 6.1 Bonnes pratiques de Sharding (Dimensionnement)

- **Taille cible d'un Shard** : Pour les cas d'usage de recherche d'entreprise classique, visez une taille de shard Lucene comprise entre 15 Go et 30 Go. Pour l'analyse de logs / SIEM, vous pouvez monter jusqu'à 50 Go.
- **Ne sur-shardez pas (Over-sharding)** : Chaque shard consomme des ressources système (CPU, descripteurs de fichiers, RAM pour la gestion de l'état du cluster). Avoir des milliers de petits shards de quelques mégaoctets est une cause majeure d'instabilité.
- **Règle de RAM par Shard** : Essayez de ne pas dépasser un ratio de 20 shards par gigaoctet de heap JVM alloué sur un nœud de données.

### 6.2 Bonnes pratiques de Mapping

- **Désactivez le Dynamic Mapping** : Configurez toujours `"dynamic": "strict"` sur vos index de production pour forcer un schéma de données documenté et propre.
- **Utilisez `keyword` à bon escient** : N'indexez pas de champs numériques (comme des codes postaux ou codes d'erreur) en `integer` si vous ne ferez jamais de calculs mathématiques dessus (somme, moyenne, plages). Indexez-les en `keyword` pour des filtres beaucoup plus rapides.
- **N'abusez pas du type `text`** : Si vous n'avez pas besoin de recherche plein texte sur un champ, stockez-le exclusivement en `keyword` pour économiser l'espace disque et la RAM du cluster.

### 6.3 Bonnes pratiques de Requêtage (Querying)

- **Filtrez avant de chercher** : Placez toujours vos critères de filtrage stricts (dates, statuts, identifiants) dans des clauses `filter` d'une requête `bool` plutôt que dans des clauses `must`. Vous libérerez de la charge CPU en évitant le calcul inutile du score et profiterez du cache de requêtes.
- **Évitez les jokers en début de chaîne** : Les requêtes avec wildcard du type `{"wildcard": {"sender": "*@wevops.com"}}` sont extrêmement coûteuses. Elasticsearch doit scanner l'intégralité de l'index inversé. Privilégiez l'utilisation d'analyzers personnalisés adaptés (comme l'analyseur d'adresses email).
