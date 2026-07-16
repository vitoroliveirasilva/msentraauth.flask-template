# Observabilidade

## Objetivos

Diagnosticar autenticação, sessão e dependências sem coletar credenciais ou PII além do necessário.

## Logs

Formato estruturado com:

- Timestamp;
- Nível;
- Evento;
- Request ID;
- Rota;
- Status;
- Duração;
- Correlation ID externo.

## Eventos

- Login iniciado e concluído;
- Callback rejeitado;
- Reautenticação;
- Graph indisponível;
- Rate limit;
- Storage indisponível;
- Logout;
- Readiness.

## Métricas

- Sucesso e falha de login;
- Latência Graph;
- Status Graph;
- Refresh de token;
- `5xx`;
- Disponibilidade Redis;
- Duração de requests.

## Alertas

- Aumento de callback inválido;
- Redis indisponível;
- Graph 5xx elevado;
- Secret próximo de expirar;
- Auditoria de dependência falhando.

## Privacidade

Não usar email, object ID, token ou request ID como label de alta cardinalidade (definir retenção e acesso aos logs).
