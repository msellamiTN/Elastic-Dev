package com.wevops.emailindexer.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.elasticsearch.client.ClientConfiguration;
import org.springframework.data.elasticsearch.client.elc.ElasticsearchConfiguration;
import org.springframework.beans.factory.annotation.Value;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import java.security.cert.X509Certificate;

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
        String uri = uris.length > 0 ? uris[0].replace("http://", "").replace("https://", "") : "localhost:9200";

        return ClientConfiguration.builder()
                .connectedTo(uri)
                .usingSsl(getTrustAllSslContext(), (s, sslSession) -> true) // Disable SSL verification
                .withBasicAuth(username, password)
                .build();
    }

    private SSLContext getTrustAllSslContext() {
        try {
            TrustManager[] trustAllCerts = new TrustManager[]{
                    new X509TrustManager() {
                        public X509Certificate[] getAcceptedIssuers() { return null; }
                        public void checkClientTrusted(X509Certificate[] certs, String authType) {}
                        public void checkServerTrusted(X509Certificate[] certs, String authType) {}
                    }
            };

            SSLContext sc = SSLContext.getInstance("SSL");
            sc.init(null, trustAllCerts, new java.security.SecureRandom());
            return sc;
        } catch (Exception e) {
            throw new RuntimeException("Failed to create trust-all SSL context", e);
        }
    }
}
