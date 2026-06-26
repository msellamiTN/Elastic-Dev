package com.wevops.emailindexer.service;

import com.wevops.emailindexer.model.Email;
import com.wevops.emailindexer.repository.EmailRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class EmailService {

    private final EmailRepository emailRepository;

    public Email create(Email email) {
        return emailRepository.save(email);
    }

    public Iterable<Email> createAll(List<Email> emails) {
        return emailRepository.saveAll(emails);
    }

    public Email getById(String id) {
        return emailRepository.findById(id).orElse(null);
    }

    public List<Email> getAll() {
        List<Email> emails = new ArrayList<>();
        emailRepository.findAll().forEach(emails::add);
        return emails;
    }

    public Email update(String id, Email email) {
        if (emailRepository.existsById(id)) {
            email.setId(id);
            return emailRepository.save(email);
        }
        return null;
    }

    public void delete(String id) {
        emailRepository.deleteById(id);
    }
}
