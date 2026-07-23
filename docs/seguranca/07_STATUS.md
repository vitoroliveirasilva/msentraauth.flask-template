# Status do programa de hardening

- **Baseline:** `f2d20385ff180f016d12622c76554a3838532b74`
- **Data:** `2026-07-23`
- **Controles:** 156
- **SEC-00:** `PARCIAL` até execução do gate oficial em checkout local

## Resumo inicial

| Estado               | Quantidade |
| -------------------- | ---------: |
| `CONCLUIDO`          |         10 |
| `PARCIAL`            |         40 |
| `PENDENTE`           |         88 |
| `BLOQUEADO_EXTENSAO` |          3 |
| `BLOQUEADO_EXTERNO`  |         15 |
| `NAO_APLICAVEL`      |          0 |

## Etapas

| Etapa    | Estado     | Dependência     | Commit sugerido                                                   |
| -------- | ---------- | --------------- | ----------------------------------------------------------------- |
| `SEC-00` | `PARCIAL`  | Nenhuma         | `docs(security): estabelece baseline e plano mestre de hardening` |
| `SEC-01` | `PENDENTE` | SEC-00          | `build(security): torna supply chain e pipeline reproduziveis`    |
| `SEC-02` | `PENDENTE` | SEC-01          | `feat(security): endurece configuracao Entra Graph e segredos`    |
| `SEC-03` | `PENDENTE` | SEC-02          | `feat(security): fortalece Redis e ciclo de vida das sessoes`     |
| `SEC-04` | `PENDENTE` | SEC-03          | `feat(security): implementa autorizacao deny-by-default`          |
| `SEC-05` | `PENDENTE` | SEC-04          | `feat(security): protege borda HTTP runtime e observabilidade`    |
| `SEC-06` | `PENDENTE` | SEC-00 a SEC-05 | `test(security): conclui validacao ofensiva e evidencias`         |

## Controles

| ID         | P    | Etapa    | Responsabilidade     | Estado               | Evidência/observação                              |
| ---------- | ---- | -------- | -------------------- | -------------------- | ------------------------------------------------- |
| `GOV-001`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `00_BASELINE_E_ESCOPO.md` e manifesto do patch    |
| `GOV-002`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `00_BASELINE_E_ESCOPO.md`                         |
| `GOV-003`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `README.md`, matriz e este status                 |
| `GOV-004`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | campo Responsabilidade da matriz                  |
| `GOV-005`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | baseline e fronteiras arquiteturais               |
| `GOV-006`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `04_CRITERIOS_DE_ACEITE.md`                       |
| `GOV-007`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | `03_PLANO_DE_IMPLEMENTACAO.md`                    |
| `GOV-008`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | política de ADR em `README.md`                    |
| `GOV-009`  | `P0` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | gates em `04_CRITERIOS_DE_ACEITE.md`              |
| `GOV-010`  | `P1` | `SEC-00` | `TEMPLATE_PROCESSO`  | `CONCLUIDO`          | padrão de entrega e manifesto deste patch         |
| `SC-001`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Referências por tag principal                     |
| `SC-002`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Permissões amplas em publicação                   |
| `SC-003`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Persistência padrão                               |
| `SC-004`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Ranges amplos                                     |
| `SC-005`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Ranges amplos                                     |
| `SC-006`   | `P1` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Range de hatchling e pip dinâmico                 |
| `SC-007`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | flask-ms-entra-auth >=1,<2                        |
| `SC-008`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Tags mutáveis                                     |
| `SC-009`   | `P0` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Build de teste e build multiarch separados        |
| `SC-010`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | Parcial/ausente                                   |
| `SC-011`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | Parcial                                           |
| `SC-012`   | `P1` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `SC-013`   | `P1` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `SC-014`   | `P1` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `SC-015`   | `P1` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Denylist                                          |
| `SC-016`   | `P1` | `SEC-01` | `TEMPLATE`           | `PARCIAL`            | Parcial                                           |
| `SC-017`   | `P1` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Sem ACL/TLS no Compose                            |
| `SC-018`   | `P2` | `SEC-01` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `CFG-001`  | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | SECRET_KEY central                                |
| `CFG-002`  | `P0` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Chave única                                       |
| `CFG-003`  | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Validação principalmente por tamanho/placeholders |
| `CFG-004`  | `P1` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Somente ambiente                                  |
| `CFG-005`  | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | TESTING validado; DEBUG precisa gate explícito    |
| `CFG-006`  | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Valida origem; path requer regra explícita        |
| `CFG-007`  | `P0` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Lista existente                                   |
| `CFG-008`  | `P0` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Mesmo-origin e alias existentes                   |
| `CFG-009`  | `P0` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Proteção existente                                |
| `CFG-010`  | `P1` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Alguns limites amplos                             |
| `CFG-011`  | `P1` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | development/production                            |
| `CFG-012`  | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Mensagens sanitizadas em parte                    |
| `CFG-013`  | `P1` | `SEC-02` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Recomendação genérica                             |
| `CFG-014`  | `P1` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Compatibilidade legada existente                  |
| `ID-001`   | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Graph base aceita HTTPS arbitrário                |
| `ID-002`   | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | HTTPS genérico                                    |
| `ID-003`   | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Requests segue redirects por padrão               |
| `ID-004`   | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Requests Session herda ambiente                   |
| `ID-005`   | `P0` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | verify padrão                                     |
| `ID-006`   | `P0` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | response.json sem limite explícito                |
| `ID-007`   | `P1` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | DTO existente                                     |
| `ID-008`   | `P1` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Implementado                                      |
| `ID-009`   | `P1` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | respect_retry_after_header false                  |
| `ID-010`   | `P1` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Tratamento parcial                                |
| `ID-011`   | `P0` | `SEC-02` | `HIBRIDO_EXTENSAO`   | `BLOQUEADO_EXTENSAO` | Ausente                                           |
| `ID-012`   | `P0` | `SEC-02` | `HIBRIDO_EXTENSAO`   | `BLOQUEADO_EXTENSAO` | Risco potencial                                   |
| `ID-013`   | `P1` | `SEC-02` | `HIBRIDO_EXTENSAO`   | `BLOQUEADO_EXTENSAO` | Client secret documentado                         |
| `ID-014`   | `P0` | `SEC-02` | `TEMPLATE`           | `PARCIAL`            | Single-tenant                                     |
| `ID-015`   | `P2` | `SEC-02` | `TEMPLATE`           | `PENDENTE`           | Hardcoded 1.0                                     |
| `ID-016`   | `P1` | `SEC-02` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                           |
| `SES-001`  | `P0` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | SID assinado; payload sem MAC próprio             |
| `SES-002`  | `P1` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | Payload em claro no Redis                         |
| `SES-003`  | `P0` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | TaggedJSON sem envelope formal                    |
| `SES-004`  | `P0` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | Derivação central                                 |
| `SES-005`  | `P0` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | Chave única                                       |
| `SES-006`  | `P0` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | TTL existe                                        |
| `SES-007`  | `P0` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `SES-008`  | `P1` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | Rotação após autenticação                         |
| `SES-009`  | `P0` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | Delete e troca separados                          |
| `SES-010`  | `P0` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | Logout local remove sessão atual                  |
| `SES-011`  | `P1` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `SES-012`  | `P0` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | NX/XX existente                                   |
| `SES-013`  | `P0` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | 64 KiB existente                                  |
| `SES-014`  | `P0` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | TaggedJSON genérico                               |
| `SES-015`  | `P1` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | Descarte existente                                |
| `SES-016`  | `P0` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | 503 preserva resposta em falhas                   |
| `SES-017`  | `P0` | `SEC-03` | `TEMPLATE`           | `PARCIAL`            | Prefixo fixo                                      |
| `SES-018`  | `P0` | `SEC-03` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Responsabilidade externa                          |
| `SES-019`  | `P1` | `SEC-03` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Mesmo Redis                                       |
| `SES-020`  | `P0` | `SEC-03` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Implementado                                      |
| `SES-021`  | `P1` | `SEC-03` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Externo                                           |
| `SES-022`  | `P2` | `SEC-03` | `TEMPLATE`           | `PENDENTE`           | Não formalizado                                   |
| `AUTH-001` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Implícito                                         |
| `AUTH-002` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `AUTH-003` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Documentado                                       |
| `AUTH-004` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `AUTH-005` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PARCIAL`            | Registro demonstrativo                            |
| `AUTH-006` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Memória limitada                                  |
| `AUTH-007` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `AUTH-008` | `P2` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `AUTH-009` | `P1` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `AUTH-010` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `AUTH-011` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `AUTH-012` | `P0` | `SEC-04` | `HIBRIDO_CONSUMIDOR` | `PENDENTE`           | Ausente                                           |
| `WEB-001`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Uso de setdefault                                 |
| `WEB-002`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | CSP existente                                     |
| `WEB-003`  | `P2` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `WEB-004`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Depende de request.is_secure                      |
| `WEB-005`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Implementado em produção                          |
| `WEB-006`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Configuração existente                            |
| `WEB-007`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `WEB-008`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | CSRFProtect existente                             |
| `WEB-009`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Implementado                                      |
| `WEB-010`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Hops configuráveis                                |
| `WEB-011`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Máximo 5                                          |
| `WEB-012`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Gunicorn sem limites explícitos suficientes       |
| `WEB-013`  | `P0` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Valores máximos muito altos                       |
| `WEB-014`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `WEB-015`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `WEB-016`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `WEB-017`  | `P0` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Readiness faz round-trip a cada chamada           |
| `WEB-018`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Implementado                                      |
| `WEB-019`  | `P2` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Não formalizado                                   |
| `WEB-020`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Handlers sanitizados                              |
| `OBS-001`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Sanitização no logger da aplicação                |
| `OBS-002`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Cobertura parcial                                 |
| `OBS-003`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | X-Request-ID válido pode ser reutilizado          |
| `OBS-004`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Logs apenas                                       |
| `OBS-005`  | `P0` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Allowlist existente                               |
| `OBS-006`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `OBS-007`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `OBS-008`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `OBS-009`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | capture_output true                               |
| `OBS-010`  | `P1` | `SEC-05` | `TEMPLATE`           | `PENDENTE`           | Dois formatos                                     |
| `OBS-011`  | `P1` | `SEC-05` | `TEMPLATE`           | `PARCIAL`            | Limite existente                                  |
| `OBS-012`  | `P1` | `SEC-05` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `TST-001`  | `P0` | `SEC-06` | `TEMPLATE`           | `PARCIAL`            | Implementado                                      |
| `TST-002`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `TST-003`  | `P0` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `TST-004`  | `P0` | `SEC-06` | `TEMPLATE`           | `PARCIAL`            | Redis real existente, concorrência parcial        |
| `TST-005`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `TST-006`  | `P0` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `TST-007`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente/externo                                   |
| `TST-008`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Doubles apenas                                    |
| `TST-009`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PARCIAL`            | Doubles                                           |
| `TST-010`  | `P1` | `SEC-06` | `TEMPLATE`           | `PARCIAL`            | Smoke existente                                   |
| `TST-011`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Build multiarch sem mesmo smoke                   |
| `TST-012`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `TST-013`  | `P0` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente no gate local                             |
| `TST-014`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Bandit apenas src/scripts                         |
| `TST-015`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `TST-016`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `TST-017`  | `P1` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Ausente                                           |
| `TST-018`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Ausente                                           |
| `TST-019`  | `P1` | `SEC-06` | `HIBRIDO_EXTERNO`    | `PENDENTE`           | Falhas unitárias                                  |
| `TST-020`  | `P0` | `SEC-06` | `TEMPLATE`           | `PENDENTE`           | Inspeção por presença                             |
| `OPS-001`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Não verificável pelo código                       |
| `OPS-002`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Fora do foco imediato, mas necessário             |
| `OPS-003`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                           |
| `OPS-004`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | A confirmar                                       |
| `OPS-005`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | A confirmar                                       |
| `OPS-006`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Responsabilidade do consumidor                    |
| `OPS-007`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                           |
| `OPS-008`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Recomendado                                       |
| `OPS-009`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Responsabilidade do consumidor                    |
| `OPS-010`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                           |
| `OPS-011`  | `P0` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                           |
| `OPS-012`  | `P1` | `SEC-05` | `EXTERNO`            | `BLOQUEADO_EXTERNO`  | Ausente                                           |

## Atualização obrigatória

Cada patch futuro deve alterar somente as linhas dos controles que realmente avançaram,
adicionar evidência objetiva e recalcular o resumo. Controles externos ou da extensão não podem
ser promovidos para `CONCLUIDO` com base apenas em código do template.
