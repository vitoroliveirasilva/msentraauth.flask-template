# ADR-009: sessão Redis pequena e explícita

## Decisão

Usar `SessionInterface` própria com SID assinado e payload Redis ao invés de adicionar uma camada genérica de sessão.

As gravações usam `NX` para SIDs novos e `XX` para SIDs já carregados. Assim, uma requisição concorrente não pode recriar um SID antigo depois que a rotação remove sua chave.

Uma falha transitória de leitura no Redis não é tratada como sessão ausente. O cookie é preservado, liveness continua independente do backend e rotas que dependem da sessão retornam indisponibilidade temporária até o Redis se recuperar. Sessões anônimas vazias permanecem sem cookie e sem chave Redis.

## Consequência

- Menos dependências e contrato auditável;
- Cookie não contém identidade ou token;
- Leituras marcam a sessão como acessada para emissão de `Vary: Cookie`;
- TTL, namespace e limite de payload são controlados pelo template;
- SID é rotacionado depois do login;
- Gravações de requisições obsoletas falham de forma fechada após rotação ou expiração;
- Cookie obsoleto é descartado em assinatura inválida, expiração ou corrupção, mesmo sem refresh por requisição;
- Falhas transitórias do Redis não destroem a referência de uma sessão ainda válida;
- Evolução de serializer, cookie, indisponibilidade ou estratégia de concorrência exige testes de compatibilidade e migração explícita.
