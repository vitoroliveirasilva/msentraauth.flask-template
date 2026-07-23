# Baseline, escopo e divergências

## Identificação do baseline

| Campo                     | Valor                                           |
| ------------------------- | ----------------------------------------------- |
| Repositório               | `vitoroliveirasilva/msentraauth.flask-template` |
| Branch de trabalho        | `dev`                                           |
| SHA analisado             | `f2d20385ff180f016d12622c76554a3838532b74`      |
| Commit observado          | `RELEASE - Prepara versão 1.0.1`                |
| Branch padrão             | `prod`                                          |
| SHA de `prod`             | `588c6455490a796b0f51c15559bd47209c0fbee2`      |
| Merge-base                | `f6751f4248265a66c0df3d703ad8c2180c15df52`      |
| Relação                   | divergente                                      |
| `dev` em relação a `prod` | 13 commits à frente e 4 atrás                   |
| Data da fotografia        | `2026-07-23`                                    |

O SHA acima é uma fotografia, não uma referência eterna. Toda etapa deve consultar novamente
`dev` e interromper a aplicação silenciosa de um patch quando a base tiver mudado.

A divergência entre branches é deliberadamente preservada nesta etapa. Não foi executado merge,
rebase, reset, cherry-pick, force-push ou alteração em `prod`.

## Escopo da SEC-00

A etapa cria apenas documentação e governança:

- fonte de verdade do hardening;
- modelo de ameaças;
- matriz de 156 controles;
- classificação de responsabilidade;
- plano de sete etapas;
- critérios de aceite;
- plano de testes;
- checklist externo;
- status inicial;
- contrato de execução e entrega.

Não altera código, dependências, configuração, workflows, Docker, sessão, Redis, Graph,
autenticação, autorização, headers ou comportamento HTTP.

## Fronteiras arquiteturais preservadas

1. A extensão `flask-ms-entra-auth` permanece o único motor OAuth/OIDC.
2. O template não duplica callback, `state`, token cache ou validação de identidade.
3. Microsoft Graph, sessão da aplicação, configuração, HTTP e operação pertencem ao template.
4. Regras de negócio, perfis finais e banco de usuários pertencem ao consumidor.
5. Infraestrutura real, secret manager, Redis gerenciado, proxy, WAF e GitHub settings exigem
   evidência externa.
6. Mudança na extensão exige escopo e repositório próprios.

## Controles já presentes que devem ser preservados

- application factory e estrutura `src`;
- sessão Redis server-side com SID assinado;
- TTL, limite de 64 KiB e rotação após autenticação;
- persistência condicional `NX` e `XX`;
- storage Redis de uso único;
- validação fail-fast de produção;
- Redis TLS obrigatório em produção;
- Graph `/me` com `$select` mínimo, timeout e retries limitados;
- Jinja, CSRF, CSP, trusted hosts e cookies defensivos;
- erros HTTP sanitizados;
- logs estruturados e access log sem query string;
- liveness separado de readiness;
- Docker multi-stage e usuário não-root;
- CI em Python 3.11 a 3.14;
- cobertura obrigatória de 100% de linhas e branches;
- job com Redis real, build de pacote e smoke da imagem.

Essas proteções são baseline. Elas não devem ser removidas para simplificar etapas futuras.

## Divergências e lacunas registradas

### D01 — maturidade declarada versus limites deliberados

O pacote é classificado como `Production/Stable`, enquanto a documentação define o projeto como
aplicação de referência e exclui autorização empresarial, banco transacional de usuários,
infraestrutura cloud e trilha persistente. A classificação deve ser reavaliada em etapa futura,
sem alteração nesta etapa.

### D02 — plano mestre antigo e programa de segurança

`docs/13_PLANO_MESTRE.md` possui etapas 00 a 08 concluídas. O Pacote Mestre de Segurança também
usa etapas 00 a 06. O namespace `SEC-00` a `SEC-06` evita falsos positivos de conclusão.

### D03 — dependências reproduzíveis

`pyproject.toml` declara intervalos para runtime, desenvolvimento e build. Não existe lock com
hashes que represente o conjunto efetivamente auditado.

### D04 — dependência da extensão

`flask-ms-entra-auth>=1.0,<2` aceita qualquer 1.x futura. O teste de contrato não deve se limitar
ao major quando a `SEC-01` fixar o conjunto validado.

### D05 — GitHub Actions mutáveis

Workflows usam referências como `actions/checkout@v7` e `actions/setup-python@v7`, não SHAs
completos. A correção pertence à `SEC-01`.

### D06 — imagens mutáveis

Python e Redis usam tags como `python:3.14-slim-bookworm` e `redis:8-alpine`. Digests e política
de atualização pertencem à `SEC-01`.

### D07 — candidato testado versus imagem publicada

O workflow testa uma candidata `linux/amd64` e depois executa novo build multiarch com push.
O digest publicado é inspecionado, mas os mesmos bytes não são promovidos a partir do candidato.
A estratégia build-once pertence à `SEC-01`.

### D08 — permissões de publicação

O workflow concede `contents: write` e `packages: write` no nível global do workflow e mantém
credenciais padrão do checkout. A separação por jobs e menor privilégio pertencem à `SEC-01`.

### D09 — credencial Entra

O contrato atual exige client secret. Certificado ou identidade federada em produção pode depender
da extensão e deve ser tratado como `HIBRIDO_EXTENSAO` na `SEC-02`.

### D10 — Graph endpoint amplo

`GRAPH_BASE_URL` exige HTTPS, mas não está restrito às clouds Microsoft compatíveis com a authority.
Isso mantém superfície de SSRF/configuração indevida.

### D11 — comportamento herdado de Requests

O transporte Graph não desabilita redirects nem `trust_env`. Proxy, `.netrc` e redirect precisam
de contrato explícito na `SEC-02`.

### D12 — limites de resposta Graph

O cliente chama `response.json()` sem limite próprio de corpo e não limita comprimentos dos campos
do perfil. A correção pertence à `SEC-02`.

### D13 — CAE e claims challenge

401 e 403 são agrupados como credencial rejeitada. Não existe contrato explícito de claims
challenge ou proteção contra loop de reautenticação.

### D14 — integridade do payload de sessão

O cookie protege o SID, mas o payload no Redis é TaggedJSON sem MAC ou AEAD próprio. Um agente com
escrita no datastore deve ser considerado no modelo de ameaças.

### D15 — ciclo de vida de sessão

Há TTL e refresh, mas não há timeout absoluto, renovação periódica de SID, key ring ou revogação
global por usuário.

### D16 — rotação não atômica

A rotação atual exclui a chave antiga e depois troca o SID em memória. A operação completa não é
atômica entre requisições concorrentes.

### D17 — autorização ausente

Autenticação não implica autorização. Não há deny-by-default, app roles, grupos, permissões ou
backend persistente de vínculo. A `SEC-04` deve fornecer contrato de referência sem criar regras
de negócio específicas.

### D18 — confiança de proxy

`ProxyFix` depende de contagem de hops configurável. A aplicação não consegue, sozinha, provar
que o acesso direto ao Gunicorn foi bloqueado.

### D19 — limites de runtime amplos

Gunicorn aceita até 1024 workers, 1024 threads e timeout de 3600 segundos. Limites de headers e
política de saturação ainda precisam ser explicitados.

### D20 — rate limiting

Não há rate limiting de login, callback, profile, logout ou readiness.

### D21 — headers com `setdefault`

Headers obrigatórios usam `setdefault`, permitindo que uma resposta anterior forneça valor mais
fraco. A política final pertence à `SEC-05`.

### D22 — HSTS e proxy

HSTS depende de `request.is_secure`; sua correção exige topologia de proxy validada e teste real.

### D23 — redaction de logs

Formatters limitam campos e mensagens, mas não aplicam redaction por padrões a mensagens arbitrárias
nem configuram globalmente loggers de bibliotecas.

### D24 — request ID

Um `X-Request-ID` válido fornecido pelo cliente torna-se o identificador principal. Auditoria deve
distinguir correlação externa de identificador interno confiável.

### D25 — observabilidade e auditoria

Não há trilha persistente, métricas de segurança, alertas, retenção ou runbooks executáveis.

### D26 — validação especializada

A cobertura é rigorosa, mas faltam property tests, fuzz, DAST, proxy real, Redis TLS, tenant Entra
controlado, Graph real, ARM64 executado, carga, chaos e prova de reprodutibilidade.

### D27 — configurações externas

Branch protection, tag protection, Actions allowlist, private vulnerability reporting, Entra,
Redis ACL, firewall, egress, secret manager, WAF, backup e restore não podem ser concluídos por
arquivos do repositório.

## Riscos de execução

- Aplicar patch sobre SHA diferente sem reanálise.
- Confundir `SEC-00` com a etapa 00 do plano funcional antigo.
- Corrigir a extensão dentro do template.
- Marcar configuração externa como concluída por haver documentação.
- reduzir testes, cobertura ou scanners para viabilizar uma etapa.
- misturar release/prod com o hardening da branch `dev`.
