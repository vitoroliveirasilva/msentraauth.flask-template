# Status de implementação

## Implementado

- Application factory em estrutura `src`;
- Extensão `flask-ms-entra-auth` 1.x como único motor OAuth/OIDC;
- Sessão Redis com SID assinado, payload server-side, TTL e rotação após login;
- Persistência condicional com `NX`/`XX`, impedindo a recriação de SID removido por requisição concorrente;
- Descarte de cookie obsoleto após assinatura inválida, expiração ou payload corrompido, inclusive sem refresh por requisição;
- `RedisAuthStorage` com TTL e consumo atômico;
- Vínculo local demonstrativo por hook;
- Microsoft Graph `/me` com `$select`, timeouts, retries limitados e DTO;
- Interface Jinja, CSRF, CSP, trusted hosts e headers de segurança;
- Access log do Gunicorn sem query string do callback;
- Request ID, logs sanitizados e health checks;
- CI, testes, artefatos, Gunicorn, Docker e Compose;
- Documentação operacional e troubleshooting.

## Limites

O registro local em memória é demonstrativo, autorização de negócio não está incluída e a configuração real de Entra ID, Redis, proxy, secrets, monitoramento e deploy permanece responsabilidade do consumidor.
