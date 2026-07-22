# Observabilidade

Cada requisição recebe request ID seguro. Um valor válido de `X-Request-ID` pode ser propagado e entradas inválidas são substituídas.

Logs da aplicação usam mensagem limitada e campos permitidos de método, endpoint, status e duração. Os formatos JSON e texto carregam o mesmo contexto; o formato textual permanece em linha única e registra apenas o tipo da exceção, sem anexar mensagens ou tracebacks potencialmente sensíveis.

Tokens, auth code, state, SID, claims e corpo Graph não entram nos logs. Em produção, `APP_LOG_FORMAT=json` facilita ingestão por plataformas de observabilidade.
Erros inesperados do transporte Graph permanecem erros internos, em vez de serem classificados silenciosamente como indisponibilidade externa.

O access log do Gunicorn não usa a linha de requisição completa e omite deliberadamente a query string.

- `/health/live`: confirma que o processo Flask responde e permanece independente do Redis;
- `/health/ready`: confirma que o Redis responde a `PING`;
- Rotas dependentes de sessão retornam `503` com `Retry-After` quando a leitura da sessão falha, sem apagar o cookie existente.
- Sessões anônimas vazias não criam cookie nem chave Redis.

Readiness não consulta Microsoft Entra ID nem Graph para evitar que uma indisponibilidade externa remova todas as instâncias saudáveis do balanceador.
