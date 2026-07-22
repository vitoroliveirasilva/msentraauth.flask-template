# ADR-009: sessão Redis pequena e explícita

## Decisão

Usar `SessionInterface` própria com SID assinado e payload Redis ao invés de adicionar uma camada genérica de sessão.

As gravações usam `NX` para SIDs novos e `XX` para SIDs já carregados. Assim, uma requisição concorrente não pode recriar um SID antigo depois que a rotação remove sua chave.

Uma falha transitória ou um retorno inválido de leitura no Redis não é tratado como sessão ausente. O cookie é preservado, liveness continua independente do backend e rotas que dependem da sessão retornam indisponibilidade temporária até o Redis se recuperar. Rotas estáticas e health checks não carregam sessão. Sessões anônimas vazias permanecem sem cookie e sem chave Redis.

A ausência de uma chave para um SID ainda corretamente assinado cria uma sessão anônima nova sem remover o cookie na resposta vazia. Essa decisão evita que uma requisição concorrente com SID antigo apague um cookie recém-rotacionado emitido por outra resposta. Falhas de gravação ou exclusão substituem a resposta por indisponibilidade sanitizada e removem headers incompatíveis antes de chegar ao navegador.

## Consequência

- Menos dependências e contrato auditável;
- Cookie não contém identidade ou token;
- Leituras marcam a sessão como acessada para emissão de `Vary: Cookie`;
- TTL, namespace e limite de payload são controlados pelo template;
- SID é rotacionado depois do login;
- Gravações de requisições obsoletas falham de forma fechada após rotação ou expiração;
- Cookie é descartado em assinatura inválida ou corrupção; uma referência assinada sem chave é preservada até ser substituída por estado novo;
- Falhas transitórias do Redis não destroem a referência de uma sessão ainda válida nem confirmam operações que não foram persistidas;
- Static assets e health checks não pagam o custo de leitura de sessão;
- Evolução de serializer, cookie, indisponibilidade ou estratégia de concorrência exige testes de compatibilidade e migração explícita.
