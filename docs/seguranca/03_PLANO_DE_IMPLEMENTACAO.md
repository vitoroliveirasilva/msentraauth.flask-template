# Plano de implementação do hardening

## Regras transversais

- GitHub somente leitura durante a geração dos patches.
- Alterações exclusivamente locais e entrega em ZIP.
- Branch de referência `dev`, com SHA registrado.
- Nenhuma sincronização automática com `prod`.
- Uma etapa por entrega e um commit sugerido.
- Nenhuma tag, release, publicação ou deploy.
- Nenhuma mudança na extensão sem escopo explícito.
- Atualização obrigatória do status por ID de controle.
- Controles externos permanecem bloqueados até evidência real.

## Sequência

### SEC-00 — Contrato, baseline e governança executável

- **Dependência:** Nenhuma
- **Commit sugerido:** `docs(security): estabelece baseline e plano mestre de hardening`
- **Controles:** `GOV-001`, `GOV-002`, `GOV-003`, `GOV-004`, `GOV-005`, `GOV-006`, `GOV-007`, `GOV-008`, `GOV-009`, `GOV-010`

Escopo concluído por este patch: baseline, threat model, matriz, critérios, testes,
configurações externas, status e contrato de execução. Nenhum runtime foi alterado.

### SEC-01 — Supply chain, CI/CD, artefatos e contêineres reproduzíveis

- **Dependência:** SEC-00
- **Commit sugerido:** `build(security): torna supply chain e pipeline reproduziveis`
- **Controles:** `SC-001`, `SC-002`, `SC-003`, `SC-004`, `SC-005`, `SC-006`, `SC-007`, `SC-008`, `SC-009`, `SC-010`, `SC-011`, `SC-012`, `SC-013`, `SC-014`, `SC-015`, `SC-016`, `SC-017`, `SC-018`

- lock e hashes; pin de Actions e imagens; menor privilégio; build-once;
- SBOM, provenance, attestation, checksums, scanners e hardening do contêiner;
- nenhuma publicação durante o desenvolvimento em `dev`.

### SEC-02 — Configuração, segredos, Microsoft Entra ID e Microsoft Graph

- **Dependência:** SEC-01
- **Commit sugerido:** `feat(security): endurece configuracao Entra Graph e segredos`
- **Controles:** `CFG-001`, `CFG-002`, `CFG-003`, `CFG-004`, `CFG-005`, `CFG-006`, `CFG-007`, `CFG-008`, `CFG-009`, `CFG-010`, `CFG-011`, `CFG-012`, `CFG-013`, `CFG-014`, `ID-001`, `ID-002`, `ID-003`, `ID-004`, `ID-005`, `ID-006`, `ID-007`, `ID-008`, `ID-009`, `ID-010`, `ID-011`, `ID-012`, `ID-013`, `ID-014`, `ID-015`, `ID-016`

- separação e rotação de secrets; fail-fast de produção; allowlist de clouds;
- Graph sem redirect ou herança ambiental; limites, retries e claims challenge;
- certificado/federação tratados sem duplicar responsabilidade da extensão.

### SEC-03 — Redis, integridade criptográfica e ciclo de vida de sessão

- **Dependência:** SEC-02
- **Commit sugerido:** `feat(security): fortalece Redis e ciclo de vida das sessoes`
- **Controles:** `SES-001`, `SES-002`, `SES-003`, `SES-004`, `SES-005`, `SES-006`, `SES-007`, `SES-008`, `SES-009`, `SES-010`, `SES-011`, `SES-012`, `SES-013`, `SES-014`, `SES-015`, `SES-016`, `SES-017`, `SES-018`, `SES-019`, `SES-020`, `SES-021`, `SES-022`

- envelope autenticado/versionado; key ring; idle e absolute timeout;
- rotação atômica; revogação; schema allowlist; ACL e testes concorrentes.

### SEC-04 — Autorização deny-by-default e vínculo local seguro

- **Dependência:** SEC-03
- **Commit sugerido:** `feat(security): implementa autorizacao deny-by-default`
- **Controles:** `AUTH-001`, `AUTH-002`, `AUTH-003`, `AUTH-004`, `AUTH-005`, `AUTH-006`, `AUTH-007`, `AUTH-008`, `AUTH-009`, `AUTH-010`, `AUTH-011`, `AUTH-012`

- classificação de rotas; deny-by-default; política abstrata de permissões;
- vínculo local persistente por contrato; testes de escalada e fail-closed.

### SEC-05 — Borda HTTP, proxy, abuso, runtime, observabilidade e operação

- **Dependência:** SEC-04
- **Commit sugerido:** `feat(security): protege borda HTTP runtime e observabilidade`
- **Controles:** `WEB-001`, `WEB-002`, `WEB-003`, `WEB-004`, `WEB-005`, `WEB-006`, `WEB-007`, `WEB-008`, `WEB-009`, `WEB-010`, `WEB-011`, `WEB-012`, `WEB-013`, `WEB-014`, `WEB-015`, `WEB-016`, `WEB-017`, `WEB-018`, `WEB-019`, `WEB-020`, `OBS-001`, `OBS-002`, `OBS-003`, `OBS-004`, `OBS-005`, `OBS-006`, `OBS-007`, `OBS-008`, `OBS-009`, `OBS-010`, `OBS-011`, `OBS-012`, `OPS-001`, `OPS-002`, `OPS-003`, `OPS-004`, `OPS-005`, `OPS-006`, `OPS-007`, `OPS-008`, `OPS-009`, `OPS-010`, `OPS-011`, `OPS-012`

- headers finais, proxy confiável, limites HTTP/Gunicorn e rate limiting;
- health seguro, redaction global, métricas, auditoria e runbooks;
- itens de infraestrutura permanecem externos até prova.

### SEC-06 — Validação ofensiva, fechamento e evidências

- **Dependência:** SEC-00 a SEC-05
- **Commit sugerido:** `test(security): conclui validacao ofensiva e evidencias`
- **Controles:** `TST-001`, `TST-002`, `TST-003`, `TST-004`, `TST-005`, `TST-006`, `TST-007`, `TST-008`, `TST-009`, `TST-010`, `TST-011`, `TST-012`, `TST-013`, `TST-014`, `TST-015`, `TST-016`, `TST-017`, `TST-018`, `TST-019`, `TST-020`

- property tests, fuzz, DAST, concorrência, carga, chaos e ambientes reais;
- reprodutibilidade, artifact allowlist, scanners e encerramento dos riscos;
- sem release ou promoção para `prod`.

## Controle de mudança de escopo

Uma alteração fora da etapa só é aceita quando for indispensável para manter o repositório
executável, testável ou seguro. O relatório deve mapear o arquivo ao controle, justificar a
exceção e registrar impacto. Refactor cosmético não é exceção.

## Padrão de entrega

Cada ZIP deve conter `arquivos_repositorio/` e `_entrega/`, com manifesto, relatório,
validações, lista de arquivos, patch e commit sugerido. Somente `arquivos_repositorio/` deve ser
copiado para o repositório.
