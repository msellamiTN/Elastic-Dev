#!/bin/sh
set -e

ALF_URL="http://alfresco:8080/alfresco/api/-default-/public/alfresco/versions/1"

echo "=== [1/3] Attente de la disponibilité de l'API REST d'Alfresco ==="
until curl -s -u admin:admin "$ALF_URL/probes/-ready-" | grep -q '"status":"Green"'; do
  echo "Alfresco démarre... attente de 5 secondes."
  sleep 5
done

echo "=== [2/3] Création du dossier de démo ==="
FOLDER_RESPONSE=$(curl -s -u admin:admin -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "POC-Elasticsearch-8.13.4", "nodeType": "cm:folder"}' \
  "$ALF_URL/nodes/-root-/children")

FOLDER_ID=$(echo "$FOLDER_RESPONSE" | grep -o '"id":"[^"]*' | head -n 1 | cut -d'"' -f4)
echo "Espace de démo initialisé avec succès. ID : $FOLDER_ID"

echo "=== [3/3] Téléversement de documents de démo (contenu varié) ==="

upload_doc() {
  FILE_NAME="$1"
  FILE_CONTENT="$2"
  FILE_PATH="/tmp/$FILE_NAME"
  echo "$FILE_CONTENT" > "$FILE_PATH"
  curl -s -o /dev/null -X POST -u admin:admin \
    -F "filedata=@$FILE_PATH" \
    -F "filename=$FILE_NAME" \
    "$ALF_URL/nodes/$FOLDER_ID/children"
  rm -f "$FILE_PATH"
  echo "  -> $FILE_NAME envoyé."
}

upload_doc "architecture-elasticsearch.txt" \
  "L'architecture Elasticsearch repose sur une indexation distribuée en shards primaires et répliques, orchestrée par un nœud maître élu au sein du cluster."

upload_doc "migration-solr.txt" \
  "La migration depuis Solr vers Elasticsearch impose une reconstruction complète de l'index de recherche à partir des données sources du repository Alfresco."

upload_doc "extraction-tika.txt" \
  "L'extraction de texte via Apache Tika permet de transformer des fichiers binaires PDF Word ou images en contenu textuel indexable dans Elasticsearch."

upload_doc "activemq-events.txt" \
  "Les événements de transaction du repository Alfresco sont publiés de manière asynchrone sur le topic alfresco.repo.event2 via Apache ActiveMQ Artemis."

upload_doc "capacity-planning.txt" \
  "Le dimensionnement d'un cluster Elasticsearch pour six téraoctets de données impose un calcul rigoureux du nombre de shards primaires et de nœuds de données."

upload_doc "kibana-dashboard.txt" \
  "Kibana permet de visualiser les documents indexés dans Elasticsearch sous forme de tableaux de bord et de requêtes de recherche full text en temps réel."

for i in $(seq 1 20); do
  upload_doc "document_generique_$i.txt" \
    "Document de test numéro $i pour le POC de migration Alfresco vers Elasticsearch version 8.13.4. Ce contenu simule une charge documentaire réelle."
done

echo ""
echo "✔ Téléversement terminé : 26 documents envoyés."
echo "✔ Les événements ActiveMQ ont été émis vers le topic alfresco.repo.event2."
echo "✔ event-bridge devrait indexer ces documents dans Elasticsearch en quelques secondes."
echo ""
echo "Vérifiez avec : ./scripts/verify-demo.sh"
