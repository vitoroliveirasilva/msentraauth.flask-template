# ADR-002: sessão server-side com Redis

## Decisão

Produção usa Redis para sessão e cache por meio das integrações definidas.

## Consequência

- Múltiplos workers compartilham estado;
- Mudança futura exige novo ADR e atualização documental.
