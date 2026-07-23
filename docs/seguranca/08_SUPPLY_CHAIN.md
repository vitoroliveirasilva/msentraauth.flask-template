# Supply chain, CI/CD, artefatos e contêineres

## Baseline da implementação

- Branch: `dev`
- SHA analisado: `18ee71ca8c7dbddd2fce06738c9ff974306a0861`
- Data: `2026-07-23`
- Relação com `prod`: divergente, 14 commits à frente e 4 atrás

Nenhuma sincronização entre branches foi realizada.

## Entradas imutáveis

`pip==26.1.2` fixa o bootstrap Python. As Actions são referenciadas por SHA completo e acompanhadas da versão humana em comentário. O
validador `scripts/validate_supply_chain.py` mantém uma allowlist dos commits aprovados e falha se
uma tag mutável ou Action desconhecida for introduzida.

As imagens-base estão fixadas por digest:

- Python `3.14-slim-bookworm`: `sha256:a9bee15510a364124aa24692899d269835683b883de42f7ebec8c293cf679ccb`
- Redis `8-alpine`: `sha256:9d317178eceac8454a2284a9e6df2466b93c745529947f0cd42a0fa9609d7005`

Tags continuam visíveis para leitura humana, mas não participam da decisão de bytes executados.

## Dependências Python

O `pyproject.toml` preserva intervalos de compatibilidade para as dependências gerais e fixa
`flask-ms-entra-auth==1.0.0`, que é o contrato de autenticação validado. CI, Docker e scripts usam
constraints com versões diretas exatas.

`SC-004` e `SC-005` permanecem `PARCIAL` porque o ambiente desta implementação não permitiu gerar e
validar locks transitivos multi-Python com `--generate-hashes`. O procedimento obrigatório está em
`requirements/README.md` e não deve ser substituído por um lock inventado ou produzido sem revisão.

## Build único e promoção

O workflow de publicação agora:

1. valida a tag e o commit de origem;
2. constrói o pacote Python uma única vez;
3. gera checksums, SBOM e attestation do pacote;
4. constrói e envia uma única imagem candidata multi-plataforma;
5. testa o digest exato em `linux/amd64` e `linux/arm64`;
6. escaneia o mesmo digest com Trivy;
7. promove o digest verificado para tags sem reconstruir;
8. gera attestation do digest promovido;
9. anexa à Release os mesmos bytes do artifact de pacote, sem sobrescrever anexos existentes.

A tag candidata é um nome operacional. A identidade confiável do artefato é o digest OCI.

## Privilégios

Todos os workflows usam `permissions: {}` por padrão. Cada job concede somente o necessário.
Checkout desabilita persistência de credenciais. Somente a promoção possui `packages: write`, a
attestation possui `id-token: write` e `attestations: write`, e o anexo à Release possui
`contents: write`.

## Contêineres

- `.dockerignore` é allowlist deny-all;
- Python e Redis usam digests;
- runtime não possui home gravável e usa UID/GID `10001`;
- Compose publica a aplicação apenas em loopback;
- Redis fica somente na rede interna;
- Redis local exige senha;
- ambos os serviços removem capabilities, usam `no-new-privileges` e limites de PID, memória e CPU;
- filesystem é somente leitura, exceto tmpfs e volume de dados explicitamente declarados.

O Compose continua sendo referência local/homologação. TLS e ACL granular do Redis de produção
continuam externos e pertencem às etapas posteriores.

## Atualização segura

1. Atualize uma dependência, Action ou imagem crítica por PR separado.
2. Resolva a nova versão por fonte primária.
3. Registre tag humana, SHA/digest e data.
4. Atualize a allowlist do validador.
5. Regenere locks e hashes quando houver mudança Python.
6. Execute todos os gates, builds, smoke tests, scanner, SBOM e attestation.
7. Compare o digest testado com o digest promovido.
8. Preserve o valor anterior no histórico para rollback.

Dependabot mantém Python, Actions e Docker em PRs individuais. A atualização só é concluída depois
da regeneração das constraints/locks e da revisão dos novos SHAs ou digests.

## Evidências esperadas após aplicação

- `python scripts/validate_supply_chain.py` aprovado;
- matriz Python 3.11 a 3.14 aprovada;
- Redis real aprovado;
- wheel/sdist inspecionados;
- `SHA256SUMS` e SBOM produzidos;
- imagem não-root aprovada;
- Trivy sem achados bloqueantes;
- smoke do digest exato em AMD64 e ARM64;
- attestations verificáveis no GitHub/GHCR.

## Estado de validação desta entrega

Os controles `SC-001`, `SC-002`, `SC-003`, `SC-015` e `SC-018` possuem verificação local
suficiente. Os demais controles permanecem `PARCIAL` até que instalação, build, Docker, Redis,
Trivy, Dependency Review, SBOM, attestations e promoção por digest sejam executados na CI após a
aplicação do patch. Essa classificação evita transformar configuração não exercitada em evidência.
