# POC Ready-to-Demo — Alfresco Community → Elasticsearch 8.13.4

Démo complète et fonctionnelle (pas de simulation) montrant la migration
architecturale Alfresco Solr → Elasticsearch, **sans licence Enterprise**.

## Ce qui tourne réellement

| Composant | Rôle | Statut |
|---|---|---|
| `alfresco` | Repository Alfresco Community 7.4, `repo.event2` activé | Réel |
| `postgres` | Base transactionnelle | Réel |
| `activemq` | Broker d'événements (STOMP + OpenWire) | Réel |
| `transform-service` | Extraction de texte (Apache Tika) | Réel |
| `elasticsearch` | **Elasticsearch 8.13.4**, nœud unique | Réel |
| `kibana` | **Kibana 8.13.4** (version alignée) | Réel |
| `event-bridge-{metadata,content,path}` | Connecteur maison remplaçant les 3 workers Enterprise propriétaires | Réel (code fourni) |
| `dataset-injector` | Injection automatique de 26 documents de démo | Réel |

## Pourquoi pas les connecteurs Enterprise officiels ?

Les images `quay.io/alfresco/alfresco-elasticsearch-live-indexing-*`
nécessitent une licence Hyland + des identifiants Quay.io obtenus via
ticket de support (inaccessibles sans contrat commercial). `event-bridge`
reproduit fonctionnellement leur rôle : il écoute les vrais événements
ActiveMQ (`alfresco.repo.event2`), construit le JSON d'indexation, appelle
Tika pour l'extraction, et indexe dans Elasticsearch — pour le détail
voir `event-bridge/bridge.py`.

## Point spécifique à Elasticsearch 8.13.4

Depuis la branche 8.x, la sécurité (TLS + authentification) est **activée
par défaut**. Pour garder cette démo simple à lancer, elle est explicitement
désactivée dans le `docker-compose.yml` :

```yaml
xpack.security.enabled=false
xpack.security.http.ssl.enabled=false
xpack.security.transport.ssl.enabled=false
```

**Ne jamais faire ça en production.** En conditions réelles, il faut
activer la sécurité, générer les certificats TLS et créer des comptes
de service dédiés pour chaque connecteur.

## Lancement

```bash
cd alfresco-es8-poc
sudo docker compose up -d --build
```

Patientez 2 à 3 minutes (Alfresco et Elasticsearch sont les plus lents à
démarrer). Le `dataset-injector` se déclenche automatiquement une fois
Alfresco prêt et injecte 26 documents de démo.

### Vérifier que tout fonctionne (script tout-en-un)

```bash
chmod +x scripts/verify-demo.sh
./scripts/verify-demo.sh
```

Ce script affiche : la santé du cluster, le nombre de documents indexés,
un exemple de recherche full-text, et un exemple de filtre par métadonnées.

### Explorer visuellement

- **Kibana** : http://localhost:5601 → Discover → index pattern `alfresco`
- **Console ActiveMQ** : http://localhost:8161 (admin / admin_password)
- **API Alfresco** : http://localhost:8080/alfresco (admin / admin)

### Suivre les logs en direct (utile pendant une soutenance)

```bash
sudo docker compose logs -f event-bridge-content
```

### Scaler le worker de contenu (comme dans le dossier d'architecture original)

```bash
sudo docker compose up -d --scale event-bridge-content=4
```

## Limitations connues (à assumer si questionné)

- **ACL simulé** : Alfresco Community ne publie pas les permissions
  complètes dans `repo.event2` (contrairement à l'Enterprise). Le worker
  `metadata` simule un ACL minimal (owner + lecture publique).
- **Pas de réindexation batch dédiée** : la vraie migration des 6 To
  utiliserait un job de réindexation scannant `ALF_NODE` (cf. le dossier
  d'architecture). Pour cette démo, l'injection initiale via l'API REST
  suffit à déclencher les événements et peupler l'index.
- **Sécurité désactivée** : voir section ci-dessus — acceptable en POC,
  jamais en production.

## Réinitialiser complètement

```bash
sudo docker compose down -v
sudo docker compose up -d --build
```
