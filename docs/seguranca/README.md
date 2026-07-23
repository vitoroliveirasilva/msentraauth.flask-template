# Programa de hardening de segurança

Este diretório é a fonte de verdade do programa de segurança do
`msentraauth.flask-template`.

## Identificação

- Repositório: `vitoroliveirasilva/msentraauth.flask-template`
- Branch de trabalho: `dev`
- Baseline da `SEC-00`: `f2d20385ff180f016d12622c76554a3838532b74`
- Baseline da `SEC-01`: `18ee71ca8c7dbddd2fce06738c9ff974306a0861`
- Baseline da `SEC-02`: `5e4d24f3522b6105da3538948db8f21bbbb1c675`
- Baseline da `SEC-03`: `17187caa25bf4003e017e8532568d3d36c45df62`
- Data do baseline: `2026-07-23`
- Pacote de origem: `Pacote Mestre de Segurança 1.0.0`
- Controles registrados: **156**

## Namespace das etapas

O repositório já possui um plano mestre funcional com etapas 00 a 08 concluídas em
`docs/13_PLANO_MESTRE.md`. Para evitar colisão, este programa usa o prefixo `SEC`:

| Pacote Mestre | Identificador no repositório | Escopo                                              |
| ------------- | ---------------------------- | --------------------------------------------------- |
| ETAPA-00      | `SEC-00`                     | Contrato, baseline e governança executável          |
| ETAPA-01      | `SEC-01`                     | Supply chain, CI/CD, artefatos e contêineres        |
| ETAPA-02      | `SEC-02`                     | Configuração, segredos, Entra ID e Graph            |
| ETAPA-03      | `SEC-03`                     | Redis, integridade e ciclo de vida de sessão        |
| ETAPA-04      | `SEC-04`                     | Autorização deny-by-default e vínculo local         |
| ETAPA-05      | `SEC-05`                     | Borda HTTP, proxy, abuso, runtime e observabilidade |
| ETAPA-06      | `SEC-06`                     | Validação ofensiva, fechamento e evidências         |

## Documentos

1. [Baseline, escopo e divergências](00_BASELINE_E_ESCOPO.md)
2. [Modelo de ameaças](01_MODELO_DE_AMEACAS.md)
3. [Matriz de riscos e controles](02_MATRIZ_DE_RISCOS_E_CONTROLES.md)
4. [Plano de implementação](03_PLANO_DE_IMPLEMENTACAO.md)
5. [Critérios de aceite](04_CRITERIOS_DE_ACEITE.md)
6. [Plano de testes e evidências](05_PLANO_DE_TESTES_E_EVIDENCIAS.md)
7. [Configurações externas](06_CHECKLIST_CONFIGURACOES_EXTERNAS.md)
8. [Status rastreável](07_STATUS.md)
9. [Supply chain e artefatos](08_SUPPLY_CHAIN.md)
10. [Configuração, Entra ID e Graph](09_CONFIGURACAO_ENTRA_GRAPH.md)
11. [Sessão Redis, integridade e ciclo de vida](10_SESSAO_REDIS.md)

## Estados permitidos

- `CONCLUIDO`: implementação ou processo verificado com evidência.
- `PARCIAL`: já existe proteção, mas o controle ainda exige endurecimento ou revalidação.
- `PENDENTE`: não iniciado pelo programa.
- `BLOQUEADO_EXTENSAO`: depende de contrato ou alteração na extensão.
- `BLOQUEADO_EXTERNO`: depende de GitHub, Entra, Redis, proxy, cloud ou operação.
- `NAO_APLICAVEL`: decisão justificada e aprovada.

Documentação, mock ou variável não exercitada não transformam um controle em `CONCLUIDO`.

## Responsabilidades

- `TEMPLATE`: pertence ao código, testes, documentação ou workflows deste repositório.
- `TEMPLATE_PROCESSO`: governança executável deste repositório.
- `HIBRIDO_EXTENSAO`: exige coordenação com `msentraauth.flask-extension`.
- `HIBRIDO_CONSUMIDOR`: o template fornece contrato seguro, mas a aplicação consumidora
  define persistência e regras de negócio.
- `HIBRIDO_EXTERNO`: combina mudança no template e configuração de infraestrutura.
- `EXTERNO`: só pode ser encerrado com evidência da plataforma real.

## Regra de execução

Cada etapa deve:

1. confirmar o SHA atual de `dev`;
2. comparar `dev` e `prod` sem sincronizá-las;
3. implementar somente seus controles;
4. preservar os gates existentes;
5. atualizar `07_STATUS.md`;
6. entregar somente arquivos criados ou alterados;
7. registrar validações executadas e não executadas;
8. sugerir um único commit coeso.

## Política de ADR

A `SEC-00` não cria ADR porque não altera arquitetura ou runtime. Ela estabelece governança.
Decisões irreversíveis ou com migração, como envelope criptográfico de sessão, key ring,
autorização ou publicação build-once, exigem ADR na etapa responsável.

## Estado da fundação

A documentação da `SEC-00`, o hardening de supply chain da `SEC-01`, o código de configuração/Graph da `SEC-02` e o hardening de sessão da `SEC-03` estão implementados. As etapas permanecem `PARCIAL` enquanto gates indisponíveis e controles externos ou da extensão não tiverem evidência real.
