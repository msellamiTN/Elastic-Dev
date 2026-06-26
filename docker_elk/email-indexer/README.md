# Email Indexer - Elasticsearch CRUD API

This project provides a Spring Boot application with a REST API to perform CRUD operations on Elasticsearch, automatically indexing an initial dataset of emails (`emails_dataset.json`).

## Features
- **Spring Boot 3 + Spring Data Elasticsearch**
- **Automatic Initialization**: On startup, it reads `/data/emails_dataset.json` and loads it into Elasticsearch if the file exists.
- **RESTful API**: Full CRUD operations for emails.
- **Dockerized**: Includes a Dockerfile and a standalone `docker-compose.yml` to spin up Elasticsearch and the API together.

## Requirements
- Docker and Docker Compose (if running via Docker)
- Java 17+ (if running locally without Docker)

## How to Run with Docker Compose

1. Make sure you have the `emails_dataset.json` in `../data/emails_dataset.json` relative to this project root.
2. Build and start the services:

```bash
docker-compose up -d --build
```

3. The application will wait for Elasticsearch to become healthy, then it will start and ingest the JSON data.

## API Endpoints (Base URL: `http://localhost:8080/api/emails`)

### 1. Get All Emails
- **URL**: `/`
- **Method**: `GET`
- **Response**: Array of email JSON objects.

### 2. Get Email by ID
- **URL**: `/{id}`
- **Method**: `GET`
- **Response**: Single email JSON object.

### 3. Create a New Email
- **URL**: `/`
- **Method**: `POST`
- **Body**:
```json
{
  "subject": "Example",
  "body": "Hello world",
  "sender": "sender@example.com",
  "recipient": "recipient@example.com",
  "date": "2024-05-04T17:06:43.319827",
  "attack_type": "Phishing"
}
```

### 4. Update an Email
- **URL**: `/{id}`
- **Method**: `PUT`
- **Body**: Same as Create.

### 5. Delete an Email
- **URL**: `/{id}`
- **Method**: `DELETE`

## Architecture Overview
- `model/Email.java`: Defines the document structure and Elasticsearch index mapping (`@Document(indexName = "emails")`).
- `repository/EmailRepository.java`: Extends `ElasticsearchRepository` for out-of-the-box CRUD operations.
- `service/EmailService.java`: Business logic layer.
- `controller/EmailController.java`: REST controller exposing endpoints.
- `component/DataSeeder.java`: Implementation of `CommandLineRunner` that reads the JSON dataset from disk using Jackson and indexes it via the repository on application start.
