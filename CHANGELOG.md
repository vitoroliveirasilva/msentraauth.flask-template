# Changelog

## Não lançado

### Segurança

- Segredos de Flask, assinatura do SID e CSRF passam a ser separados, com key ring e rotação compatível;
- Configurações sensíveis podem ser lidas por secret mounts via variáveis `_FILE`;
- Produção rejeita chaves criptográficas fracas ou reutilizadas, DEBUG, tenant genérico, URL-base com path e hosts curinga;
- O endpoint Graph fica restrito ao cloud global aprovado, sem redirects, proxy de ambiente ou `.netrc`;
- Respostas Graph são lidas por streaming com limites de corpo, tipo e campos do DTO;
- 401, 403, 429, 5xx, redirects e claims challenge possuem tratamento separado e sanitizado;
- `Retry-After` é interpretado com teto configurável e o User-Agent usa a versão instalada;
- O template detecta CAE sem loop automático e registra a dependência de evolução da extensão.
- GitHub Actions passam a usar SHAs completos, permissões mínimas e checkout sem credenciais persistidas;
- Python e Redis são referenciados por digests OCI validados;
- CI, Docker e scripts usam constraints diretas exatas, com procedimento para locks transitivos com hashes;
- A extensão de autenticação é fixada em `flask-ms-entra-auth==1.0.0`;
- O fluxo de publicação constrói uma única imagem multi-plataforma, testa o digest exato e promove os mesmos bytes;
- Pacotes e imagens recebem checksums, SBOM, provenance, attestations e scanner bloqueante;
- Dependency Review passa a bloquear dependências de severidade alta ou crítica;
- O contexto Docker usa allowlist e o Compose restringe rede, senha Redis, capabilities e recursos.


## 1.0.1 - 2026-07-22

### Corrigido

- Gravações de sessão usam condições Redis `NX` e `XX`, impedindo que uma requisição concorrente ressuscite um SID removido durante a rotação;
- Cookies com assinatura inválida ou payload corrompido são descartados mesmo quando `SESSION_REFRESH_EACH_REQUEST=false`;
- Falhas transitórias ou retornos inválidos de leitura no Redis preservam o cookie existente, bloqueiam somente rotas dependentes de sessão e retornam `503` com possibilidade de recuperação automática;
- Referências assinadas sem chave Redis não apagam o cookie, evitando que uma resposta concorrente com SID antigo remova o cookie recém-rotacionado;
- Rotas estáticas, liveness e readiness deixam de carregar ou persistir sessão, reduzindo latência e carga desnecessária no Redis;
- Falhas tardias de gravação ou exclusão substituem respostas de sucesso por `503` sanitizado, removem headers incompatíveis, preservam o cookie e impedem confirmação enganosa de login ou logout;
- Falhas de serialização e payloads acima do limite substituem a resposta por erro `500` sanitizado sem expor o conteúdo original;
- Visitas anônimas sem estado deixam de criar chaves Redis e cookies de sessão desnecessários;
- Leituras da sessão passam a emitir `Vary: Cookie`, evitando cache compartilhado incorreto de respostas personalizadas;
- Falhas condicionais ou retornos falsos do Redis interrompem a persistência em vez de serem tratados como sucesso;
- O readiness valida `PING` e um ciclo efêmero de gravação e consumo atômico, detectando Redis acessível porém sem as permissões exigidas;
- Produção rejeita explicitamente Redis sem TLS, modo de teste e CSRF desabilitado, inclusive quando `AppSettings` é construído diretamente;
- Timeouts não finitos, como `NaN` e infinito, são rejeitados durante a configuração;
- Retentativas do Microsoft Graph permanecem limitadas e erros inesperados do transporte deixam de ser mascarados como indisponibilidade externa;
- Logs textuais passam a manter contexto estruturado em linha única sem anexar mensagens sensíveis de exceções;
- O registro local demonstrativo possui limite de crescimento e descarte dos usuários autenticados há mais tempo;
- O vínculo local só é gravado depois que a rotação segura do SID é concluída;
- Parâmetros numéricos do Gunicorn são validados com limites seguros e mensagens de erro claras;
- Aliases de callback decodificam o caminho e rejeitam sintaxe dinâmica, excesso de tamanho ou formas ambíguas antes de registrar uma rota Flask;
- `APP_BASE_URL`, redirect URIs e `GRAPH_BASE_URL` rejeitam formas ambíguas, controles e queries incompatíveis; callbacks respeitam o limite e as restrições do Microsoft Entra;
- A documentação deixa de apresentar `/auth/logged-out` incorretamente como redirect URI do App Registration;
- A publicação exige tag pertencente ao histórico de `prod`, testa a imagem candidata antes do push e verifica o digest publicado;
- A CI valida o Compose, confirma o usuário não-root e executa smoke test real da imagem com Redis;
- Testes de distribuição deixam de depender da versão `1.0.0` codificada manualmente;
- A validação local em PowerShell passa a interromper no primeiro comando nativo com falha e ambos os scripts podem ser chamados fora da raiz do repositório;
- Respostas `405 Method Not Allowed` preservam o header `Allow` gerado pelo Werkzeug;
- A detecção de placeholders deixa de rejeitar valores legítimos que apenas contêm palavras de exemplo no meio do conteúdo;
- O registro direto de aliases de callback rejeita todos os caracteres de controle, independentemente da validação de settings;
- Parâmetros de query em `REDIS_URL` não podem sobrescrever o modo binário, os timeouts, o health check ou a verificação TLS controlados pela aplicação;
- O readiness tenta remover sua chave efêmera em todos os resultados, inclusive quando o consumo atômico retorna um valor inesperado;
- Os testes de readiness isolam corretamente o cenário em que o Redis recusa a exclusão da chave efêmera.

### Alterado

- A publicação deixa de manter uma versão fixa no formulário manual do workflow;
- Cada GitHub Release passa a receber `wheel` e `sdist` validados, sem publicar o template no PyPI;
- A imagem GHCR continua sendo publicada com tags semânticas, SBOM, proveniência, smoke test e verificação de digest.

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
