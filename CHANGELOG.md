# Changelog

## Não lançado

### Corrigido

- Gravações de sessão usam condições Redis `NX` e `XX`, impedindo que uma requisição concorrente ressuscite um SID removido durante a rotação;
- Cookies de sessão inválidos ou obsoletos são descartados mesmo quando `SESSION_REFRESH_EACH_REQUEST=false`;
- Falhas transitórias de leitura no Redis preservam o cookie existente, bloqueiam somente rotas dependentes de sessão e retornam `503` com possibilidade de recuperação automática;
- Visitas anônimas sem estado deixam de criar chaves Redis e cookies de sessão desnecessários;
- Leituras da sessão passam a emitir `Vary: Cookie`, evitando cache compartilhado incorreto de respostas personalizadas;
- Falhas condicionais ou retornos falsos do Redis interrompem a persistência em vez de serem tratados como sucesso;
- O readiness retorna indisponível quando `PING` produz uma resposta falsa, não apenas quando lança exceção;
- Produção rejeita explicitamente Redis sem TLS, modo de teste e CSRF desabilitado, inclusive quando `AppSettings` é construído diretamente;
- Timeouts não finitos, como `NaN` e infinito, são rejeitados durante a configuração;
- Retentativas do Microsoft Graph permanecem limitadas e erros inesperados do transporte deixam de ser mascarados como indisponibilidade externa;
- Logs textuais passam a manter contexto estruturado em linha única sem anexar mensagens sensíveis de exceções;
- O registro local demonstrativo possui limite de crescimento e descarte dos usuários autenticados há mais tempo;
- O vínculo local só é gravado depois que a rotação segura do SID é concluída;
- Parâmetros numéricos do Gunicorn são validados com limites seguros e mensagens de erro claras;
- Aliases de callback rejeitam caminhos dinâmicos, excessivos ou ambíguos antes de registrar uma rota Flask;
- Publicações manuais de contêiner exigem a branch `prod` ou a tag versionada e validam que o commit corresponde à tag;
- A CI valida o Compose, confirma o usuário não-root e executa smoke test real da imagem com Redis;
- Testes de distribuição deixam de depender da versão `1.0.0` codificada manualmente.

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
- Dependabot para Python, GitHub Actions e Docker;
- Alias seguro para callbacks legados definidos pelo App Registration, como `/getAToken`;
- Publicação versionada da imagem no GitHub Container Registry, com tags semânticas, SBOM, proveniência e smoke test com Redis.

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
