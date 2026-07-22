# Status de implementação

## Implementado

- Application factory em estrutura `src`;
- Extensão `flask-ms-entra-auth` 1.x como único motor OAuth/OIDC;
- Sessão Redis com SID assinado, payload server-side, TTL e rotação após login;
- Persistência condicional com `NX`/`XX`, impedindo a recriação de SID removido por requisição concorrente;
- Descarte de cookie obsoleto após assinatura inválida, expiração ou payload corrompido, inclusive sem refresh por requisição;
- Preservação de sessão e resposta `503` durante falha transitória de leitura no Redis;
- Ausência de escrita Redis e cookie para sessões anônimas vazias;
- `Vary: Cookie` em respostas que consultam a sessão;
- `RedisAuthStorage` com TTL e consumo atômico;
- Vínculo local demonstrativo, thread-safe, limitado por capacidade e posterior à rotação bem-sucedida do SID;
- Microsoft Graph `/me` com `$select`, timeouts, retries estritamente limitados, DTO e separação entre falha de rede e erro interno;
- Configuração fail-fast também para instâncias de `AppSettings` injetadas diretamente;
- Produção exige Redis TLS, CSRF ativo e modo de teste desabilitado;
- Callback legado restrito a caminho estático, não-raiz e sem colisão;
- Interface Jinja, CSRF, CSP, trusted hosts e headers de segurança;
- Access log do Gunicorn sem query string do callback;
- Request ID e logs JSON/texto sanitizados com campos permitidos;
- Health checks com liveness independente e readiness do Redis;
- CI com Redis real, inspeção de artefatos e smoke test da imagem não-root;
- Publicação GHCR vinculada ao commit da tag versionada;
- Gunicorn, Docker e Compose com validações operacionais;
- Documentação operacional e troubleshooting.

## Limites

O registro local em memória é demonstrativo, autorização de negócio não está incluída e a configuração real de Entra ID, Redis, proxy, secrets, monitoramento e deploy permanece responsabilidade do consumidor.
