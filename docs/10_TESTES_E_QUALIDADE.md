# Testes e qualidade

A suíte cobre settings, sessão, concorrência, indisponibilidade do Redis, storage, hooks, Graph, factory, operação, contrato da extensão e artefatos.

## Gate

- Ruff lint e format;
- mypy estrito;
- pytest com 100% de linhas e branches;
- Bandit e pip-audit;
- build e `twine check`;
- inspeção de wheel/sdist com versão obtida do `pyproject.toml`;
- job com Redis real;
- validação do Compose;
- build Docker, confirmação de UID não-root e smoke test da imagem com Redis.

MSAL, Graph e Redis usam doubles nos testes rápidos. A CI adiciona integração com Redis real sem credenciais Microsoft e exercita a imagem final antes de qualquer release.

Os scripts `validate.ps1` e `validate.sh` resolvem a raiz do repositório automaticamente e interrompem no primeiro comando externo com código de saída diferente de zero. Uma execução que chega ao fim representa todos os gates aprovados.
