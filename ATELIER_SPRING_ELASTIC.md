# 🎓 Atelier Pratique : Création d'un Indexeur d'Emails avec Spring Boot et Elasticsearch

Bienvenue dans ce guide d'atelier autonome (*self-paced lab*). L'objectif de cet atelier est de vous guider pas-à-pas dans la création du projet **Email Indexer**. À la fin de ce guide, vous aurez développé une API REST complète en Java (Spring Boot) capable d'ingérer un dataset JSON et d'interagir avec une stack Elasticsearch sécurisée via Docker.

---

## 🏗️ 1. Architecture du Projet

Avant de coder, comprenons comment les différentes briques communiquent entre elles.

### Diagramme d'Architecture (Infrastructure)

```mermaid
graph TD
    subgraph "Docker Host (VM/Local)"
        subgraph "Réseau Docker (docker_elk)"
            ES(fa:fa-database Elasticsearch<br/>es01:9200)
            KIB(fa:fa-chart-bar Kibana<br/>localhost:5601)
            API(fa:fa-cogs Spring Boot API<br/>email-indexer:8080)
        end
        
        DATA[fa:fa-file-code emails_dataset.json<br/>Volume monté]
        USER((fa:fa-user Utilisateur))
        
        API -->|1. Lit au démarrage| DATA
        API <-->|2. Indexe et Requete sur HTTPS 9200| ES
        KIB <-->|Visualisation| ES
        USER <-->|3. Appels HTTP CRUD sur Port 8080| API
        USER <-->|Consulte les Dashboards sur Port 5601| KIB
    end
    
    style ES fill:#00bfb3,stroke:#fff,stroke-width:2px,color:#000
    style KIB fill:#f04e98,stroke:#fff,stroke-width:2px,color:#fff
    style API fill:#6db33f,stroke:#fff,stroke-width:2px,color:#fff
```

### Architecture Interne Spring Boot

```mermaid
graph LR
    C[Controller<br/>EmailController] --> S[Service<br/>EmailService]
    S --> R[Repository<br/>EmailRepository]
    R --> ES[(Elasticsearch)]
    
    DS[DataSeeder<br/>Démarrage] --> S
    JSON[Fichier JSON] --> DS
```

---

## 🛠️ 2. Prérequis

Pour réaliser cet atelier, vous avez besoin de :
- **Java 17** d'installé (ou plus récent).
- **Docker** et **Docker Compose**.
- Le fichier `emails_dataset.json` placé dans un dossier `data` à la racine de votre environnement.
- Un éditeur de code (VS Code, IntelliJ IDEA).

---

## 🚀 3. Étapes de l'Atelier

### Étape 1 : Initialisation du Projet Spring Boot

La première étape consiste à générer la structure du projet Java. 
Allez sur [Spring Initializr (start.spring.io)](https://start.spring.io/) et configurez le projet ainsi :
- **Project** : Gradle - Groovy
- **Language** : Java 17
- **Spring Boot** : 3.3.0
- **Dependencies** : 
  - `Spring Web` (pour l'API REST)
  - `Spring Data Elasticsearch` (pour l'interaction avec ES)
  - `Lombok` (pour réduire le code boilerplate)

Une fois généré, décompressez le projet dans votre répertoire `email-indexer`.

> [!WARNING]
> Attention, le générateur inclut parfois des versions incompatibles entre Gradle 9.x et Spring Boot. Assurez-vous que votre fichier `gradle/wrapper/gradle-wrapper.properties` pointe vers `gradle-8.8-bin.zip`.

### Étape 2 : Configuration de la Connexion à Elasticsearch

Dans une architecture sécurisée (comme `docker_elk`), Elasticsearch utilise un certificat auto-signé HTTPS et une authentification. 
Nous devons configurer Spring Boot pour accepter cette connexion dans l'environnement de développement.

Créez une classe `ElasticConfig.java` dans le package `config` :

```java
package com.wevops.emailindexer.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.elasticsearch.client.ClientConfiguration;
import org.springframework.data.elasticsearch.client.elc.ElasticsearchConfiguration;
import org.springframework.beans.factory.annotation.Value;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

@Configuration
public class ElasticConfig extends ElasticsearchConfiguration {

    @Value("${spring.elasticsearch.uris:http://localhost:9200}")
    private String[] uris;

    @Value("${spring.elasticsearch.username:elastic}")
    private String username;

    @Value("${spring.elasticsearch.password:}")
    private String password;

    @Override
    public ClientConfiguration clientConfiguration() {
        String uri = uris[0].replace("https://", "").replace("http://", "");
        return ClientConfiguration.builder()
                .connectedTo(uri)
                .usingSsl(getTrustAllSslContext(), (s, session) -> true) // Ignore les erreurs SSL locales
                .withBasicAuth(username, password)
                .build();
    }

    private SSLContext getTrustAllSslContext() {
        // Implémentation générique d'un TrustManager qui accepte tout
        // (voir le code final pour l'implémentation complète)
    }
}
```

### Étape 3 : Création du Modèle de Données (Model)

Il s'agit de mapper la structure JSON vers une classe Java compréhensible par Elasticsearch.
Créez `Email.java` dans le package `model` :

```java
package com.wevops.emailindexer.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;
import java.util.List;

@Data
@Document(indexName = "emails")
public class Email {
    @Id
    private String id;

    @Field(type = FieldType.Text)
    private String subject;

    @Field(type = FieldType.Date, format = {}, pattern = "uuuu-MM-dd'T'HH:mm:ss.SSSSSS")
    private String date;

    // Ajouter body, sender, recipient, attachments, tags, etc.
}
```
> [!TIP]
> Notez l'importance du `pattern` sur le champ `date`. Elasticsearch doit savoir comment parser le format microsecondes spécifique de notre jeu de données.

### Étape 4 : Le Repository (Accès aux Données)

Spring Data simplifie l'accès à la base de données via une simple interface.
Créez `EmailRepository.java` dans le package `repository` :

```java
package com.wevops.emailindexer.repository;

import com.wevops.emailindexer.model.Email;
import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface EmailRepository extends ElasticsearchRepository<Email, String> {
    // Spring génère automatiquement save(), findById(), delete(), etc.
}
```

### Étape 5 : Logique Métier (Service) et API (Controller)

Créez `EmailService.java` pour isoler la logique métier, et `EmailController.java` pour exposer vos Endpoints.

**Exemple partiel du Controller :**
```java
@RestController
@RequestMapping("/api/emails")
@RequiredArgsConstructor
public class EmailController {
    private final EmailService emailService;

    @GetMapping
    public ResponseEntity<List<Email>> getAll() {
        return ResponseEntity.ok(emailService.getAll());
    }

    @PostMapping
    public ResponseEntity<Email> create(@RequestBody Email email) {
        return ResponseEntity.ok(emailService.create(email));
    }
}
```

### Étape 6 : Ingestion Initiale Automatique (DataSeeder)

L'objectif est que notre API lise notre gros fichier `emails_dataset.json` au démarrage.
Créez `DataSeeder.java` (qui implémente `CommandLineRunner`) :

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class DataSeeder implements CommandLineRunner {
    private final EmailService emailService;
    private final ObjectMapper objectMapper;

    @Override
    public void run(String... args) throws Exception {
        File file = new File("/data/emails_dataset.json");
        if (file.exists()) {
            List<Email> emails = objectMapper.readValue(file, new TypeReference<List<Email>>() {});
            emailService.createAll(emails);
            log.info("Chargement réussi : {} emails.", emails.size());
        }
    }
}
```

### Étape 7 : Conteneurisation (Docker)

Au lieu d'exiger Java sur le serveur de production, nous embarquons l'application dans une image Docker en deux étapes (Compilation + Exécution).

Créez le fichier `Dockerfile` :
```dockerfile
# Étape 1 : Compilation (JDK)
FROM eclipse-temurin:17-jdk-alpine AS build
WORKDIR /workspace/app
COPY . .
RUN chmod +x ./gradlew
RUN ./gradlew build -x test
RUN mkdir -p build/dependency && (cd build/dependency; jar -xf ../libs/*-SNAPSHOT.jar)

# Étape 2 : Exécution (JRE plus léger)
FROM eclipse-temurin:17-jre-alpine
VOLUME /tmp
ARG DEPENDENCY=/workspace/app/build/dependency
COPY --from=build ${DEPENDENCY}/BOOT-INF/lib /app/lib
COPY --from=build ${DEPENDENCY}/META-INF /app/META-INF
COPY --from=build ${DEPENDENCY}/BOOT-INF/classes /app
ENTRYPOINT ["java","-cp","app:app/lib/*","com.wevops.emailindexer.EmailIndexerApplication"]
```

### Étape 8 : Déploiement et Test avec Docker Compose

Intégrez l'application à votre stack existante (votre fichier `docker-compose.yml`) :

```yaml
  email-indexer:
    build: ./email-indexer
    environment:
      - ELASTICSEARCH_URIS=https://es01:9200
      - SPRING_ELASTICSEARCH_USERNAME=elastic
      - SPRING_ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
    volumes:
      - ../data:/data:ro
    ports:
      - "8080:8080"
    depends_on:
      es01:
        condition: service_healthy
```

> [!IMPORTANT]
> - `depends_on` avec `service_healthy` garantit que l'API ne démarre que quand Elasticsearch est complètement prêt et sécurisé.
> - Le volume mappé `../data:/data:ro` permet au DataSeeder de trouver le fichier `emails_dataset.json` local.

---

## 🎯 Validation Finale de l'Atelier

1. Construisez et lancez la stack : `docker compose up -d --build`
2. Regardez les logs : `docker compose logs -f email-indexer`
3. Exécutez une requête CRUD :
   ```bash
   curl -X GET http://localhost:8080/api/emails | jq
   ```
4. Connectez-vous sur **Kibana** (`http://localhost:5601`) et créez une *Data View* ciblant l'index `emails`. Vous pouvez maintenant visualiser toutes les données ingérées !

*Félicitations, vous avez mené à bien l'intégration complète d'une API Java / Elasticsearch dans un environnement Dockerisé sécurisé !*
