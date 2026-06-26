package com.wevops.emailindexer.controller;

import com.wevops.emailindexer.model.Email;
import com.wevops.emailindexer.service.EmailService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/emails")
@RequiredArgsConstructor
public class EmailController {

    private final EmailService emailService;

    @PostMapping
    public ResponseEntity<Email> create(@RequestBody Email email) {
        return ResponseEntity.ok(emailService.create(email));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Email> getById(@PathVariable String id) {
        Email email = emailService.getById(id);
        return email != null ? ResponseEntity.ok(email) : ResponseEntity.notFound().build();
    }

    @GetMapping
    public ResponseEntity<List<Email>> getAll() {
        return ResponseEntity.ok(emailService.getAll());
    }

    @PutMapping("/{id}")
    public ResponseEntity<Email> update(@PathVariable String id, @RequestBody Email email) {
        Email updated = emailService.update(id, email);
        return updated != null ? ResponseEntity.ok(updated) : ResponseEntity.notFound().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        emailService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
