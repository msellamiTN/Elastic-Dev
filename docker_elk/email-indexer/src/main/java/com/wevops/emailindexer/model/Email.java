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

    @Field(type = FieldType.Text)
    private String body;

    @Field(type = FieldType.Keyword)
    private String sender;

    @Field(type = FieldType.Keyword)
    private String recipient;

    @Field(type = FieldType.Date, format = {}, pattern = "uuuu-MM-dd'T'HH:mm:ss.SSSSSS")
    private String date;

    @Field(type = FieldType.Nested)
    private List<Attachment> attachments;

    @Field(type = FieldType.Keyword)
    private List<String> tags;

    @Field(type = FieldType.Keyword, name = "attack_type")
    private String attackType;

    @Field(type = FieldType.Nested)
    private List<Ioc> ioc;

    @Data
    public static class Attachment {
        @Field(type = FieldType.Keyword)
        private String filename;

        @Field(type = FieldType.Keyword, name = "content_type")
        private String contentType;
    }

    @Data
    public static class Ioc {
        @Field(type = FieldType.Keyword)
        private String indicator;

        @Field(type = FieldType.Keyword)
        private String type;
    }
}
