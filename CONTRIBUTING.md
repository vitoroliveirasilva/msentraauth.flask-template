# Contribuindo

O produto deste repositório é o **template gerado**, não uma aplicação de referência executada na raiz.

Antes de enviar uma mudança, rode `pytest`, os testes de geração, o scanner de placeholders/hardcodes e, quando disponíveis, Copier, Ruff, mypy, Bandit, pip-audit e Docker. Mudanças em auth/session/security exigem regressão completa dos projetos renderizados com e sem Graph.

Não introduza código OAuth/OIDC paralelo ao `flask-ms-entra-auth`.
