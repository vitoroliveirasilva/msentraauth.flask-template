# Segurança

Relate vulnerabilidades de forma privada pelo recurso **Private vulnerability reporting** do
GitHub, quando habilitado. Não abra issue pública com client secret, auth code, access token,
refresh token, cookie, SID, cache, claims completas ou dados pessoais reais.

## Regras de produção

- HTTPS e `SESSION_COOKIE_SECURE=true`;
- `DEBUG=false`, `TESTING=false` e CSRF ativo;
- `APP_SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `SESSION_SIGNING_KEYS` e `SESSION_PAYLOAD_KEYS` independentes;
- chaves criptográficas base64 URL-safe que codifiquem pelo menos 32 bytes;
- secrets fornecidos por secret manager, preferencialmente via variáveis `_FILE`;
- rings do SID e do payload com a chave ativa primeiro e retirada controlada das anteriores;
- namespace único por aplicação e ambiente, timeout absoluto e revogação operacional testada;
- App Registration single-tenant, client ID UUID, tenant específico e redirect exata;
- `User.Read` como escopo mínimo;
- Microsoft Graph restrito a `https://graph.microsoft.com/v1.0` nesta versão;
- Redis privado, autenticado, com TLS, `REDIS_TLS_REQUIRED=true` e URI `rediss://`;
- proxy hops configurados somente quando a topologia é conhecida;
- logs sem payloads de Entra, Graph ou query string do callback;
- imagem executada como usuário não-root;
- dependências, Actions e imagens auditadas continuamente;
- branches e tags de produção protegidas;
- rotação periódica de credenciais e plano de revogação.

## Claims challenge e credenciais modernas

O template detecta claims challenge do Graph e evita loops, mas a reautenticação com `claims`,
certificado e workload identity dependem de suporte da extensão de autenticação. Não implemente
atalhos locais que dupliquem OAuth/OIDC ou aceitem endpoint Graph arbitrário.

## Limites

O registro local em memória é demonstrativo e não substitui banco transacional, autorização de
negócio, trilha de auditoria persistente ou governança de identidades. A SEC-03 implementa integridade, criptografia, timeout absoluto e revogação no template. ACL,
separação física, TLS real, backup e restauração do Redis continuam responsabilidades externas.
