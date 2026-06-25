#!/usr/bin/env python3
"""
event-bridge — Connecteur Elasticsearch "fait-maison" pour Alfresco Community.

Remplace les 3 connecteurs propriétaires Enterprise
(quay.io/alfresco/alfresco-elasticsearch-live-indexing-{metadata,content,path})
qui nécessitent une licence Hyland/Quay.io.

Compatible Elasticsearch 8.13.4 (sécurité désactivée pour la démo via
xpack.security.enabled=false côté serveur — voir docker-compose.yml).

Architecture reproduite (cf. dossier de migration Solr -> Elasticsearch) :

    Alfresco Repository --(repo.event2 topic, STOMP)--> event-bridge
                                                              |
                                  +---------------------------+---------------------------+
                                  |                           |                           |
                            worker_metadata             worker_content              worker_path
                          (props + ACL léger)      (Tika via Transform Svc)     (hiérarchie dossiers)
                                  |                           |                           |
                                  +---------------------------+---------------------------+
                                                              |
                                                        Elasticsearch 8.13.4 (_update upsert)

Limitation connue (documentée) : Alfresco Community ne publie pas les
permissions complètes dans repo.event2 (contrairement à l'Enterprise) :
le worker metadata simule un ACL minimal (owner + lecture publique) pour
les besoins de la démo.
"""

import os
import json
import time
import logging

import stomp
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("event-bridge")

# --------------------------------------------------------------------------
# Configuration (variables d'environnement, valeurs par défaut alignées sur
# le docker-compose.yml de la démo)
# --------------------------------------------------------------------------
ACTIVEMQ_HOST = os.getenv("ACTIVEMQ_HOST", "activemq")
ACTIVEMQ_STOMP_PORT = int(os.getenv("ACTIVEMQ_STOMP_PORT", "61613"))
ACTIVEMQ_USER = os.getenv("ACTIVEMQ_USER", "admin")
ACTIVEMQ_PASSWORD = os.getenv("ACTIVEMQ_PASSWORD", "admin_password")
REPO_EVENT_TOPIC = os.getenv("REPO_EVENT_TOPIC", "/topic/alfresco.repo.event2")

ALFRESCO_BASE_URL = os.getenv("ALFRESCO_BASE_URL", "http://alfresco:8080/alfresco")
ALFRESCO_USER = os.getenv("ALFRESCO_USER", "admin")
ALFRESCO_PASSWORD = os.getenv("ALFRESCO_PASSWORD", "admin")

TRANSFORM_URL = os.getenv("ALFRESCO_TRANSFORM_URL", "http://transform-service:8090")

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
ES_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ES_INDEX = os.getenv("ELASTICSEARCH_INDEX", "alfresco")
ES_URL = f"http://{ES_HOST}:{ES_PORT}"

# Profils actifs pour cette instance (permet de scaler le worker content
# indépendamment, comme demandé dans le dossier d'architecture original)
ACTIVE_PROFILES = set(os.getenv("BRIDGE_PROFILES", "metadata,content,path").split(","))

CONTENT_TYPES_INDEXABLE = {"cm:content"}

# --------------------------------------------------------------------------
# Helpers Elasticsearch (API _update/_doc — inchangée entre ES 7.x et 8.x
# pour cet usage basique, sans types de mapping obsolètes)
# --------------------------------------------------------------------------

def es_index_document(node_id: str, body: dict, doc_type_hint: str = ""):
    """Indexe (ou met à jour partiellement) un document dans Elasticsearch."""
    url = f"{ES_URL}/{ES_INDEX}/_update/{node_id}"
    payload = {"doc": body, "doc_as_upsert": True}
    try:
        resp = requests.post(
            url, json=payload, headers={"Content-Type": "application/json"}, timeout=10
        )
        if resp.status_code >= 300:
            log.warning(
                "ES upsert KO (%s) node=%s %s: %s",
                doc_type_hint, node_id, resp.status_code, resp.text[:300],
            )
        else:
            log.info("ES upsert OK (%s) node=%s", doc_type_hint, node_id)
    except requests.RequestException as exc:
        log.error("Erreur réseau vers Elasticsearch pour node=%s: %s", node_id, exc)


def es_delete_document(node_id: str):
    url = f"{ES_URL}/{ES_INDEX}/_doc/{node_id}"
    try:
        resp = requests.delete(url, timeout=10)
        if resp.status_code not in (200, 404):
            log.warning("ES delete KO node=%s: %s", node_id, resp.text[:200])
        else:
            log.info("ES delete OK node=%s", node_id)
    except requests.RequestException as exc:
        log.error("Erreur réseau vers Elasticsearch (delete) node=%s: %s", node_id, exc)


def ensure_index_exists():
    """Crée l'index avec un mapping minimal s'il n'existe pas déjà."""
    resp = requests.head(f"{ES_URL}/{ES_INDEX}")
    if resp.status_code == 200:
        log.info("Index '%s' déjà présent.", ES_INDEX)
        return
    mapping = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "name": {"type": "text"},
                "nodeType": {"type": "keyword"},
                "isFolder": {"type": "boolean"},
                "isFile": {"type": "boolean"},
                "createdAt": {"type": "date"},
                "modifiedAt": {"type": "date"},
                "mimeType": {"type": "keyword"},
                "sizeInBytes": {"type": "long"},
                "path": {"type": "keyword"},
                "primaryHierarchy": {"type": "keyword"},
                "owner": {"type": "keyword"},
                "readers": {"type": "keyword"},
                "content": {
                    "properties": {"text": {"type": "text"}}
                },
            }
        },
    }
    resp = requests.put(
        f"{ES_URL}/{ES_INDEX}", json=mapping, headers={"Content-Type": "application/json"}
    )
    if resp.status_code < 300:
        log.info("Index '%s' créé avec succès.", ES_INDEX)
    else:
        log.warning("Création de l'index KO: %s", resp.text[:300])


# --------------------------------------------------------------------------
# Worker : profil METADATA
# --------------------------------------------------------------------------

def worker_metadata(event_type: str, resource: dict):
    node_id = resource.get("id")
    if not node_id:
        return

    body = {
        "name": resource.get("name"),
        "nodeType": resource.get("nodeType"),
        "isFolder": resource.get("isFolder", False),
        "isFile": resource.get("isFile", False),
        "createdAt": resource.get("createdAt"),
        "modifiedAt": resource.get("modifiedAt"),
        # ACL simulé : Alfresco Community ne publie pas les permissions
        # réelles dans repo.event2 (limitation connue). On simule un
        # owner + lecture publique pour la démo.
        "owner": (resource.get("createdByUser") or {}).get("id", "unknown"),
        "readers": ["GROUP_EVERYONE"],
    }
    content = resource.get("content")
    if content:
        body["mimeType"] = content.get("mimeType")
        body["sizeInBytes"] = content.get("sizeInBytes")

    es_index_document(node_id, body, doc_type_hint="metadata")


# --------------------------------------------------------------------------
# Worker : profil CONTENT (extraction texte via Transform Service / Tika)
# --------------------------------------------------------------------------

def fetch_node_binary(node_id: str):
    url = f"{ALFRESCO_BASE_URL}/api/-default-/public/alfresco/versions/1/nodes/{node_id}/content"
    try:
        resp = requests.get(url, auth=(ALFRESCO_USER, ALFRESCO_PASSWORD), timeout=30)
        if resp.status_code == 200:
            return resp.content
        log.warning("Téléchargement binaire KO node=%s: HTTP %s", node_id, resp.status_code)
    except requests.RequestException as exc:
        log.error("Erreur réseau Alfresco (download) node=%s: %s", node_id, exc)
    return None


def extract_text_via_tika(binary: bytes, filename: str, mime_type: str) -> str:
    """Appelle l'Alfresco Transform Service (AIO, Apache Tika) en mode
    synchrone pour extraire le texte brut d'un fichier binaire."""
    url = f"{TRANSFORM_URL}/transform"
    files = {"file": (filename, binary, mime_type or "application/octet-stream")}
    data = {"targetMimetype": "text/plain", "sourceMimetype": mime_type or "application/octet-stream"}
    try:
        resp = requests.post(url, files=files, data=data, timeout=60)
        if resp.status_code == 200:
            return resp.text
        log.warning("Extraction Tika KO (%s): HTTP %s — %s", filename, resp.status_code, resp.text[:200])
    except requests.RequestException as exc:
        log.error("Erreur réseau Transform Service pour %s: %s", filename, exc)
    return ""


def worker_content(event_type: str, resource: dict):
    node_id = resource.get("id")
    content = resource.get("content")
    node_type = resource.get("nodeType")

    if not node_id or not content or node_type not in CONTENT_TYPES_INDEXABLE:
        return  # rien à extraire (dossier, ou pas de binaire)

    binary = fetch_node_binary(node_id)
    if binary is None:
        return

    mime_type = content.get("mimeType", "application/octet-stream")
    text = extract_text_via_tika(binary, resource.get("name", node_id), mime_type)

    body = {"content": {"text": text}}
    es_index_document(node_id, body, doc_type_hint="content")


# --------------------------------------------------------------------------
# Worker : profil PATH (hiérarchie de dossiers — instance unique requise)
# --------------------------------------------------------------------------

def worker_path(event_type: str, resource: dict):
    node_id = resource.get("id")
    if not node_id:
        return
    hierarchy = resource.get("primaryHierarchy", [])
    body = {"primaryHierarchy": hierarchy}
    es_index_document(node_id, body, doc_type_hint="path")


# --------------------------------------------------------------------------
# Listener STOMP : réception + routage des événements CloudEvents Alfresco
# --------------------------------------------------------------------------

class AlfrescoEventListener(stomp.ConnectionListener):
    def __init__(self, connection):
        self.connection = connection

    def on_error(self, frame):
        log.error("Erreur STOMP reçue: %s", frame.body)

    def on_disconnected(self):
        log.warning("Déconnecté d'ActiveMQ — tentative de reconnexion...")
        connect_with_retry(self.connection)

    def on_message(self, frame):
        try:
            event = json.loads(frame.body)
        except json.JSONDecodeError:
            log.warning("Message non-JSON ignoré: %s", frame.body[:200])
            return

        event_type = event.get("type", "")
        data = event.get("data", {})
        resource = data.get("resource", {})

        if not event_type.startswith("org.alfresco.event.node."):
            return  # on ignore les événements de permission, etc. pour cette démo

        node_id = resource.get("id", "?")
        log.info("Événement reçu: %s | node=%s | name=%s", event_type, node_id, resource.get("name"))

        if event_type == "org.alfresco.event.node.Deleted":
            es_delete_document(node_id)
            return

        # Created / Updated -> dispatch vers les profils actifs sur cette instance
        if "metadata" in ACTIVE_PROFILES:
            worker_metadata(event_type, resource)
        if "content" in ACTIVE_PROFILES:
            worker_content(event_type, resource)
        if "path" in ACTIVE_PROFILES:
            worker_path(event_type, resource)


def connect_with_retry(conn: "stomp.Connection", max_wait=60):
    delay = 2
    while True:
        try:
            conn.connect(ACTIVEMQ_USER, ACTIVEMQ_PASSWORD, wait=True)
            conn.subscribe(destination=REPO_EVENT_TOPIC, id="event-bridge-1", ack="auto")
            log.info("Connecté à ActiveMQ (%s:%s) et abonné à %s", ACTIVEMQ_HOST, ACTIVEMQ_STOMP_PORT, REPO_EVENT_TOPIC)
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("Connexion ActiveMQ échouée (%s). Nouvelle tentative dans %ss...", exc, delay)
            time.sleep(delay)
            delay = min(delay * 2, max_wait)


def wait_for_elasticsearch():
    while True:
        try:
            resp = requests.get(f"{ES_URL}/_cluster/health", timeout=5)
            if resp.status_code == 200 and resp.json().get("status") in ("yellow", "green"):
                log.info("Elasticsearch 8.x prêt (status=%s).", resp.json().get("status"))
                return
        except requests.RequestException:
            pass
        log.info("En attente d'Elasticsearch...")
        time.sleep(3)


def main():
    log.info("=== event-bridge démarrage (profils actifs: %s) ===", ", ".join(sorted(ACTIVE_PROFILES)))
    wait_for_elasticsearch()
    ensure_index_exists()

    hosts = [(ACTIVEMQ_HOST, ACTIVEMQ_STOMP_PORT)]
    conn = stomp.Connection(host_and_ports=hosts, heartbeats=(10000, 10000))
    listener = AlfrescoEventListener(conn)
    conn.set_listener("alfresco-listener", listener)
    connect_with_retry(conn)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        log.info("Arrêt demandé, fermeture de la connexion ActiveMQ.")
        conn.disconnect()


if __name__ == "__main__":
    main()
