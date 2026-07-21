# Microsoft Graph

O template chama somente `GET /me` e solicita `id`, `displayName`, `userPrincipalName` e `mail`.

O token é obtido pela extensão e nunca armazenado no modelo local ou enviado ao navegador. Sendo assim, o cliente possui:

- Timeouts separados de conexão e leitura;
- Pool HTTP reutilizável;
- Retries limitados apenas para `GET` em 429 e falhas 5xx transitórias;
- Respeito ao header `Retry-After`;
- `$select` restrito aos campos renderizados;
- Tradução de 401/403, 429, 5xx, JSON inválido e perfil incompleto para exceções sanitizadas.

Rotas não executam HTTP diretamente. Elas dependem de `GraphClient`, permitindo doubles sem rede nos testes. Respostas de erro exibem apenas mensagem segura e request ID.
