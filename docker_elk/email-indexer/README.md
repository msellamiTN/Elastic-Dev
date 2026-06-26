# 📧 Email Indexer API

Bienvenue dans le projet **Email Indexer**, une application Java (Spring Boot) conçue pour s'interfacer avec Elasticsearch. Son rôle principal est d'ingérer automatiquement un jeu de données de courriels (emails) lors de son lancement et d'exposer une API REST permettant de manipuler ces données (opérations CRUD).

Ce composant s'intègre parfaitement avec la stack **docker_elk**, qui inclut un environnement complet Elasticsearch + Kibana sécurisé (HTTPS activé, authentification via mot de passe).

---

## 🏗️ Architecture du Projet

Le projet est basé sur **Spring Boot 3.3.0** et **Spring Data Elasticsearch**.

### Composants Principaux
1. **Model (`Email.java`)** : Définit la structure d'un courriel (sujet, expéditeur, date, pièces jointes, etc.) et le mapping Elasticsearch.
2. **Repository (`EmailRepository.java`)** : Hérite de `ElasticsearchRepository` pour fournir automatiquement toutes les requêtes basiques vers la base de données.
3. **Controller (`EmailController.java`)** : Expose l'API RESTful sur le port `8080` (Endpoints `/api/emails`).
4. **DataSeeder (`DataSeeder.java`)** : Un script de démarrage (`CommandLineRunner`) qui va chercher le fichier `emails_dataset.json` (monté via Docker) et l'injecte dans Elasticsearch si la base est vide.
5. **Configuration (`ElasticConfig.java`)** : Configure la connexion à Elasticsearch en acceptant les certificats auto-signés générés par l'environnement de développement `docker_elk`.

---

## 🚀 Guide Utilisateur : Installation et Démarrage

Le projet est conçu pour être lancé via **Docker Compose** dans la stack `docker_elk`.

### 1. Prérequis
- Avoir Docker et Docker Compose installés sur votre machine (ou VM).
- Avoir le jeu de données `emails_dataset.json` situé dans le dossier `../data/` (soit `Elastic-Dev/data/emails_dataset.json`).

### 2. Démarrage de l'Environnement
Dans le terminal de votre machine (ex: la VM Linux), placez-vous dans le répertoire `docker_elk` et lancez la commande suivante pour construire et démarrer les conteneurs :

```bash
sudo docker compose up -d --build
```

**Que va-t-il se passer ?**
1. Docker va démarrer `setup` pour générer les certificats SSL.
2. Le nœud `es01` (Elasticsearch) va démarrer.
3. Le conteneur `email-indexer` va compiler le code Java via Gradle (grâce au `Dockerfile` multi-stades) puis se lancer.
4. Au démarrage, `email-indexer` va se connecter à `es01`, parser le fichier `/data/emails_dataset.json` et envoyer les 3600+ courriels dans Elasticsearch.

### 3. Vérification des logs
Pour vérifier que l'indexation s'est bien passée :
```bash
sudo docker compose logs -f email-indexer
```
Vous devriez voir un message confirmant le chargement des emails : `Successfully loaded 3606 emails into Elasticsearch.`

---

## 📖 Guide de l'API (Endpoints CRUD)

Une fois l'application démarrée, l'API est accessible sur `http://localhost:8080/api/emails`. Vous pouvez utiliser `curl`, `Postman` ou votre navigateur web.

### 1. Lister tous les courriels (READ)
- **URL** : `GET http://localhost:8080/api/emails`
- **Description** : Renvoie la liste complète des emails indexés.
- **Test rapide avec Curl** :
  ```bash
  curl -X GET http://localhost:8080/api/emails
  ```

### 2. Récupérer un courriel spécifique (READ)
- **URL** : `GET http://localhost:8080/api/emails/{id}`
- **Description** : Renvoie le détail d'un email selon son identifiant généré par Elasticsearch.

### 3. Ajouter un nouveau courriel (CREATE)
- **URL** : `POST http://localhost:8080/api/emails`
- **Description** : Ajoute un nouvel email à l'index.
- **Exemple JSON (Body)** :
  ```json
  {
    "subject": "Alerte de Sécurité Interne",
    "body": "Veuillez mettre à jour vos mots de passe.",
    "sender": "admin@wevops.com",
    "recipient": "all@wevops.com",
    "date": "2024-05-10T10:00:00.000000",
    "attack_type": "Phishing",
    "tags": ["urgent", "security"]
  }
  ```
- **Test rapide avec Curl** :
  ```bash
  curl -X POST http://localhost:8080/api/emails \
       -H "Content-Type: application/json" \
       -d '{"subject": "Test", "sender": "test@test.com", "body": "Ceci est un test"}'
  ```

### 4. Mettre à jour un courriel (UPDATE)
- **URL** : `PUT http://localhost:8080/api/emails/{id}`
- **Description** : Remplace les informations de l'email existant.

### 5. Supprimer un courriel (DELETE)
- **URL** : `DELETE http://localhost:8080/api/emails/{id}`
- **Description** : Supprime l'email de la base Elasticsearch.
- **Test rapide avec Curl** :
  ```bash
  curl -X DELETE http://localhost:8080/api/emails/12345
  ```

---

## 🛠️ Dépannage (Troubleshooting)

- **Erreur : `Permission denied` sur gradlew** : Si Docker n'arrive pas à compiler le projet, assurez-vous que le fichier a les droits d'exécution. (Le Dockerfile inclut déjà un `chmod +x`, mais une vérification sous Linux ne fait jamais de mal).
- **Problème de Synchronisation Git** : Si vous développez sur Windows et exécutez sur une VM Linux, n'oubliez pas de `git add .`, `git commit` et `git push` vos modifications sur Windows, puis de faire un `git pull` sur la VM avant de relancer le `docker compose build`.
- **Accès à Kibana** : Vous pouvez visualiser vos données indexées en vous connectant à Kibana via `http://localhost:5601` (ou l'IP de votre VM), avec le nom d'utilisateur `elastic` et le mot de passe défini dans le fichier `.env` du répertoire `docker_elk`.
