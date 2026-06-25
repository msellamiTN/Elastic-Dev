#!/bin/bash

# Définir les variables
NETWORK_NAME="elastic"
ES_CONTAINER_NAME="es01"
KIBANA_CONTAINER_NAME="kib"
ES_IMAGE="docker.elastic.co/elasticsearch/elasticsearch:8.13.4"
KIBANA_IMAGE="docker.elastic.co/kibana/kibana:8.13.4"
ES_PORT=9200
KIBANA_PORT=5601
ES_PASSWORD="1Cge99g6yEs3s4406vWk"  # Remplacez par un mot de passe sécurisé
CERTS_DIR="./certs"

# Créer un réseau Docker dédié
docker network create $NETWORK_NAME

# Lancer le conteneur Elasticsearch
docker run -d --name $ES_CONTAINER_NAME --net $NETWORK_NAME \
  -p $ES_PORT:$ES_PORT -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "ELASTIC_PASSWORD=$ES_PASSWORD" \
  $ES_IMAGE

# Attendre que Elasticsearch soit prêt
echo "Attente de 30 secondes pour que Elasticsearch soit prêt..."
sleep 30

# Générer un jeton d'inscription pour Kibana
ENROLLMENT_TOKEN=$(docker exec -it $ES_CONTAINER_NAME /bin/bash -c \
  "/usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana")

if [ -z "$ENROLLMENT_TOKEN" ]; then
  echo "Erreur lors de la génération du jeton d'inscription pour Kibana."
  exit 1
fi

echo "Jeton d'inscription pour Kibana généré avec succès."

# Créer le répertoire pour les certificats SSL
mkdir -p $CERTS_DIR

# Copier le certificat CA d'Elasticsearch depuis le conteneur vers l'hôte
docker cp $ES_CONTAINER_NAME:/usr/share/elasticsearch/config/certs/http_ca.crt $CERTS_DIR/

# Lancer le conteneur Kibana avec le jeton d'inscription et la configuration SSL
docker run -d --name $KIBANA_CONTAINER_NAME --net $NETWORK_NAME \
  -p $KIBANA_PORT:$KIBANA_PORT \
  -e "ELASTICSEARCH_HOSTS=https://$ES_CONTAINER_NAME:$ES_PORT" \
  -e "ELASTICSEARCH_ENROLLMENT_TOKEN=$ENROLLMENT_TOKEN" \
  -e "ELASTICSEARCH_SSL_VERIFICATIONMODE=full" \
  -e "ELASTICSEARCH_CA_CERT_FILE=/usr/share/kibana/config/certs/http_ca.crt" \
  $KIBANA_IMAGE

# Attendre que Kibana soit prêt
echo "Attente de 30 secondes pour que Kibana soit prêt..."
sleep 30

# Vérifier l'accès à Kibana
curl --cacert $CERTS_DIR/http_ca.crt -u elastic:$ES_PASSWORD https://localhost:$KIBANA_PORT
