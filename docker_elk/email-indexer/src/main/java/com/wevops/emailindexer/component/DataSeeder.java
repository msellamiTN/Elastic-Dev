package com.wevops.emailindexer.component;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.wevops.emailindexer.model.Email;
import com.wevops.emailindexer.service.EmailService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.io.File;
import java.util.List;

@Component
@RequiredArgsConstructor
@Slf4j
public class DataSeeder implements CommandLineRunner {

    private final EmailService emailService;
    private final ObjectMapper objectMapper;

    @Value("${app.dataset.path:/data/emails_dataset.json}")
    private String datasetPath;

    @Override
    public void run(String... args) throws Exception {
        log.info("Checking dataset at {}", datasetPath);
        File file = new File(datasetPath);
        if (file.exists()) {
            log.info("Dataset found. Loading data...");
            List<Email> emails = objectMapper.readValue(file, new TypeReference<List<Email>>() {});
            emailService.createAll(emails);
            log.info("Successfully loaded {} emails into Elasticsearch.", emails.size());
        } else {
            log.warn("Dataset not found at {}. Skipping initialization.", datasetPath);
        }
    }
}
