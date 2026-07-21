# Testes e qualidade

A suíte cobre settings, sessão, storage, hooks, Graph, factory, operação, contrato da extensão e artefatos.

## Gate

- Ruff lint e format;
- mypy estrito;
- pytest com 100% de linhas e branches;
- Bandit e pip-audit;
- build e `twine check`;
- inspeção de wheel/sdist;
- job com Redis real;
- build Docker.

MSAL, Graph e Redis usam doubles nos testes rápidos. A CI adiciona integração com Redis real sem credenciais Microsoft.
