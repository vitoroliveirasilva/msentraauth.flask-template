# ADR-010: extensão 1.x e ordem de release

## Decisão

Fixar `flask-ms-entra-auth>=1.0,<2` e publicar a extensão antes de ativar a CI normal do template.

## Consequência

- O consumidor testa um contrato estável;
- Desenvolvimento conjunto continua possível por instalação editável;
- Mudança major da extensão exige revisão explícita do template;
- O template não mantém cópia vendorizada da biblioteca.
