# Changelog

## 1.0.0

### Adicionado

- Application factory em estrutura `src`;
- Consumo estável de `flask-ms-entra-auth` 1.x;
- Sessão Redis server-side com SID opaco assinado;
- `RedisAuthStorage` com TTL e `take()` atômico por Lua;
- Vínculo local demonstrativo por hook;
- Cliente Microsoft Graph com DTO, `$select`, timeout, retries e erros sanitizados;
- Páginas acessíveis, CSRF, CSP e headers de segurança;
- Request ID, logs conservadores e health checks;
- Testes unitários, integração cruzada e cobertura integral;
- Docker multi-stage não-root, Redis e Gunicorn;
- CI para Python 3.11 a 3.14, Redis real, pacote e imagem;
- Dependabot para Python, GitHub Actions e Docker.

### Segurança

- Tokens, auth codes, state e claims completas permanecem fora de cookies e logs;
- Access log do Gunicorn omite query strings;
- Sessão gira o SID depois da autenticação;
- Cookies obsoletos são removidos após assinatura inválida, expiração ou payload corrompido;
- Configuração falha cedo em placeholders, portas inválidas, escopo insuficiente, HTTP externo e produção insegura;
- Storage e sessão compartilham Redis, mas usam namespaces independentes;
- Callback e identidade exigem consumo atômico distribuído;
- `ProxyFix` só é ativado por contagem explícita de proxies confiáveis;
- Imagem executa sem root e com filesystem read-only no Compose.
