# Status do programa de hardening

- **Baseline SEC-01:** `18ee71ca8c7dbddd2fce06738c9ff974306a0861`
- **Data:** `2026-07-23`
- **Controles:** 156
- **SEC-00:** `PARCIAL` até execução do gate oficial em checkout local
- **SEC-01:** `PARCIAL` por ausência de gate completo e locks transitivos com hashes
- **Baseline SEC-02:** `5e4d24f3522b6105da3538948db8f21bbbb1c675`
- **SEC-02:** `PARCIAL` até execução integral da suíte e evolução dos contratos bloqueados
- **Baseline SEC-03:** `17187caa25bf4003e017e8532568d3d36c45df62`
- **SEC-03:** `PARCIAL` até suíte integral, Redis TLS real e controles externos terem evidência

## Resumo inicial

| Estado               | Quantidade |
| -------------------- | ---------: |
| `CONCLUIDO`          |         57 |
| `PARCIAL`            |         34 |
| `PENDENTE`           |         46 |
| `BLOQUEADO_EXTENSAO` |          3 |
| `BLOQUEADO_EXTERNO`  |         16 |
| `NAO_APLICAVEL`      |          0 |

## Etapas

| Etapa    | Estado     | Dependência     | Commit sugerido                                                   |
| -------- | ---------- | --------------- | ----------------------------------------------------------------- |
| `SEC-00` | `PARCIAL`  | Nenhuma         | `docs(security): estabelece baseline e plano mestre de hardening` |
| `SEC-01` | `PARCIAL`  | SEC-00          | `build(security): torna supply chain e pipeline reproduziveis`    |
| `SEC-02` | `PARCIAL`  | SEC-01          | `feat(security): endurece configuracao Entra Graph e segredos`    |
| `SEC-03` | `PARCIAL`  | SEC-02          | `feat(security): fortalece Redis e ciclo de vida das sessoes`     |
| `SEC-04` | `PENDENTE` | SEC-03          | `feat(security): implementa autorizacao deny-by-default`          |
| `SEC-05` | `PENDENTE` | SEC-04          | `feat(security): protege borda HTTP runtime e observabilidade`    |
| `SEC-06` | `PENDENTE` | SEC-00 a SEC-05 | `test(security): conclui validacao ofensiva e evidencias`         |

## Controles

| ID         | P    | Etapa    | Responsabilidade     | Estado               | Evidência/observação                                                          |
| ---------- | ---- | -------- | -------------------- | -------------------- | ----------------------------------------------------------------------------- |
| `GOV-001`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `00_BASELINE_E_ESCOPO.md` e manifesto do patch                                |
| `GOV-002`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `00_BASELINE_E_ESCOPO.md`                                                     |
| `GOV-003`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `README.md`, matriz e este status                                             |
| `GOV-004`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | campo Responsabilidade da matriz                                              |
| `GOV-005`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | baseline e fronteiras arquiteturais                                           |
| `GOV-006`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `04_CRITERIOS_DE_ACEITE.md`                                                   |
| `GOV-007`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `03_PLANO_DE_IMPLEMENTACAO.md`                                                |
| `GOV-008`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | política de ADR em `README.md`                                                |
| `GOV-009`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | gates em `04_CRITERIOS_DE_ACEITE.md`                                          |
| `GOV-010`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | padrão de entrega e manifesto deste patch                                     |
| `SC-001`   | `P0` | `SEC-01` | `TEMPLATE`           | `CONCLUIDO`          | Actions fixadas por SHA e validador allowlist                                 |
| `SC-002`   | `P0` | `SEC-01` | `TEMPLATE`           | `CONCLUIDO`          | `permissions: {}` e privilégios mínimos por job                               |
| `SC-003`   | `P0` | `SEC-01` | `TEMPLATE`           | `CONCLUIDO`          | checkout usa `persist-credentials: false`                                     |
| `SC-004`   | `P0` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | constraints diretas; lock transitivo com hashes pendente                      |
| `SC-005`   | `P0` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | constraints diretas; lock transitivo com hashes pendente                      |
| `SC-006`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | pins implementados; instalação completa não executada neste ambiente          |
| `SC-007`   | `P0` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | versão exata e teste atualizados; suíte completa pendente                     |
| `SC-008`   | `P0` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | digests fixados; pull/build das imagens pendente                              |
| `SC-009`   | `P0` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | workflow build-once implementado; promoção real não executada                 |
| `SC-010`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | SBOM configurado; artifact ainda não produzido                                |
| `SC-011`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | attestations configuradas; emissão real depende do GitHub                     |
| `SC-012`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | checksums configurados; build do pacote pendente                              |
| `SC-013`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | Dependency Review configurado; execução em PR pendente                        |
| `SC-014`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | Trivy bloqueante configurado; scanner não executado localmente                |
| `SC-015`   | `P1` | `SEC-01` | `TEMPLATE`           | `CONCLUIDO`          | `.dockerignore` deny-all com allowlist                                        |
| `SC-016`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | YAML validado; `docker compose config` e runtime pendentes                    |
| `SC-017`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | senha e rede interna configuradas; runtime Redis pendente                     |
| `SC-018`   | `P2` | `SEC-01` | `TEMPLATE`           | `CONCLUIDO`          | `08_SUPPLY_CHAIN.md` e Dependabot granular                                    |
| `CFG-001`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | chaves independentes em `AppSettings` e Flask config                          |
| `CFG-002`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | ring ordenado, chave ativa e reassinatura por chave anterior                  |
| `CFG-003`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | base64 URL-safe, 32 bytes, diversidade e independência                        |
| `CFG-004`  | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | suporte `_FILE` com arquivo absoluto, regular, UTF-8 e limitado               |
| `CFG-005`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | produção rejeita DEBUG, TESTING e CSRF desabilitado                           |
| `CFG-006`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | base URL canônica e restrita à origem                                         |
| `CFG-007`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | hosts exatos, sem curingas ou padrões por sufixo                              |
| `CFG-008`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | callback exato, sem query ou path ambíguo                                     |
| `CFG-009`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | proteção Redis existente preservada e retestada                               |
| `CFG-010`  | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | tetos para timeouts, TTL, retries, resposta e proxy                           |
| `CFG-011`  | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | enum explícito development/testing/production                                 |
| `CFG-012`  | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | erros não refletem secrets, URIs ou conteúdo de arquivos                      |
| `CFG-013`  | `P1` | `SEC-02` | `HIBRIDO_EXTERNO`    | `BLOQUEADO_EXTERNO`  | procedimento documentado; secret manager real exige plataforma                |
| `CFG-014`  | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | fallback somente em desenvolvimento/teste e conflitos falham                  |
| `ID-001`   | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | cloud global explicitamente allowlisted                                       |
| `ID-002`   | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | Graph arbitrário, IP, localhost e host alternativo rejeitados                 |
| `ID-003`   | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | `allow_redirects=False` e 3xx rejeitado                                       |
| `ID-004`   | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | `trust_env=False` e autenticação herdada desabilitada                         |
| `ID-005`   | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | TLS/hostname verification sem bypass configurável                             |
| `ID-006`   | `P0` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | streaming com limite de corpo e Content-Type JSON                             |
| `ID-007`   | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | limites de tipo, tamanho e controles no DTO                                   |
| `ID-008`   | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | `$select` mínimo preservado por teste                                         |
| `ID-009`   | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | Retry-After interpretado e limitado sem sleep arbitrário                      |
| `ID-010`   | `P1` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | 401, 403, 429, 5xx, 3xx e rede separados                                      |
| `ID-011`   | `P0` | `SEC-02` | `HIBRIDO_EXTENSAO`   | `BLOQUEADO_EXTENSAO` | challenge detectado/sanitizado; nova aquisição com claims depende da extensão |
| `ID-012`   | `P0` | `SEC-02` | `HIBRIDO_EXTENSAO`   | `BLOQUEADO_EXTENSAO` | template não redireciona automaticamente; fluxo completo depende da extensão  |
| `ID-013`   | `P1` | `SEC-02` | `HIBRIDO_EXTENSAO`   | `BLOQUEADO_EXTENSAO` | certificado ou federação não existem no contrato 1.0.0                        |
| `ID-014`   | `P0` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | tenant específico validado; validação de issuer pertence à extensão           |
| `ID-015`   | `P2` | `SEC-02` | `TEMPLATE`           | `CONCLUIDO`          | User-Agent deriva da versão instalada sem dados locais                        |
| `ID-016`   | `P1` | `SEC-02` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | destinos mínimos documentados; firewall/egress exige infraestrutura           |
| `SES-001`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | AES-256-GCM autentica o payload Redis; SID continua assinado                  |
| `SES-002`  | `P1` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | payload criptografado por chave AEAD própria                                  |
| `SES-003`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | envelope v1 com kid, nonce, timestamps e schema estrito                       |
| `SES-004`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | HKDF com domínio próprio e chave separada do SID/CSRF/Flask                   |
| `SES-005`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | ring ativo/anterior, rewrap automático e retirada documentada                 |
| `SES-006`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | idle autenticado, TTL limitado e refresh amortizado                           |
| `SES-007`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | timeout absoluto autenticado e cookie limitado                                |
| `SES-008`  | `P1` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | renovação periódica configurável e rotação pós-login                          |
| `SES-009`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | Lua compara, cria novo SID NX e remove antigo atomicamente                    |
| `SES-010`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | logout e API revoke_session removem SID atual                                 |
| `SES-011`  | `P1` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | revisão pseudônima persistente invalida todas as sessões do usuário           |
| `SES-012`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | NX/XX preservados e corrida de SID coberta por regressão                      |
| `SES-013`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | limites antes/depois de AEAD e campos/coleções limitados                      |
| `SES-014`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | allowlist para \_permanent, metadata da extensão e chaves declaradas          |
| `SES-015`  | `P1` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | compare-and-delete evita apagar valor concorrente                             |
| `SES-016`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | 500/503 sanitizados e fail-safe por operação                                  |
| `SES-017`  | `P0` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | namespace único gera prefixos session/auth/revocation                         |
| `SES-018`  | `P0` | `SEC-03` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | ACL Redis de menor privilégio exige infraestrutura real                       |
| `SES-019`  | `P1` | `SEC-03` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | prefixos e contrato separados; credenciais/instâncias físicas são externas    |
| `SES-020`  | `P0` | `SEC-03` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | rediss, hostname e CA privada suportados; teste TLS real indisponível         |
| `SES-021`  | `P1` | `SEC-03` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | backup/restauração sem segredos exige operação real                           |
| `SES-022`  | `P2` | `SEC-03` | `TEMPLATE`           | `CONCLUIDO`          | skew configurável limitado a 300 segundos e timestamps autenticados           |
| `AUTH-001` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Implícito                                                                     |
| `AUTH-002` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `AUTH-003` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Documentado                                                                   |
| `AUTH-004` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `AUTH-005` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PARCIAL`            | Registro demonstrativo                                                        |
| `AUTH-006` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Memória limitada                                                              |
| `AUTH-007` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `AUTH-008` | `P2` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `AUTH-009` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `AUTH-010` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `AUTH-011` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `AUTH-012` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                                                       |
| `WEB-001`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Uso de setdefault                                                             |
| `WEB-002`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | CSP existente                                                                 |
| `WEB-003`  | `P2` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `WEB-004`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Depende de request.is_secure                                                  |
| `WEB-005`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Implementado em produção                                                      |
| `WEB-006`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Configuração existente                                                        |
| `WEB-007`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `WEB-008`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | CSRFProtect existente                                                         |
| `WEB-009`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Implementado                                                                  |
| `WEB-010`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Hops configuráveis                                                            |
| `WEB-011`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Máximo 5                                                                      |
| `WEB-012`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Gunicorn sem limites explícitos suficientes                                   |
| `WEB-013`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Valores máximos muito altos                                                   |
| `WEB-014`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `WEB-015`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `WEB-016`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `WEB-017`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Readiness faz round-trip a cada chamada                                       |
| `WEB-018`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Implementado                                                                  |
| `WEB-019`  | `P2` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Não formalizado                                                               |
| `WEB-020`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Handlers sanitizados                                                          |
| `OBS-001`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Sanitização no logger da aplicação                                            |
| `OBS-002`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Cobertura parcial                                                             |
| `OBS-003`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | X-Request-ID válido pode ser reutilizado                                      |
| `OBS-004`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Logs apenas                                                                   |
| `OBS-005`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Allowlist existente                                                           |
| `OBS-006`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `OBS-007`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `OBS-008`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `OBS-009`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | capture_output true                                                           |
| `OBS-010`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Dois formatos                                                                 |
| `OBS-011`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Limite existente                                                              |
| `OBS-012`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `TST-001`  | `P0` | `SEC-06` | `TEMPLATE`           | `PARCIAL`            | Implementado                                                                  |
| `TST-002`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `TST-003`  | `P0` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `TST-004`  | `P0` | `SEC-06` | `TEMPLATE`           | `PARCIAL`            | Redis real existente, concorrência parcial                                    |
| `TST-005`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `TST-006`  | `P0` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `TST-007`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente/externo                                                               |
| `TST-008`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Doubles apenas                                                                |
| `TST-009`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Doubles                                                                       |
| `TST-010`  | `P1` | `SEC-06` | `TEMPLATE`           | `PARCIAL`            | Smoke existente                                                               |
| `TST-011`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Build multiarch sem mesmo smoke                                               |
| `TST-012`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `TST-013`  | `P0` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente no gate local                                                         |
| `TST-014`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Bandit apenas src/scripts                                                     |
| `TST-015`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `TST-016`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `TST-017`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                                                       |
| `TST-018`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                                                       |
| `TST-019`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Falhas unitárias                                                              |
| `TST-020`  | `P0` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Inspeção por presença                                                         |
| `OPS-001`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Não verificável pelo código                                                   |
| `OPS-002`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Fora do foco imediato, mas necessário                                         |
| `OPS-003`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                                                       |
| `OPS-004`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | A confirmar                                                                   |
| `OPS-005`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | A confirmar                                                                   |
| `OPS-006`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Responsabilidade do consumidor                                                |
| `OPS-007`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                                                       |
| `OPS-008`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Recomendado                                                                   |
| `OPS-009`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Responsabilidade do consumidor                                                |
| `OPS-010`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                                                       |
| `OPS-011`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                                                       |
| `OPS-012`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                                                       |

## Atualização obrigatória

Cada patch futuro deve alterar somente as linhas dos controles que realmente avançaram,
adicionar evidência objetiva e recalcular o resumo. Controles externos ou da extensão não podem
ser promovidos para `CONCLUIDO` com base apenas em código do template.
