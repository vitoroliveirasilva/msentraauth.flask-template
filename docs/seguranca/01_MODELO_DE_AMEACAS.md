# Modelo de ameaças do programa de segurança

## Objetivo

Proteger uma aplicação Flask de referência que autentica usuários por Microsoft Entra ID, mantém
estado de autenticação em Redis, consulta Microsoft Graph e é executada atrás de proxy/contêiner.

## Ativos

1. Credenciais da aplicação Entra.
2. Chaves de assinatura e criptografia.
3. SID de sessão no navegador.
4. Payload de sessão e token cache no Redis.
5. Estado/nonce/PKCE e dados transitórios OAuth/OIDC.
6. Access token delegado usado no Graph.
7. Identidade local e decisões de autorização.
8. Logs, auditoria, request IDs e métricas.
9. Artefatos Python e imagens de contêiner.
10. Workflows, tokens do GitHub e attestations.
11. Configuração de proxy, hosts, URLs e Redis.
12. Disponibilidade da aplicação, Redis e Graph.

## Fronteiras de confiança

- Navegador para proxy.
- Proxy para Gunicorn/Flask.
- Flask para a extensão.
- Flask para Redis.
- Flask para Microsoft Graph.
- Extensão/MSAL para Microsoft Entra ID.
- Runner de CI para registries e GitHub.
- Secret manager para runtime.
- Operador para arquivos de configuração.

## Agentes e capacidades

- Usuário anônimo enviando requests arbitrários.
- Usuário autenticado sem permissão.
- Usuário autenticado tentando acessar dados de outro usuário.
- Atacante com cookie/SID roubado.
- Atacante com acesso de leitura ou escrita parcial ao Redis.
- Dependência, action ou imagem comprometida.
- Proxy ou variável de ambiente mal configurada.
- Insider com acesso a logs/artifacts.
- Falha operacional que produz bypass por comportamento fail-open.
- Atacante tentando exaustão de workers, Redis, Graph ou armazenamento.

## Cenários prioritários

### T01: supply-chain compromise
Action/tag/imagem mutável é alterada e executa código no runner.

### T02: artifact substitution
O pipeline testa uma imagem e publica outra reconstruída.

### T03: Graph SSRF ou bearer forwarding
Base URL/redirect/proxy desvia chamada e recebe token delegado.

### T04: secret leakage
Segredo aparece em log, exception, environment, image layer ou artifact.

### T05: sessão adulterada
Atacante altera payload Redis ou explora desserialização permissiva.

### T06: replay/fixation
SID roubado permanece válido além do necessário ou é recriado por corrida.

### T07: revogação incompleta
Logout ou remoção de usuário não invalida outras sessões.

### T08: privilege escalation
Usuário autenticado acessa rota sem autorização explícita.

### T09: proxy spoofing
Atacante controla Host, scheme ou client IP por forwarded headers.

### T10: resource exhaustion
Headers, bodies, health, Graph, Redis ou logs exaurem recursos.

### T11: observability leakage
Biblioteca registra Authorization, query, token, secret ou claims.

### T12: fail-open
Falha de Redis, autorização ou configuração concede acesso.

## Regras de tratamento

- T01, T02, T03, T04, T05, T06, T08, T09 e T12 são P0.
- Confidencialidade do payload Redis deve ser decidida por ADR, mas integridade é obrigatória.
- Indisponibilidade não pode ser “resolvida” concedendo acesso.
- Controles externos precisam de evidência de plataforma.

## Mapeamento para etapas

| Cenário | Etapas principais |
|---|---|
| T01 supply chain | `SEC-01`, `SEC-06` |
| T02 substituição de artefato | `SEC-01`, `SEC-06` |
| T03 Graph SSRF/bearer forwarding | `SEC-02`, `SEC-06` |
| T04 vazamento de segredo | `SEC-01`, `SEC-02`, `SEC-05`, `SEC-06` |
| T05 sessão adulterada | `SEC-03`, `SEC-06` |
| T06 replay/fixation | `SEC-03`, `SEC-06` |
| T07 revogação incompleta | `SEC-03`, `SEC-04` |
| T08 escalada de privilégio | `SEC-04`, `SEC-06` |
| T09 proxy spoofing | `SEC-05`, `SEC-06` |
| T10 exaustão de recursos | `SEC-05`, `SEC-06` |
| T11 vazamento por observabilidade | `SEC-05`, `SEC-06` |
| T12 fail-open | `SEC-02`, `SEC-03`, `SEC-04`, `SEC-05` |

## Critério de atualização

O modelo deve ser atualizado quando uma etapa:

- adiciona ativo, integração ou fronteira de confiança;
- muda formato ou armazenamento de sessão;
- muda credencial, authority ou cloud;
- adiciona autorização;
- altera proxy, publicação ou telemetria;
- aceita risco residual novo.
