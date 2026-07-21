# ADR-009: sessão Redis pequena e explícita

## Decisão

Usar `SessionInterface` própria com SID assinado e payload Redis ao invés de adicionar uma camada genérica de sessão.

## Consequência

- Menos dependências e contrato auditável;
- Cookie não contém identidade ou token;
- TTL, namespace e limite de payload são controlados pelo template;
- SID é rotacionado depois do login;
- Cookie obsoleto é descartado em assinatura inválida, expiração ou corrupção;
- Evolução de serializer ou cookie exige testes de compatibilidade e migração explícita.
