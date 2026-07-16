# Microsoft Graph

## Escopo inicial

Consultar `GET https://graph.microsoft.com/v1.0/me` com `User.Read` para exibir perfil.

## Campos

Usar `$select` para solicitar somente:

```text
id,displayName,givenName,surname,mail,userPrincipalName,jobTitle
```

## Cliente

O cliente Graph pertence ao template, não à extensão:

- Timeout de conexão e leitura;
- Redirects desabilitados quando apropriado;
- Status explícitos;
- JSON inválido tratado;
- DTO interno;
- Nenhum token em log;
- Request ID/correlation ID quando disponível.

## Status

| Status | Comportamento                                     |
| -----: | :------------------------------------------------ |
|    200 | Validar DTO                                       |
|    401 | Solicitar reautenticação                          |
|    403 | Erro de permissão                                 |
|    429 | Respeitar Retry-After e responder temporariamente |
|    5xx | Indisponibilidade temporária                      |
| outros | Erro externo controlado                           |

## Retry

Somente para GET idempotente e falhas transitórias com poucas tentativas. Nunca retry automático de `401` ou `403` e não bloquear worker por espera longa.

## Privacidade

Campos de perfil são dados pessoais. Exibir somente o necessário, não persistir sem finalidade e não usá-los como labels de métricas.
