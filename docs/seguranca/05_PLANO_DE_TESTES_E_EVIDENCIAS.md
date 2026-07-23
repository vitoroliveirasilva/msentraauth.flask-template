# Plano de testes e evidências do hardening

## Pirâmide

### Unitários

- parsing e validação de settings;
- canonicalização de URL/host;
- redaction;
- envelope de sessão;
- key ring;
- timeouts;
- autorização;
- mapeamento de erros Graph/Redis.

### Integração

- application factory;
- extensão e hooks;
- Redis real;
- Graph fake HTTP;
- proxy reverso;
- contêiner final;
- workflows e artifacts.

### Segurança especializada

- property-based testing;
- fuzz;
- DAST;
- SAST;
- secret scanning;
- dependency review;
- imagem/SBOM/provenance;
- carga e chaos.

## Matriz de casos críticos

| Área | Casos mínimos |
|---|---|
| Settings | placeholder, segredo fraco, produção insegura, URL parser diferencial, limites extremos |
| Graph | redirect, proxy env, `.netrc`, 3xx, 401, 403, 429, 5xx, body grande, JSON inválido, CAE |
| Sessão | assinatura inválida, payload adulterado, versão desconhecida, key rotation, idle/absolute timeout |
| Concorrência | rotate/save/delete/revoke simultâneos, falha Redis durante transação |
| Autorização | anônimo, autenticado sem vínculo, sem permissão, revogado, horizontal, vertical |
| Proxy | Host forjado, proto forjado, IP forjado, acesso direto, HSTS |
| DoS | headers, body, payload sessão, rate limit, health, Graph lento, Redis lento |
| Logs | Authorization, Cookie, code, token, secret, URI Redis, newline injection |
| Artefatos | allowlist, ausência de `.env`, chaves, caches, VCS, testes indevidos e metadados locais |

## Evidência mínima no relatório

Para cada comando:

- comando completo sem secret;
- diretório de execução;
- ambiente/Python;
- código de saída;
- resumo numérico;
- arquivo de saída relevante;
- motivo de qualquer teste não executado.

## Comandos

A implementação deve descobrir e respeitar os scripts oficiais do repositório. Quando existirem,
executar os scripts PowerShell e shell apropriados, além dos comandos especializados introduzidos
na etapa.

Não instalar ferramentas globalmente de forma silenciosa. Ferramentas novas devem estar no lock de
desenvolvimento ou em contêiner fixado por digest.

## Testes manuais controlados

Itens Entra, Graph real, secret manager, GitHub ruleset, Redis gerenciado e proxy de produção devem
ser marcados como `PARCIAL` ou `BLOQUEADO_EXTERNO` até receberem evidência do ambiente real.

## Validações da SEC-00

Executadas sobre os arquivos deste patch:

- estrutura obrigatória do ZIP;
- UTF-8;
- ausência de byte NUL;
- ausência de whitespace no fim das linhas;
- IDs de controle únicos;
- cobertura exata dos 156 controles no status;
- etapas e prioridades válidas;
- links relativos dos documentos novos;
- SHA-base presente no baseline e no status;
- somente Markdown modificado no repositório;
- busca local por padrões de secrets;
- hashes SHA-256 no manifesto.

Não executadas neste ambiente:

- `scripts/validate.sh`;
- `scripts/validate.ps1`;
- Ruff, mypy, pytest, Bandit e pip-audit;
- build, `twine check` e instalação do wheel;
- Redis real, Compose e Docker smoke.

Motivo: o ambiente não conseguiu resolver o host do GitHub para criar um checkout local completo.
A leitura e análise foram realizadas pelo conector do GitHub e o baseline permaneceu no SHA
`f2d20385ff180f016d12622c76554a3838532b74`. A aplicação do patch deve ser seguida pelo gate oficial na cópia local do usuário.
