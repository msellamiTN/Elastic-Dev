# 🎓 Atelier Jour 2 : Maîtrise d'Elasticsearch (Recherche, Pertinence et Analyse)

Bienvenue dans le second atelier de la formation. Maintenant que vous savez ingérer des données via notre API Java (`email-indexer`) ou via l'API Bulk, nous allons explorer en profondeur la façon dont Elasticsearch stocke, analyse et recherche ces informations.

Toutes les requêtes de cet atelier sont pensées pour être exécutées dans la **Dev Tools Console de Kibana** (`http://localhost:5601 > Management > Dev Tools`), qui est l'outil le plus confortable pour interagir avec Elasticsearch.

---

## 🧠 Section 1 : Sous le capot d'Elasticsearch (Théorie appliquée)

Avant de lancer nos recherches, il est crucial de comprendre comment Elasticsearch transforme vos documents.

### 1.1 L'Inverted Index (Index Inversé)
Elasticsearch ne parcourt pas tous les documents un par un (comme un `LIKE %...%` en SQL). Il utilise un **Index Inversé**. 
Lorsqu'il lit la phrase `"Alerte de sécurité"`, il la découpe en mots (tokens) et crée un dictionnaire pointant vers les IDs des documents :
- `alerte` -> Doc 1, Doc 4
- `de` -> Doc 1, Doc 2, Doc 4
- `sécurité` -> Doc 1, Doc 9

### 1.2 Les Analyzers et Token Filters
L'analyse de texte est le processus qui transforme le texte brut en termes (tokens) ajoutés à l'index inversé. Un Analyzer est composé de :
1. **Character Filters** (ex: supprimer le HTML `<b>`)
2. **Tokenizer** (ex: découper selon les espaces)
3. **Token Filters** (ex: tout mettre en minuscules, retirer les mots vides "le, la, de", racinisation/stemming).

### 1.3 Testons l'Analyze API
Regardez comment Elasticsearch analyse nativement le sujet d'un email :

```json
GET /_analyze
{
  "analyzer": "standard",
  "text": "Alerte de sécurité critique sur le serveur !"
}
```
*Le résultat montrera les tokens : `alerte`, `de`, `sécurité`, `critique`, `sur`, `le`, `serveur`. Notez que la ponctuation a disparu et tout est en minuscules.*

---

## 🛠️ Section 2 : Le Mapping et les Multi-champs

Le Mapping est le schéma de votre index (l'équivalent de la définition de table en SQL). 

### 2.1 Différence entre `text` et `keyword`
- Un champ `text` passe par l'Analyzer (recherche plein texte).
- Un champ `keyword` est stocké **exactement** tel quel (idéal pour le filtrage exact, les tris et les agrégations).

### 2.2 Exercice : Définir un Mapping optimisé pour nos Emails
Plutôt que de laisser Elasticsearch deviner (Dynamic Mapping), nous allons créer un nouvel index avec un mapping précis incluant des **multi-champs**. Les multi-champs permettent d'indexer la même donnée de deux manières différentes.

```json
PUT /emails_v2
{
  "settings": {
    "analysis": {
      "analyzer": {
        "email_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding"]
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
          "raw": { "type": "keyword" } 
        }
      },
      "sender": { "type": "keyword" },
      "date": { "type": "date" },
      "body": { "type": "text", "analyzer": "email_analyzer" },
      "attack_type": { "type": "keyword" }
    }
  }
}
```
> [!NOTE]
> Ici, `subject` est indexé en tant que texte analysé pour la recherche de mots-clés, MAIS son sous-champ `subject.raw` est un `keyword` pour pouvoir filtrer sur le sujet exact. `asciifolding` permet de retirer les accents (é devient e).

---

## 🔍 Section 3 : Requêtage des Données (Queries)

Maintenant que nos données sont bien structurées, apprenons à les interroger.

### 3.1 La recherche de termes exacts (`term`)
Utilisée sur les champs `keyword` pour trouver une valeur exacte (pas d'analyse lors de la requête).

```json
GET /emails/_search
{
  "query": {
    "term": {
      "attack_type": "Phishing"
    }
  }
}
```

### 3.2 La recherche Plein Texte (`match`)
Utilisée sur les champs `text`. Elasticsearch va analyser la requête avant de chercher dans l'index inversé.

```json
GET /emails/_search
{
  "query": {
    "match": {
      "subject": "alerte sécurité"
    }
  }
}
```
*(Trouvera tous les documents contenant "alerte" OU "sécurité").*

### 3.3 La recherche de Phrases exactes (`match_phrase`)
L'ordre des mots compte ici !

```json
GET /emails/_search
{
  "query": {
    "match_phrase": {
      "body": "mot de passe compromis"
    }
  }
}
```

### 3.4 La recherche dans les plages de dates (`range`)

```json
GET /emails/_search
{
  "query": {
    "range": {
      "date": {
        "gte": "2024-01-01T00:00:00.000000",
        "lt": "2024-06-01T00:00:00.000000"
      }
    }
  }
}
```

---

## 🧩 Section 4 : Combiner et Filtrer (Boolean Query)

Dans la vraie vie, une requête simple ne suffit pas. La `bool` query permet de combiner la logique métier.

- `must` : La clause **doit** matcher (contribue au score).
- `filter` : La clause **doit** matcher (NE contribue PAS au score -> très rapide, mis en cache).
- `should` : La clause **devrait** matcher (booste le score si c'est le cas).
- `must_not` : La clause ne **doit pas** matcher (comme un NOT).

### 4.1 Exercice : La requête Ultime

Je veux les emails de "Phishing", reçus cette année, contenant "urgent" dans le sujet. Si l'email contient "banque" dans le corps, c'est encore plus pertinent.

```json
GET /emails/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "subject": "urgent" } }
      ],
      "filter": [
        { "term": { "attack_type": "Phishing" } },
        { "range": { "date": { "gte": "2024-01-01" } } }
      ],
      "should": [
        { "match": { "body": "banque" } }
      ]
    }
  }
}
```

---

## 🎯 Section 5 : Amélioration de la Pertinence (Le Score)

### 5.1 Comprendre le Score (BM25)
Le champ `_score` dans les résultats détermine l'ordre d'affichage. Il est basé sur l'algorithme BM25 qui prend en compte :
1. **Term Frequency (TF)** : Combien de fois le mot apparaît dans le document.
2. **Inverse Document Frequency (IDF)** : Plus un mot est rare dans l'index global, plus il donne de points.
3. **Field Length** : Un mot trouvé dans un champ court (le sujet) vaut plus de points que s'il est noyé dans un champ long (le corps de l'email).

### 5.2 Booster l'importance d'un champ
Si un mot est dans le sujet, c'est plus important que s'il est dans le corps. Utilisons le caractère circonflexe `^`.

```json
GET /emails/_search
{
  "query": {
    "multi_match": {
      "query": "fraude",
      "fields": ["subject^3", "body"]
    }
  }
}
```
> [!TIP]
> Dans cet exemple, une occurrence dans le `subject` vaut 3 fois plus de points pour le score qu'une occurrence dans le `body`.

---

## ✅ Exercices Pratiques de fin de journée

Utilisez le dataset indexé via `email-indexer` pour répondre aux questions suivantes en utilisant la Dev Tools Console de Kibana :

1. Trouvez tous les emails envoyés par `admin@wevops.com`. (Quel type de requête utiliser ?)
2. Trouvez les emails parlant de `password` dans le `body` MAIS qui ne sont pas de type `Password Attack`.
3. Écrivez une requête pour analyser comment Elasticsearch découperait le texte `l'utilisateur s'est connecté` en utilisant l'analyzer `french`.

*Bon courage ! La maîtrise du DSL (Domain Specific Language) d'Elasticsearch est la clé pour tirer pleinement parti du moteur de recherche.*
