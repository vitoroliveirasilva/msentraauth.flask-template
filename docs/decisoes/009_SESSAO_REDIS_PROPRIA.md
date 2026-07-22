# ADR-009: sessão Redis pequena e explícita

## Decisão

Usar `SessionInterface` própria com SID assinado e payload Redis ao invés de adicionar uma camada genérica de sessão.

As gravações usam `NX` para SIDs novos e `XX` para SIDs já carregados. Assim, uma requisição concorrente não pode recriar um SID antigo depois que a rotação remove sua chave.

## Consequência

- Menos dependências e contrato auditável;
- Cookie não contém identidade ou token;
- TTL, namespace e limite de payload são controlados pelo template;
- SID é rotacionado depois do login;
- Gravações de requisições obsoletas falham de forma fechada após rotação ou expiração;
- Cookie obsoleto é descartado em assinatura inválida, expiração ou corrupção, mesmo sem refresh por requisição;
- Evolução de serializer, cookie ou estratégia de concorrência exige testes de compatibilidade e migração explícita.
