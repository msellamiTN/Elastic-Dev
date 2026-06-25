#!/bin/sh
set -e

echo "=== [1/3] Attente de la disponibilité complète de l'API REST d'Alfresco ==="
until curl -s -u admin:admin "http://alfresco:8080/alfresco/api/-default-/public/alfresco/versions/1/probes/-ready-" | grep -q '"status":"Green"'; do
  echo "Alfresco démarre... attente de 5 secondes."
  sleep 5
done

echo "=== [2/3] Création du dossier racine de Benchmark ==="
FOLDER_RESPONSE=$(curl -s -u admin:admin -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Large-Scale-Benchmark", "nodeType": "cm:folder"}' \
  "http://alfresco:8080/alfresco/api/-default-/public/alfresco/versions/1/nodes/-root-/children")

FOLDER_ID=$(echo "$FOLDER_RESPONSE" | grep -o '"id":"[^"]*' | head -n 1 | cut -d'"' -f4)
echo "Dossier créé avec succès. ID : $FOLDER_ID"

echo "=== [3/3] Injection de documents de test textuels ==="
for i in $(seq 1 150); do
  echo "Génération du fichier temporaire local $i..."
  FILE_PATH="/tmp/perf_doc_$i.txt"
  echo "ID_Document: $i. Ce fichier simule l'extraction de métadonnées et de contenu textuel enrichi pour les tests de performance du connecteur Elasticsearch d'Alfresco." > "$FILE_PATH"
  
  echo "Téléversement du fichier $i vers Alfresco..."
  curl -s -o /dev/null -X POST -u admin:admin \
    -F "filedata=@$FILE_PATH" \
    -F "filename=Performance_Doc_$i.txt" \
    "http://alfresco:8080/alfresco/api/-default-/public/alfresco/versions/1/nodes/$FOLDER_ID/children"
  
  rm -f "$FILE_PATH"
done

echo "✔ Injection terminée avec succès. Déclenchement automatique du job de réindexation..."