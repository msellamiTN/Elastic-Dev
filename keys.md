# Setting up elasticsearch (8.14.0) ...
--------------------------- Security autoconfiguration information ------------------------------

Authentication and authorization are enabled.
TLS for the transport and HTTP layers is enabled and configured.

The generated password for the elastic built-in superuser is : avzBDMSed5MUlsUk2tKZ

If this node should join an existing cluster, you can reconfigure this with
'/usr/share/elasticsearch/bin/elasticsearch-reconfigure-node --enrollment-token <token-here>'
after creating an enrollment token on your existing cluster.

You can complete the following actions at any time:

Reset the password of the elastic built-in superuser with
'/usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic'.

Generate an enrollment token for Kibana instances with
 '/usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana'.
eyJ2ZXIiOiI4LjE0LjAiLCJhZHIiOlsiMTUyLjIyOC4yMzAuMjM4OjkyMDAiXSwiZmdyIjoiMzY2YWJjMGU5NWE2ZTBlMThmMzg5ZGI4NDBkM2Q2NTRlYjY2NmIyZDM2MGNjMGU5YmYxNzVlYWMwZTE5NWIzNCIsImtleSI6ImlFSHBfSThCT0hub1ZNWTFCRTJROmRnanh6MDNtVC0tS3VyS0pPSkQyV0EifQ==
Generate an enrollment token for Elasticsearch nodes with
'/usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s node'.

-------------------------------------------------------------------------------------------------
### NOT starting on installation, please execute the following statements to configure elasticsearch service to start automatically using systemd
 sudo systemctl daemon-reload
 sudo systemctl enable elasticsearch.service
### You can start elasticsearch service by executing
 sudo systemctl start elasticsearch.service
Scanning processes...
Scanning linux images...

sha256 Fingerprint=36:6A:BC:0E:95:A6:E0:E1:8F:38:9D:B8:40:D3:D6:54:EB:66:6B:2D:36:0C:C0:E9:BF:17:5E:AC:0E:19:5B:34
-----BEGIN CERTIFICATE-----
MIIFWTCCA0GgAwIBAgIUFN7jb+8dtn1GhLr1XrGHQlIDi08wDQYJKoZIhvcNAQEL
BQAwPDE6MDgGA1UEAxMxRWxhc3RpY3NlYXJjaCBzZWN1cml0eSBhdXRvLWNvbmZp
Z3VyYXRpb24gSFRUUCBDQTAeFw0yNDA2MDkxMDI3MjBaFw0yNzA2MDkxMDI3MjBa
MDwxOjA4BgNVBAMTMUVsYXN0aWNzZWFyY2ggc2VjdXJpdHkgYXV0by1jb25maWd1
cmF0aW9uIEhUVFAgQ0EwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDL
fIvo8IV4bpZ37WOfy5x7pq/KBPO++A3omE4xXK5QQk/SudJe+H/HHkshSFK06o28
Ef8g3nfGJCwYVs8Ej61mGBUuljED3RGAT3B0n31SbyZQXepp1S+jBQiKOzQmRgXm
aZhYd5bf5sqIfNSro79hbRBSwD+8qzVYHxqXwywBLuZY8HeVKjlWN7YfpRhT2Hqf
STV2g+yyvDY4fsHNk0iwRzSAeVbpixxI4zBjrTD4/nL9SxYUID9MPZzti/cLmIGd
3fHLeVU01COGA91jZweJ1dbCaGzvP15lp+ysc3ypyfFaQAZXiv1HNPKJH4KGqHUF
uW4gAh8vesS/JtLwQdmnMhtPLNyYgq19zdwf+OU9vkwa2Z2ZClw1bM73qpdzK9Ai
F8ZxK1MG7mxDFEN6H2CSQAI3RSbLBxCRGdq4NsrxZI382WZ1uazMLcOLnu64CgAd
OqA6MgS5h+5Lf9Xvh7KhiIfP9HlcIvDX8MFzht3yzlex8x+TQIEHd7pIk4Wyam/A
QHHKBMOFQdHv/UuxuVl6ccxFRaTHF5JtX7CA/kAmg241QsCuierQtwK5SMhj4/oL
/bsjGXH7X2QiUs7qtnz/1S1JPVWgF5pgNck1kGp7S5LR9J/hUbQmL4DsznIpAYYc
ubU2ItlSGVIaTzmdsT3pfGnVZ/Ss0maoqKMMWYKfvQIDAQABo1MwUTAdBgNVHQ4E
FgQU7FsDZx+H6rVm86TTs3DMVFZ+8bMwHwYDVR0jBBgwFoAU7FsDZx+H6rVm86TT
s3DMVFZ+8bMwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAgEACXs9
D0FegWmTqf5VYSAA1KG/316BNwZ+LTKsCgNq5BzKVEyFHJ/9sRHeMHjbuzsfZu4j
wtVW5WPpKRtiVWH+o7OCHtXvF6I6aY3iFlvGmeEDxaNfB8/3dyW9S4kkWblmvXvg
DjtkwtHZMoFi3lAyjD1YC3LG4H1q1sUg9EVXpNwIiZ7IOOCcei/4k2k7lAJwGIH3
16b1dJLMEtIBMfVG7dRD4dojiDZCU1C488jDyycCzoQRiBgEcybfrg3ZmV0SGpEI
QfS5vR0INSecd+/0W7Xk5xIqMNx5groWVK1Ib8+ULcq2oCFNDHBWpZownONaZxA3
++nwoSF3Dr7CTjbLWvEztL66dnoYY4I6ZJPx5sBPNQS0rybg+omIsegsxtXsWsOA
qPYhXP3cTXGW/HZ4e6gJdLl7yjB8U30tIlKyfSXJWka/GrxbayLFxlRTNx6HmBzX
ZGdbYGQrl7Tb/nP6JF6zLajquIuB15Jldg8OZ1n2CDb6Bq0Cg0PEAC2O1KaVKlcA
M0VvumGjU8OH1ZRhhO6KVAqrwjHqGSexsH3xY2B748ii2dGOgMCHR5r4Cy8QnHqM
rLYoth71p7MV/D+sVpzbmwBcoxu0e/15IEauv98VjHFGEkkj9I8lDY6Gbi9ZoTBY
V/BTPPtJP0x5wbrz1FQA7eFk8BZ8PdeWOk+t+xg=
-----END CERTIFICATE-----
