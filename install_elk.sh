wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
sudo apt-get install apt-transport-https
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo /bin/systemctl daemon-reload
sudo /bin/systemctl enable elasticsearch.service
sudo systemctl start elasticsearch.service
#sudo systemctl stop elasticsearch.service

curl http://localhost:9200

sudo nano /etc/elasticsearch/elasticsearch.yml

sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic

export ELASTIC_PASSWORD="avzBDMSed5MUlsUk2tKZ"
sudo cp /etc/elasticsearch/certs/http_ca.crt .
sudo chmod 644 http_ca.crt
sudo apt-get update && sudo apt-get install kibana
sudo /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana

sudo /usr/share/kibana/bin/kibana-verification-code

wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg

sudo openssl x509 -fingerprint -sha256 -in /etc/elasticsearch/certs/http_ca.crt
sudo openssl x509 -fingerprint -sha256 -noout -in /etc/elasticsearch/certs/http_ca.crt | awk --field-separator="=" '{print $2}' | sed 's/://g'

sudo apt-get update && sudo apt-get install filebeat



sudo nano /etc/filebeat/filebeat.yml



