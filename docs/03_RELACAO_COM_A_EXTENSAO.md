# Relação com a extensão

## Extensão

Controla protocolo MSAL, state, callback, cache, aquisição silenciosa, identidade, logout, hooks, erros e contrato de storage.

## Template

Fornece Redis, sessão Flask, vínculo local, Graph, interface, headers, health checks, Docker e documentação operacional.

## Dependência

Produção:

```text
flask-ms-entra-auth>=1.0,<2
```

- Desenvolvimento conjunto usa instalação editável do repositório irmão;
- A ordem de release é extensão primeiro, template depois;
- O template não contém fallback OAuth próprio.
