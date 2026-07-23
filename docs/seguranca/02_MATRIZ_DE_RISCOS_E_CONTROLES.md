# Matriz de riscos e controles

Baseline: `f2d20385ff180f016d12622c76554a3838532b74`. Total: **156** controles.

- P0: 77
- P1: 73
- P2: 6

A coluna de estado inicial não encerra controles técnicos. `PARCIAL` indica proteção existente
que ainda será endurecida ou revalidada na etapa responsável.

## GOV-001 — Registrar SHA-base de toda execução

- **Prioridade:** `P0`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Processo
- **Baseline:** Ausente como gate formal
- **Ação requerida:** Capturar branch, SHA, data, árvore suja/limpa e relação com prod antes de alterar qualquer arquivo.
- **Evidência mínima:** Relatório e manifesto mostram o SHA; patch é rejeitado se aplicado sobre base incompatível.

## GOV-002 — Tratar divergência dev/prod explicitamente

- **Prioridade:** `P0`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Processo
- **Baseline:** Branches divergentes
- **Ação requerida:** Não sincronizar, rebasear ou mesclar automaticamente; documentar diferenças relevantes e trabalhar apenas em dev.
- **Evidência mínima:** Relatório registra ahead/behind e confirma ausência de escrita em prod.

## GOV-003 — Manter fonte de verdade do hardening

- **Prioridade:** `P0`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Documentação
- **Baseline:** Ausente
- **Ação requerida:** Criar status rastreável por controle, etapa, responsável, evidência e risco residual.
- **Evidência mínima:** Todos os IDs da matriz aparecem no status e podem ser auditados entre chats.

## GOV-004 — Separar código, externo, extensão e híbrido

- **Prioridade:** `P0`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Governança
- **Baseline:** Parcial
- **Ação requerida:** Classificar cada correção para impedir implementação no repositório errado ou falsa conclusão.
- **Evidência mínima:** Nenhum item externo é marcado concluído apenas por documentação ou mock.

## GOV-005 — Preservar limites arquiteturais do template

- **Prioridade:** `P1`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Arquitetura
- **Baseline:** Documentado parcialmente
- **Ação requerida:** Não duplicar OAuth/OIDC da extensão e não introduzir regra de negócio específica.
- **Evidência mínima:** ADRs e revisão confirmam responsabilidades claras entre template, extensão e consumidor.

## GOV-006 — Definir política de risco residual

- **Prioridade:** `P1`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Governança
- **Baseline:** Ausente
- **Ação requerida:** Exigir justificativa, impacto, compensação, prazo e responsável para controles não implementados.
- **Evidência mínima:** Relatório final lista riscos aceitos sem usar expressões vagas.

## GOV-007 — Controlar mudanças de escopo

- **Prioridade:** `P1`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Processo
- **Baseline:** Ausente
- **Ação requerida:** Impedir correções cosméticas ou refactors amplos sem vínculo com controles da etapa.
- **Evidência mínima:** Manifesto mapeia cada arquivo alterado a IDs de controle.

## GOV-008 — Criar ADRs para decisões irreversíveis

- **Prioridade:** `P1`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Arquitetura
- **Baseline:** ADRs existentes
- **Ação requerida:** Registrar criptografia de sessão, key ring, autorização, lock, cloud Graph e publicação quando necessário.
- **Evidência mínima:** Cada decisão inclui contexto, alternativas, consequências e estratégia de migração.

## GOV-009 — Não reduzir gates existentes

- **Prioridade:** `P0`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Qualidade
- **Baseline:** 100% line/branch existente
- **Ação requerida:** Proibir redução de cobertura, remoção de testes, exclusões amplas ou scanners não bloqueantes sem ADR.
- **Evidência mínima:** Diff e CI provam manutenção ou fortalecimento dos gates.

## GOV-010 — Padronizar commit e ZIP por etapa

- **Prioridade:** `P1`
- **Etapa:** `SEC-00`
- **Responsabilidade:** `TEMPLATE_PROCESSO`
- **Estado inicial:** `CONCLUIDO`
- **Natureza:** Entrega
- **Baseline:** Ausente
- **Ação requerida:** Usar um commit sugerido por entrega e estrutura de ZIP definida neste pacote.
- **Evidência mínima:** Cada ZIP possui manifesto, relatório, validações, commit sugerido e somente arquivos de repositório na pasta própria.

## SC-001 — Fixar GitHub Actions por SHA completo

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** CI
- **Baseline:** Referências por tag principal
- **Ação requerida:** Substituir tags mutáveis por commits completos e comentar versão humana.
- **Evidência mínima:** Validador falha ao encontrar uses externo sem SHA de 40 caracteres.

## SC-002 — Aplicar permissões mínimas por job

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** CI
- **Baseline:** Permissões amplas em publicação
- **Ação requerida:** Definir permissions vazio no topo e conceder somente o necessário em cada job.
- **Evidência mínima:** Revisão confirma que jobs de teste não possuem contents/packages/id-token write.

## SC-003 — Separar checkout com credenciais de publicação

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** CI
- **Baseline:** Persistência padrão
- **Ação requerida:** Usar persist-credentials false fora de operações que realmente necessitem escrita.
- **Evidência mínima:** Workflow não deixa token reutilizável em jobs de build/teste.

## SC-004 — Criar lock reproduzível de runtime

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Dependências
- **Baseline:** Ranges amplos
- **Ação requerida:** Gerar lock/constraints com versões exatas e hashes, mantendo pyproject como intenção de compatibilidade.
- **Evidência mínima:** Instalação limpa resolve exatamente o conjunto auditado.

## SC-005 — Criar lock reproduzível de desenvolvimento

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Dependências
- **Baseline:** Ranges amplos
- **Ação requerida:** Fixar ferramentas de teste, build, lint, tipagem e segurança.
- **Evidência mínima:** CI e validação local usam o mesmo lock.

## SC-006 — Fixar backend de build e bootstrap

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Build
- **Baseline:** Range de hatchling e pip dinâmico
- **Ação requerida:** Controlar pip/setuptools/wheel/build/hatchling usados para construir.
- **Evidência mínima:** Build em ambiente limpo não baixa versões inesperadas fora do lock.

## SC-007 — Fixar versão validada da extensão

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Dependências
- **Baseline:** flask-ms-entra-auth >=1,<2
- **Ação requerida:** Usar versão exata/constraint auditada e processo explícito de atualização.
- **Evidência mínima:** Teste de contrato valida versão e comportamento, não apenas major.

## SC-008 — Fixar imagens por digest

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Contêiner
- **Baseline:** Tags mutáveis
- **Ação requerida:** Referenciar Python, Redis e imagens auxiliares por digest compatível com a plataforma.
- **Evidência mínima:** Scanner/validador detecta imagem sem digest.

## SC-009 — Construir uma vez e promover os mesmos bytes

- **Prioridade:** `P0`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Publicação
- **Baseline:** Build de teste e build multiarch separados
- **Ação requerida:** Produzir artefato/digest, testar e promover exatamente o mesmo objeto.
- **Evidência mínima:** Digest registrado no smoke test coincide com o digest candidato à publicação.

## SC-010 — Gerar SBOM

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Supply chain
- **Baseline:** Parcial/ausente
- **Ação requerida:** Gerar SBOM de pacote e imagem em formato padrão e armazenar como artifact.
- **Evidência mínima:** SBOM contém dependências diretas/transitivas e digest do artefato.

## SC-011 — Gerar provenance e attestation

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Supply chain
- **Baseline:** Parcial
- **Ação requerida:** Atestar origem, workflow, commit e digest sem conceder id-token a jobs desnecessários.
- **Evidência mínima:** Attestation pode ser verificada contra repositório e commit.

## SC-012 — Gerar checksums dos artefatos

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Build
- **Baseline:** Ausente
- **Ação requerida:** Produzir SHA-256 para wheel, sdist e materiais de entrega.
- **Evidência mínima:** Checksum é recalculável e referenciado no relatório.

## SC-013 — Adicionar dependency review em PR

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** CI
- **Baseline:** Ausente
- **Ação requerida:** Bloquear inclusão de dependências com política de severidade/licença definida.
- **Evidência mínima:** PR com dependência proibida falha antes do merge.

## SC-014 — Adicionar scanner de imagem

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Contêiner
- **Baseline:** Ausente
- **Ação requerida:** Escanear a imagem final por vulnerabilidades e configuração.
- **Evidência mínima:** Falha bloqueante acima do limiar documentado, com exceções rastreadas.

## SC-015 — Transformar .dockerignore em allowlist efetiva

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Contêiner
- **Baseline:** Denylist
- **Ação requerida:** Enviar ao build apenas arquivos necessários e impedir inclusão acidental de secrets/artifacts.
- **Evidência mínima:** Teste inspeciona o contexto e a imagem final.

## SC-016 — Endurecer runtime do Compose

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Contêiner
- **Baseline:** Parcial
- **Ação requerida:** Adicionar rede interna, limites de CPU/memória/PIDs, health, read-only, tmpfs e usuário adequado.
- **Evidência mínima:** Compose validado e containers executam sem capabilities extras.

## SC-017 — Proteger Redis local de referência

- **Prioridade:** `P1`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Contêiner
- **Baseline:** Sem ACL/TLS no Compose
- **Ação requerida:** Deixar claro que é desenvolvimento, reduzir exposição e adicionar autenticação quando compatível com o objetivo.
- **Evidência mínima:** Redis não publica porta, usa rede interna e não aceita acesso externo acidental.

## SC-018 — Criar política de atualização de digests/locks

- **Prioridade:** `P2`
- **Etapa:** `SEC-01`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Governança
- **Baseline:** Ausente
- **Ação requerida:** Definir cadência, validação e PRs separados para atualizações.
- **Evidência mínima:** Dependabot/Renovate não agrupa mudanças críticas sem visibilidade.

## CFG-001 — Separar segredos por finalidade

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** SECRET_KEY central
- **Ação requerida:** Usar chaves distintas para Flask, SID, payload de sessão, CSRF e outros materiais criptográficos.
- **Evidência mínima:** Teste impede reutilização acidental em produção.

## CFG-002 — Suportar key ring para rotação

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Configuração
- **Baseline:** Chave única
- **Ação requerida:** Aceitar chave ativa e chaves de verificação anteriores com ordem explícita.
- **Evidência mínima:** Rotação ocorre sem logout massivo não planejado e sem assinar com chave antiga.

## CFG-003 — Validar entropia e formato dos secrets

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** Validação principalmente por tamanho/placeholders
- **Ação requerida:** Exigir formato codificado, comprimento e diversidade adequados, rejeitando valores triviais.
- **Evidência mínima:** Casos fracos e placeholders falham no startup.

## CFG-004 — Ler secrets por arquivo/mount

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** Somente ambiente
- **Ação requerida:** Aceitar convenção *_FILE sem imprimir conteúdo.
- **Evidência mínima:** Container consome secret mount e não expõe valor em inspect/env.

## CFG-005 — Proibir DEBUG e TESTING em produção

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** TESTING validado; DEBUG precisa gate explícito
- **Ação requerida:** Falhar cedo quando flags inseguras estiverem ativas.
- **Evidência mínima:** Teste de produção cobre combinações conflitantes.

## CFG-006 — Validar APP_BASE_URL integralmente

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** Valida origem; path requer regra explícita
- **Ação requerida:** Definir política para path-base, barra, fragmento, userinfo, query e portas.
- **Evidência mínima:** URLs ambíguas ou com userinfo/backslash são rejeitadas.

## CFG-007 — Validar trusted hosts sem curingas perigosos

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Configuração
- **Baseline:** Lista existente
- **Ação requerida:** Normalizar IDNA, portas e proibir padrões excessivamente amplos.
- **Evidência mínima:** Host inválido não alcança aplicação.

## CFG-008 — Alinhar redirect URI ao contrato exato

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Configuração
- **Baseline:** Mesmo-origin e alias existentes
- **Ação requerida:** Manter comparação canônica, path estático e ausência de controles/query/fragment.
- **Evidência mínima:** Casos de parser diferencial possuem testes.

## CFG-009 — Validar opções Redis contra override por URI

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Configuração
- **Baseline:** Proteção existente
- **Ação requerida:** Preservar bloqueio de query params que enfraqueçam TLS, timeouts ou decode.
- **Evidência mínima:** Teste garante precedência da aplicação.

## CFG-010 — Definir limites máximos de configurações numéricas

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** Alguns limites amplos
- **Ação requerida:** Limitar proxy hops, TTL, workers, threads, timeouts, retries e payloads a faixas seguras.
- **Evidência mínima:** Valores extremos falham com mensagem sanitizada.

## CFG-011 — Padronizar ambientes aceitos

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** development/production
- **Ação requerida:** Usar enum explícito e postura segura para valor desconhecido.
- **Evidência mínima:** Ambiente inválido não herda defaults inseguros.

## CFG-012 — Impedir vazamento de configuração em erros

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Configuração
- **Baseline:** Mensagens sanitizadas em parte
- **Ação requerida:** Nunca incluir URI com credenciais, segredo ou token em exceções/logs.
- **Evidência mínima:** Testes capturam logs e verificam redaction.

## CFG-013 — Documentar secret manager e rotação

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Externo
- **Baseline:** Recomendação genérica
- **Ação requerida:** Definir procedimentos de geração, armazenamento, acesso, rotação e rollback.
- **Evidência mínima:** Checklist operacional possui evidência e responsável.

## CFG-014 — Manter compatibilidade sem fallback silencioso

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Configuração
- **Baseline:** Compatibilidade legada existente
- **Ação requerida:** Deprecar aliases com aviso seguro e prazo, sem aceitar configuração ambígua.
- **Evidência mínima:** Testes distinguem alias suportado de conflito fatal.

## ID-001 — Allowlist de clouds Microsoft

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Identidade
- **Baseline:** Graph base aceita HTTPS arbitrário
- **Ação requerida:** Mapear authority/tenant cloud para endpoint Graph oficial permitido.
- **Evidência mínima:** Endpoint fora da lista é rejeitado antes de criar o cliente.

## ID-002 — Impedir SSRF via Graph base URL

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** HTTP
- **Baseline:** HTTPS genérico
- **Ação requerida:** Proibir IPs, localhost, userinfo, portas inesperadas, redirects e hosts não Microsoft configurados.
- **Evidência mínima:** Testes cobrem IPv4, IPv6, IDNA, DNS rebinding conceitual e URLs malformadas.

## ID-003 — Desabilitar redirects no Graph

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** HTTP
- **Baseline:** Requests segue redirects por padrão
- **Ação requerida:** Usar allow_redirects false e tratar 3xx como erro controlado.
- **Evidência mínima:** Nenhum bearer token é reenviado a host de redirect.

## ID-004 — Desabilitar trust_env por padrão

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** HTTP
- **Baseline:** Requests Session herda ambiente
- **Ação requerida:** Definir trust_env false ou proxy explícito validado.
- **Evidência mínima:** HTTP_PROXY, HTTPS_PROXY e .netrc não alteram o destino/autorização em testes.

## ID-005 — Validar TLS sem opção de bypass em produção

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** HTTP
- **Baseline:** verify padrão
- **Ação requerida:** Manter verificação de certificado/hostname e permitir CA customizada por caminho seguro.
- **Evidência mínima:** Produção rejeita verify false e CA inexistente.

## ID-006 — Limitar corpo da resposta Graph

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** HTTP
- **Baseline:** response.json sem limite explícito
- **Ação requerida:** Ler streaming com limite e Content-Type esperado antes de parsear.
- **Evidência mínima:** Resposta grande ou tipo inesperado é abortada e sanitizada.

## ID-007 — Limitar campos do DTO Graph

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Dados
- **Baseline:** DTO existente
- **Ação requerida:** Definir tamanho e caracteres para id, displayName, mail e userPrincipalName.
- **Evidência mínima:** Campos excessivos ou inválidos não entram em sessão/log.

## ID-008 — Manter $select mínimo

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Privacidade
- **Baseline:** Implementado
- **Ação requerida:** Preservar conjunto mínimo e revisar qualquer expansão.
- **Evidência mínima:** Teste de URL impede remoção do filtro ou campos adicionais não aprovados.

## ID-009 — Controlar Retry-After

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Resiliência
- **Baseline:** respect_retry_after_header false
- **Ação requerida:** Aplicar backoff limitado e teto absoluto, sem dormir por valor arbitrário.
- **Evidência mínima:** Teste cobre 429/503, datas e valores extremos.

## ID-010 — Distinguir 401, 403, 429 e falha de rede

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Erros
- **Baseline:** Tratamento parcial
- **Ação requerida:** Mapear causas sem revelar token e sem converter tudo em 502 genérico.
- **Evidência mínima:** UX e logs mostram categoria segura e request ID.

## ID-011 — Implementar claims challenge/CAE

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `HIBRIDO_EXTENSAO`
- **Estado inicial:** `BLOQUEADO_EXTENSAO`
- **Natureza:** Identidade
- **Baseline:** Ausente
- **Ação requerida:** Propagar claims challenge para nova autenticação conforme contrato da extensão.
- **Evidência mínima:** Teste simula WWW-Authenticate com claims e evita loop.

## ID-012 — Evitar loop de reautenticação

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `HIBRIDO_EXTENSAO`
- **Estado inicial:** `BLOQUEADO_EXTENSAO`
- **Natureza:** Identidade
- **Baseline:** Risco potencial
- **Ação requerida:** Contabilizar tentativa/nonce e falhar de modo controlado após limite.
- **Evidência mínima:** Claims inválidos não causam redirect infinito.

## ID-013 — Preferir certificado ou identidade federada

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `HIBRIDO_EXTENSAO`
- **Estado inicial:** `BLOQUEADO_EXTENSAO`
- **Natureza:** Credencial
- **Baseline:** Client secret documentado
- **Ação requerida:** Preparar configuração e contrato para credencial assimétrica/federada em produção.
- **Evidência mínima:** Client secret pode ser proibido por política de produção quando suporte existir.

## ID-014 — Validar tenant e issuer esperados

- **Prioridade:** `P0`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Identidade
- **Baseline:** Single-tenant
- **Ação requerida:** Preservar validação single-tenant e rejeitar identidade fora do tenant configurado.
- **Evidência mínima:** Testes negativos cobrem issuer/tenant divergentes.

## ID-015 — User-Agent versionado e sem dados locais

- **Prioridade:** `P2`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** HTTP
- **Baseline:** Hardcoded 1.0
- **Ação requerida:** Derivar versão do pacote e não incluir hostname, usuário ou ambiente.
- **Evidência mínima:** Teste confirma formato previsível.

## ID-016 — Política de egress

- **Prioridade:** `P1`
- **Etapa:** `SEC-02`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Ausente
- **Ação requerida:** Documentar e testar destinos mínimos: Entra, Graph, Redis e dependências necessárias.
- **Evidência mínima:** Checklist externo registra regras de firewall/DNS/proxy.

## SES-001 — Autenticar payload Redis

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Sessão
- **Baseline:** SID assinado; payload sem MAC próprio
- **Ação requerida:** Aplicar AEAD/MAC ao payload antes de persistir.
- **Evidência mínima:** Alteração de um byte causa rejeição e limpeza segura.

## SES-002 — Criptografar payload conforme threat model

- **Prioridade:** `P1`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Sessão
- **Baseline:** Payload em claro no Redis
- **Ação requerida:** Usar criptografia autenticada quando confidencialidade no datastore for requisito.
- **Evidência mínima:** Dump Redis não revela tokens/cache/identidade em texto claro.

## SES-003 — Versionar envelope de sessão

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Sessão
- **Baseline:** TaggedJSON sem envelope formal
- **Ação requerida:** Persistir versão, key id, timestamps e payload autenticado.
- **Evidência mínima:** Migração/rejeição de versões desconhecidas é testada.

## SES-004 — Separar chave de SID e payload

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Criptografia
- **Baseline:** Derivação central
- **Ação requerida:** Não reutilizar material criptográfico entre assinatura do cookie e proteção do payload.
- **Evidência mínima:** Configuração e teste verificam separação.

## SES-005 — Rotação de chaves sem janela indefinida

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Criptografia
- **Baseline:** Chave única
- **Ação requerida:** Definir ativa, anteriores, prazo de retirada e regravação com chave atual.
- **Evidência mínima:** Sessão antiga é migrada ou expira conforme política.

## SES-006 — Timeout ocioso

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Sessão
- **Baseline:** TTL existe
- **Ação requerida:** Atualizar atividade de forma controlada e invalidar inatividade.
- **Evidência mínima:** Relógio simulado prova expiração ociosa.

## SES-007 — Timeout absoluto

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Sessão
- **Baseline:** Ausente
- **Ação requerida:** Persistir issued_at imutável e invalidar sessão após duração máxima.
- **Evidência mínima:** Refresh não estende o limite absoluto.

## SES-008 — Renovação periódica de SID

- **Prioridade:** `P1`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Sessão
- **Baseline:** Rotação após autenticação
- **Ação requerida:** Rotacionar em intervalos e eventos sensíveis sem tempestade de cookies.
- **Evidência mínima:** Teste prova SID novo e invalidação do anterior.

## SES-009 — Rotação atômica de SID

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Concorrência
- **Baseline:** Delete e troca separados
- **Ação requerida:** Usar operação Redis atômica/Lua/transação para mover/revogar estado.
- **Evidência mínima:** Requisições concorrentes não ressuscitam SID.

## SES-010 — Revogação por sessão

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Sessão
- **Baseline:** Logout local remove sessão atual
- **Ação requerida:** Garantir invalidade imediata do SID revogado.
- **Evidência mínima:** Reuso do cookie após logout falha.

## SES-011 — Revogação por usuário

- **Prioridade:** `P1`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Sessão
- **Baseline:** Ausente
- **Ação requerida:** Manter índice controlado ou versão de sessão por identidade.
- **Evidência mínima:** Desativação ou incidente invalida todas as sessões do usuário.

## SES-012 — Não recriar sessão removida em corrida

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Concorrência
- **Baseline:** NX/XX existente
- **Ação requerida:** Preservar e ampliar testes de concorrência para rotação/revogação.
- **Evidência mínima:** Teste determinístico cobre interleavings relevantes.

## SES-013 — Limitar payload por bytes antes e depois de proteção

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** DoS
- **Baseline:** 64 KiB existente
- **Ação requerida:** Aplicar limites ao JSON, envelope e ciphertext.
- **Evidência mínima:** Payload excessivo retorna erro sanitizado sem escrita parcial.

## SES-014 — Schema allowlist

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Desserialização
- **Baseline:** TaggedJSON genérico
- **Ação requerida:** Permitir apenas chaves e tipos esperados; rejeitar objetos inesperados.
- **Evidência mínima:** Fuzz/property tests não produzem tipos fora do contrato.

## SES-015 — Limpar payload corrompido com segurança

- **Prioridade:** `P1`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Resiliência
- **Baseline:** Descarte existente
- **Ação requerida:** Remover dado inválido sem apagar sessão nova criada por corrida.
- **Evidência mínima:** Teste cobre corrupção, falha de DEL e rotação simultânea.

## SES-016 — Política fail-closed/fail-safe para Redis

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Disponibilidade
- **Baseline:** 503 preserva resposta em falhas
- **Ação requerida:** Definir por operação quando negar acesso, preservar cookie ou limpar estado.
- **Evidência mínima:** Tabela de falhas e testes cobrem GET/SET/DEL/EVAL/timeout.

## SES-017 — Namespaces únicos por aplicação/ambiente

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Redis
- **Baseline:** Prefixo fixo
- **Ação requerida:** Incluir app/env e impedir colisão entre template, testes e outras aplicações.
- **Evidência mínima:** Chaves de dois ambientes não se sobrepõem.

## SES-018 — ACL de menor privilégio

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Redis
- **Baseline:** Responsabilidade externa
- **Ação requerida:** Criar usuários separados e limitar comandos/chaves necessários.
- **Evidência mínima:** ACL efetiva é testada ou registrada como pendência externa.

## SES-019 — Separar session store e auth storage

- **Prioridade:** `P1`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Redis
- **Baseline:** Mesmo Redis
- **Ação requerida:** Usar usuários/prefixos e, quando necessário, DB/instância separados.
- **Evidência mínima:** Comprometimento de uma credencial não concede acesso amplo ao outro namespace.

## SES-020 — TLS Redis obrigatório em produção

- **Prioridade:** `P0`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Redis
- **Baseline:** Implementado
- **Ação requerida:** Preservar cert validation e hostname check, suportando CA privada segura.
- **Evidência mínima:** Testes rejeitam rediss mal configurado e redis:// em produção.

## SES-021 — Backups sem secrets expostos

- **Prioridade:** `P1`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Operação
- **Baseline:** Externo
- **Ação requerida:** Definir criptografia, retenção, acesso e restore de Redis.
- **Evidência mínima:** Restore testado não reativa sessões que deveriam estar expiradas/revogadas.

## SES-022 — Clock skew controlado

- **Prioridade:** `P2`
- **Etapa:** `SEC-03`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Sessão
- **Baseline:** Não formalizado
- **Ação requerida:** Usar tempo UTC e tolerância mínima documentada para timestamps do envelope.
- **Evidência mínima:** Testes cobrem relógio avançado/atrasado.

## AUTH-001 — Inventário de rotas públicas

- **Prioridade:** `P0`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Autorização
- **Baseline:** Implícito
- **Ação requerida:** Declarar explicitamente login, callback, assets e health; todo o restante não é público por acidente.
- **Evidência mínima:** Teste falha quando nova rota não é classificada.

## AUTH-002 — Deny-by-default

- **Prioridade:** `P0`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Autorização
- **Baseline:** Ausente
- **Ação requerida:** Negar rotas protegidas sem política explícita.
- **Evidência mínima:** Rota nova protegida retorna 403 até receber regra.

## AUTH-003 — Separar autenticação de autorização

- **Prioridade:** `P0`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Arquitetura
- **Baseline:** Documentado
- **Ação requerida:** Manter extensão como autenticação e módulo local como decisão de acesso.
- **Evidência mínima:** Nenhum decorator depende de internals privados da extensão.

## AUTH-004 — Política de permissões abstrata

- **Prioridade:** `P1`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Arquitetura
- **Baseline:** Ausente
- **Ação requerida:** Definir interface para roles/grupos/permissions adaptável pelo consumidor.
- **Evidência mínima:** Exemplo funciona sem codificar domínio de negócio.

## AUTH-005 — Validar identidade local

- **Prioridade:** `P0`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Autorização
- **Baseline:** Registro demonstrativo
- **Ação requerida:** Exigir vínculo ativo e consistente com tenant/object ID.
- **Evidência mínima:** Usuário removido ou divergente perde acesso.

## AUTH-006 — Persistência transacional do vínculo

- **Prioridade:** `P1`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Dados
- **Baseline:** Memória limitada
- **Ação requerida:** Criar interface e implementação de referência segura, evitando estado apenas por processo.
- **Evidência mínima:** Múltiplos workers observam a mesma revogação.

## AUTH-007 — Evitar TOCTOU de permissão

- **Prioridade:** `P1`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Concorrência
- **Baseline:** Ausente
- **Ação requerida:** Definir consistência/cache e revalidação para ações sensíveis.
- **Evidência mínima:** Revogação concorrente é coberta em teste.

## AUTH-008 — Reautenticação para ações críticas

- **Prioridade:** `P2`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Autorização
- **Baseline:** Ausente
- **Ação requerida:** Disponibilizar política de auth freshness/step-up quando necessária.
- **Evidência mínima:** Ação marcada crítica rejeita sessão antiga.

## AUTH-009 — Auditar decisões negativas

- **Prioridade:** `P1`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Auditoria
- **Baseline:** Ausente
- **Ação requerida:** Registrar regra, resultado e identidade pseudonimizada, sem claims completas.
- **Evidência mínima:** Tentativas negadas geram evento correlacionável.

## AUTH-010 — Testar escalada horizontal

- **Prioridade:** `P0`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Teste
- **Baseline:** Ausente
- **Ação requerida:** Cobrir acesso a recurso de outro usuário/tenant lógico.
- **Evidência mínima:** Testes negativos falham antes de qualquer leitura/efeito.

## AUTH-011 — Testar escalada vertical

- **Prioridade:** `P0`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Teste
- **Baseline:** Ausente
- **Ação requerida:** Cobrir usuário comum tentando ação privilegiada.
- **Evidência mínima:** Resposta é 403 e não produz efeito lateral.

## AUTH-012 — Fallback seguro quando backend de autorização falha

- **Prioridade:** `P0`
- **Etapa:** `SEC-04`
- **Responsabilidade:** `HIBRIDO_CONSUMIDOR`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Resiliência
- **Baseline:** Ausente
- **Ação requerida:** Negar acesso em falha/timeout, com tratamento de disponibilidade documentado.
- **Evidência mínima:** Falha do repositório nunca concede acesso.

## WEB-001 — Sobrescrever headers obrigatórios

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** HTTP
- **Baseline:** Uso de setdefault
- **Ação requerida:** Definir valor final para CSP, nosniff, frame, referrer e políticas críticas.
- **Evidência mínima:** Blueprint/handler não consegue enfraquecer header por acidente.

## WEB-002 — CSP sem permissões desnecessárias

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Browser
- **Baseline:** CSP existente
- **Ação requerida:** Remover data: e fontes amplas quando não necessárias; usar nonce/hash para scripts futuros.
- **Evidência mínima:** Scanner/teste valida diretivas aprovadas.

## WEB-003 — CSP reporting

- **Prioridade:** `P2`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Browser
- **Baseline:** Ausente
- **Ação requerida:** Adicionar Report-Only em rollout e endpoint/coletor apropriado sem PII.
- **Evidência mínima:** Violações são observáveis sem quebrar produção inesperadamente.

## WEB-004 — HSTS somente com HTTPS confiável

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Proxy
- **Baseline:** Depende de request.is_secure
- **Ação requerida:** Validar proxy e emitir HSTS em produção apenas quando a origem externa for HTTPS comprovada.
- **Evidência mínima:** Teste com proxy real cobre acesso direto e forwarded headers.

## WEB-005 — Cookies __Host- e atributos seguros

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Cookie
- **Baseline:** Implementado em produção
- **Ação requerida:** Preservar Secure, HttpOnly, Path=/, sem Domain e SameSite conforme threat model.
- **Evidência mínima:** Inspeção de resposta confirma todos os atributos.

## WEB-006 — Reavaliar SameSite

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Cookie
- **Baseline:** Configuração existente
- **Ação requerida:** Documentar Lax/Strict/None e compatibilidade do callback.
- **Evidência mínima:** Testes reais de login/callback não reduzem CSRF.

## WEB-007 — Fetch Metadata

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** CSRF
- **Baseline:** Ausente
- **Ação requerida:** Bloquear requisições cross-site incompatíveis em métodos mutáveis, com exceções explícitas.
- **Evidência mínima:** Sec-Fetch-Site cross-site é rejeitado em endpoints sensíveis.

## WEB-008 — Origin/Referer para ações sensíveis

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** CSRF
- **Baseline:** CSRFProtect existente
- **Ação requerida:** Validar origem como defesa adicional onde navegador envia cabeçalhos.
- **Evidência mínima:** Origem divergente falha mesmo com cenário malformado.

## WEB-009 — Preservar CSRF em produção

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** CSRF
- **Baseline:** Implementado
- **Ação requerida:** Não permitir desativação e cobrir todos os métodos mutáveis.
- **Evidência mínima:** Teste de produção rejeita configuração sem CSRF.

## WEB-010 — Confiar apenas em proxies conhecidos

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Proxy
- **Baseline:** Hops configuráveis
- **Ação requerida:** Combinar número de hops com restrição de rede e documentação de topologia.
- **Evidência mínima:** Acesso direto não consegue forjar scheme/host/client IP.

## WEB-011 — Limitar hops de proxy

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Proxy
- **Baseline:** Máximo 5
- **Ação requerida:** Reduzir ao necessário e rejeitar combinação inconsistente.
- **Evidência mínima:** Configuração acima do contrato falha.

## WEB-012 — Limites de headers HTTP

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** DoS
- **Baseline:** Gunicorn sem limites explícitos suficientes
- **Ação requerida:** Definir quantidade/tamanho de campos e linha de requisição.
- **Evidência mínima:** Requisição excessiva é rejeitada antes da aplicação.

## WEB-013 — Limites de workers/threads/timeouts

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** DoS
- **Baseline:** Valores máximos muito altos
- **Ação requerida:** Aplicar faixas seguras e fail-fast.
- **Evidência mínima:** Valores extremos não iniciam o servidor.

## WEB-014 — Rate limit de autenticação

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Abuso
- **Baseline:** Ausente
- **Ação requerida:** Limitar início de login, callback inválido e reautenticação por IP/identidade com cuidado para NAT.
- **Evidência mínima:** Rajada controlada recebe 429 e gera métrica.

## WEB-015 — Rate limit de Graph/profile

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Abuso
- **Baseline:** Ausente
- **Ação requerida:** Evitar amplificação contra Graph e Redis.
- **Evidência mínima:** Requisições excessivas são limitadas sem vazar estado.

## WEB-016 — Rate limit de logout e endpoints mutáveis

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Abuso
- **Baseline:** Ausente
- **Ação requerida:** Aplicar política coerente sem impedir recuperação legítima.
- **Evidência mínima:** Testes cobrem janela, reset e concorrência.

## WEB-017 — Health checks mínimos

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Operação
- **Baseline:** Readiness faz round-trip a cada chamada
- **Ação requerida:** Manter resposta genérica, custo limitado e proteção de rede/rate limit.
- **Evidência mínima:** Health não expõe versão, topologia, exceção ou credencial.

## WEB-018 — Separar liveness de dependências

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Operação
- **Baseline:** Implementado
- **Ação requerida:** Preservar liveness local e readiness dependente.
- **Evidência mínima:** Falha Redis não reinicia processo saudável por liveness.

## WEB-019 — Assets com fingerprint e cache seguro

- **Prioridade:** `P2`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Frontend
- **Baseline:** Não formalizado
- **Ação requerida:** Usar hashes de conteúdo e cache imutável para assets, mantendo HTML no-store quando sensível.
- **Evidência mínima:** Alteração de asset muda URL/digest.

## WEB-020 — Respostas de erro uniformes

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Erros
- **Baseline:** Handlers sanitizados
- **Ação requerida:** Preservar headers semânticos e incluir request ID interno seguro.
- **Evidência mínima:** Nenhuma stacktrace ou detalhe de configuração chega ao cliente.

## OBS-001 — Redaction global por padrão

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Logs
- **Baseline:** Sanitização no logger da aplicação
- **Ação requerida:** Aplicar filtro a handlers/loggers relevantes e padrões de segredo.
- **Evidência mínima:** Testes injetam token, cookie, code, secret e Authorization em logs.

## OBS-002 — Sanitizar logs de bibliotecas

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Logs
- **Baseline:** Cobertura parcial
- **Ação requerida:** Configurar requests/urllib3/msal/redis/gunicorn sem debug sensível.
- **Evidência mínima:** Captura de log não contém headers ou URIs com credenciais.

## OBS-003 — Separar correlation ID externo e interno

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Observabilidade
- **Baseline:** X-Request-ID válido pode ser reutilizado
- **Ação requerida:** Preservar ID externo como campo e gerar ID interno confiável.
- **Evidência mínima:** Atacante não controla identificador primário de auditoria.

## OBS-004 — Auditoria persistente

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Auditoria
- **Baseline:** Logs apenas
- **Ação requerida:** Definir sink append-only/imutável para eventos críticos ou contrato de integração.
- **Evidência mínima:** Eventos sobrevivem a reinício e possuem retenção.

## OBS-005 — Minimização de dados em auditoria

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Privacidade
- **Baseline:** Allowlist existente
- **Ação requerida:** Registrar apenas IDs pseudonimizados, ação, resultado, tempo e correlação.
- **Evidência mínima:** Claims completas e PII desnecessária não aparecem.

## OBS-006 — Métricas de segurança

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Métricas
- **Baseline:** Ausente
- **Ação requerida:** Contabilizar falhas de login/callback, 401/403/429, corrupção de sessão, Redis e Graph.
- **Evidência mínima:** Métricas têm cardinalidade controlada.

## OBS-007 — Alertas acionáveis

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Operação
- **Baseline:** Ausente
- **Ação requerida:** Definir limiares, janela, severidade e runbook.
- **Evidência mínima:** Teste ou simulação prova roteamento do alerta.

## OBS-008 — Retenção e acesso a logs

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Externo
- **Baseline:** Ausente
- **Ação requerida:** Definir prazo, RBAC, criptografia, exportação e descarte.
- **Evidência mínima:** Checklist externo possui evidência.

## OBS-009 — Evitar capture_output irrestrito

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Gunicorn
- **Baseline:** capture_output true
- **Ação requerida:** Controlar stdout/stderr, filtros e formato para exceções de terceiros.
- **Evidência mínima:** Erro de biblioteca não vaza ambiente.

## OBS-010 — Segurança em modo texto e JSON

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Logs
- **Baseline:** Dois formatos
- **Ação requerida:** Aplicar a mesma allowlist, redaction e limites em ambos.
- **Evidência mínima:** Testes parametrizados cobrem os dois modos.

## OBS-011 — Limitar tamanho de mensagens

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** DoS
- **Baseline:** Limite existente
- **Ação requerida:** Preservar limite após formatação/serialização e evitar log injection.
- **Evidência mínima:** Quebras de linha e caracteres de controle são neutralizados.

## OBS-012 — Runbooks de incidentes

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Operação
- **Baseline:** Ausente
- **Ação requerida:** Criar procedimentos para secret leak, Redis compromise, token abuse, Graph outage e supply-chain.
- **Evidência mínima:** Cada alerta crítico aponta para runbook.

## TST-001 — Manter 100% linhas e branches

- **Prioridade:** `P0`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Teste
- **Baseline:** Implementado
- **Ação requerida:** Não reduzir gate; adicionar testes para código novo.
- **Evidência mínima:** pytest e coverage passam sem omit/exclude oportunista.

## TST-002 — Property-based testing de parsers

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Teste
- **Baseline:** Ausente
- **Ação requerida:** Testar URLs, hosts, headers, envelopes e configurações com geração de casos.
- **Evidência mínima:** Casos reduzidos são persistidos como regressão quando relevantes.

## TST-003 — Fuzz de desserialização de sessão

- **Prioridade:** `P0`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Teste
- **Baseline:** Ausente
- **Ação requerida:** Fuzzar envelope, ciphertext, JSON e tipos.
- **Evidência mínima:** Nenhum input causa execução, crash não controlado ou bypass.

## TST-004 — Testes reais de concorrência Redis

- **Prioridade:** `P0`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Teste
- **Baseline:** Redis real existente, concorrência parcial
- **Ação requerida:** Cobrir rotação, revogação, save/delete e falhas com múltiplas conexões.
- **Evidência mínima:** Interleavings críticos têm asserts determinísticos.

## TST-005 — DAST local

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Teste
- **Baseline:** Ausente
- **Ação requerida:** Executar scanner contra aplicação containerizada com configuração segura.
- **Evidência mínima:** Achados são tratados ou justificados.

## TST-006 — Teste com proxy reverso real

- **Prioridade:** `P0`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Teste
- **Baseline:** Ausente
- **Ação requerida:** Usar Nginx/Traefik/Caddy de teste para forwarded headers e acesso direto.
- **Evidência mínima:** Scheme, host, IP e HSTS se comportam conforme topologia.

## TST-007 — Teste Redis TLS

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Teste
- **Baseline:** Ausente/externo
- **Ação requerida:** Subir Redis TLS de teste ou executar em ambiente controlado.
- **Evidência mínima:** Certificado inválido/hostname incorreto falha.

## TST-008 — Teste Entra real controlado

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Teste
- **Baseline:** Doubles apenas
- **Ação requerida:** Executar smoke manual/automatizado em tenant de teste sem secrets em CI não confiável.
- **Evidência mínima:** Login, callback, CAE e logout local possuem evidência.

## TST-009 — Teste Graph real controlado

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Teste
- **Baseline:** Doubles
- **Ação requerida:** Validar /me e falhas reais em tenant de teste.
- **Evidência mínima:** Sem permissões além de User.Read.

## TST-010 — Teste de imagem AMD64

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PARCIAL`
- **Natureza:** Contêiner
- **Baseline:** Smoke existente
- **Ação requerida:** Executar imagem final pelo digest.
- **Evidência mínima:** Health e usuário não-root confirmados.

## TST-011 — Teste de imagem ARM64

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Contêiner
- **Baseline:** Build multiarch sem mesmo smoke
- **Ação requerida:** Executar em runner/emulação e registrar limitações.
- **Evidência mínima:** Imagem inicia e passa smoke básico.

## TST-012 — Reprodutibilidade de build

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Supply chain
- **Baseline:** Ausente
- **Ação requerida:** Comparar artefatos ou explicar campos não determinísticos.
- **Evidência mínima:** Hashes iguais ou diferenças justificadas e minimizadas.

## TST-013 — Secret scanning

- **Prioridade:** `P0`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** SAST
- **Baseline:** Ausente no gate local
- **Ação requerida:** Escanear histórico relevante e diff atual.
- **Evidência mínima:** Achado de segredo bloqueia entrega e exige rotação.

## TST-014 — SAST ampliado

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** SAST
- **Baseline:** Bandit apenas src/scripts
- **Ação requerida:** Adicionar Semgrep/CodeQL ou equivalente e revisar exclusões.
- **Evidência mínima:** Regras críticas são bloqueantes.

## TST-015 — actionlint e análise de workflows

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** CI
- **Baseline:** Ausente
- **Ação requerida:** Executar actionlint e zizmor ou equivalente.
- **Evidência mínima:** Workflows inválidos/perigosos falham.

## TST-016 — shellcheck e análise PowerShell

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Scripts
- **Baseline:** Ausente
- **Ação requerida:** Validar scripts shell e PowerShell com ferramentas apropriadas.
- **Evidência mínima:** Erros relevantes bloqueiam.

## TST-017 — hadolint e configuração de container

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Contêiner
- **Baseline:** Ausente
- **Ação requerida:** Lint Dockerfile/Compose e executar scanner de configuração.
- **Evidência mínima:** Exceções são localizadas e justificadas.

## TST-018 — Teste de carga e saturação

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Resiliência
- **Baseline:** Ausente
- **Ação requerida:** Medir login mock, profile, sessão e health sob limites controlados.
- **Evidência mínima:** Servidor degrada sem exaurir memória/conexões.

## TST-019 — Chaos de Redis e Graph

- **Prioridade:** `P1`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `HIBRIDO_EXTERNO`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Resiliência
- **Baseline:** Falhas unitárias
- **Ação requerida:** Injetar timeout, conexão fechada, resposta truncada e indisponibilidade.
- **Evidência mínima:** Comportamento segue a matriz fail-safe.

## TST-020 — Teste de artifact allowlist

- **Prioridade:** `P0`
- **Etapa:** `SEC-06`
- **Responsabilidade:** `TEMPLATE`
- **Estado inicial:** `PENDENTE`
- **Natureza:** Build
- **Baseline:** Inspeção por presença
- **Ação requerida:** Validar também ausência de arquivos proibidos e secrets.
- **Evidência mínima:** Wheel/sdist/imagem contêm somente allowlist aprovada.

## OPS-001 — Ruleset de proteção da branch dev

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Não verificável pelo código
- **Ação requerida:** Exigir PR/checks/review conforme fluxo desejado, sem impedir desenvolvimento controlado.
- **Evidência mínima:** Captura/export da configuração e teste de branch protegida.

## OPS-002 — Proteção de prod e tags

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Fora do foco imediato, mas necessário
- **Ação requerida:** Impedir push direto e alteração de tags/releases.
- **Evidência mínima:** Configuração registrada como pendente até a fase de release.

## OPS-003 — GitHub Actions allowlist

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Ausente
- **Ação requerida:** Permitir somente ações aprovadas e SHA-pinned.
- **Evidência mínima:** Política do repositório/conta registrada.

## OPS-004 — Private vulnerability reporting

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** A confirmar
- **Ação requerida:** Habilitar canal privado e alinhar SECURITY.md.
- **Evidência mínima:** Fluxo de teste/documentação confirma contato.

## OPS-005 — Code scanning e secret protection

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** A confirmar
- **Ação requerida:** Habilitar recursos disponíveis no GitHub e push protection.
- **Evidência mínima:** Configuração registrada com screenshot/export.

## OPS-006 — Redis de produção privado

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Responsabilidade do consumidor
- **Ação requerida:** Usar rede privada, TLS, ACL, backup e monitoramento.
- **Evidência mínima:** Checklist de deploy não permite endpoint público.

## OPS-007 — Firewall e egress mínimo

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Ausente
- **Ação requerida:** Restringir entrada ao proxy e saída aos serviços necessários.
- **Evidência mínima:** Teste de conectividade prova bloqueio do restante.

## OPS-008 — Secret manager e identidade de workload

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Recomendado
- **Ação requerida:** Fornecer segredos/credenciais sem arquivo versionado ou env permanente.
- **Evidência mínima:** Rotação e acesso possuem logs e menor privilégio.

## OPS-009 — WAF/reverse proxy e TLS

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Responsabilidade do consumidor
- **Ação requerida:** Configurar TLS moderno, limites, headers e acesso direto bloqueado.
- **Evidência mínima:** Scan TLS e teste de bypass do proxy.

## OPS-010 — Backup e restore

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Externo
- **Baseline:** Ausente
- **Ação requerida:** Testar restore de configuração/dados necessários sem reviver sessões indevidas.
- **Evidência mínima:** Evidência datada do exercício.

## OPS-011 — Rotação emergencial

- **Prioridade:** `P0`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Operação
- **Baseline:** Ausente
- **Ação requerida:** Definir passos para client secret/certificado, chaves de sessão, Redis e GitHub.
- **Evidência mínima:** Runbook inclui rollback e impacto esperado.

## OPS-012 — Inventário e retenção de dados

- **Prioridade:** `P1`
- **Etapa:** `SEC-05`
- **Responsabilidade:** `EXTERNO`
- **Estado inicial:** `BLOQUEADO_EXTERNO`
- **Natureza:** Privacidade
- **Baseline:** Ausente
- **Ação requerida:** Mapear cookies, sessão, token cache, identidade local, logs e artifacts.
- **Evidência mínima:** Cada dado tem finalidade, retenção, acesso e descarte.
