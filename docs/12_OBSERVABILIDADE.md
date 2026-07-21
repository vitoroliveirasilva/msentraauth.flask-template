# Observabilidade

Cada requisição recebe request ID seguro. Um valor válido de `X-Request-ID` pode ser propagado e entradas inválidas são substituídas.

Logs da aplicação usam mensagem constante e campos permitidos de método, endpoint, status e duração. Tokens, auth code, state, SID, claims e corpo Graph não entram nos logs. Em produção, `APP_LOG_FORMAT=json` facilita ingestão por plataformas de observabilidade.

O access log do Gunicorn não usa a linha de requisição completa e omite deliberadamente a query string.

- `/health/live`: confirma que o processo Flask responde;
- `/health/ready`: confirma que o Redis está acessível e que a aplicação pode sustentar sessão/autenticação.

Readiness não consulta Microsoft Entra ID nem Graph para evitar que uma indisponibilidade externa remova todas as instâncias saudáveis do balanceador.
