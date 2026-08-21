# Segurança operacional

Produção falha no startup para configuração insegura: HTTPS, cookie Secure, CSRF, schema estrito e Redis TLS são obrigatórios. Use segredos independentes para `APP_SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `SESSION_SIGNING_KEYS`, `SESSION_PAYLOAD_KEYS` e credencial do Entra.

Não use `common`, `organizations` ou `consumers` como tenant. Não habilite `unsafe-inline`, `unsafe-eval` ou wildcard na CSP. Configure `ProxyFix` somente com a quantidade real de proxies confiáveis.

Rotacione key rings adicionando a chave nova na primeira posição, preservando temporariamente as anteriores até expirar o maior TTL. Trocar namespace, remover todas as chaves antigas ou revogar uma identidade invalida sessões existentes; planeje isso como mudança operacional.

O cookie contém apenas um SID opaco assinado. O conteúdo no Redis usa AEAD, schema e limites de tamanho, mas ainda deve ser tratado como dado sensível: restrinja rede/ACL, habilite TLS fora do host local e defina retenção e backup conforme a política da aplicação.
