#!/bin/sh
# Script de vérification rapide pour la démo POC Alfresco -> Elasticsearch 8.13.4
# Usage : ./scripts/verify-demo.sh

ES_URL="http://localhost:9200"

echo "==================================================================="
echo " VÉRIFICATION DE LA DÉMO — Alfresco Community -> Elasticsearch 8.13.4"
echo "==================================================================="

echo ""
echo "--- 1. Santé du cluster Elasticsearch ---"
curl -s "$ES_URL/_cluster/health?pretty"

echo ""
echo "--- 2. Nombre de documents indexés dans l'index 'alfresco' ---"
curl -s "$ES_URL/alfresco/_count?pretty"

echo ""
echo "--- 3. Exemple de recherche full-text (mot-clé: 'Elasticsearch') ---"
curl -s -X GET "$ES_URL/alfresco/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": { "match": { "content.text": "Elasticsearch" } },
    "_source": ["name", "nodeType", "content.text"],
    "size": 5
  }'

echo ""
echo "--- 4. Exemple de recherche par métadonnées (type cm:content) ---"
curl -s -X GET "$ES_URL/alfresco/_search?pretty" \
  -H "Content-Type: application/json" \
  -d '{
    "query": { "term": { "nodeType": "cm:content" } },
    "_source": ["name", "mimeType", "sizeInBytes"],
    "size": 5
  }'

echo ""
echo "==================================================================="
echo " Pour explorer visuellement : http://localhost:5601 (Kibana)"
echo " Pour suivre les logs en direct : sudo docker compose logs -f event-bridge-content"
echo "==================================================================="
