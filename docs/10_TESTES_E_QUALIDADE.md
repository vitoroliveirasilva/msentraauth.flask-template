# Testes e qualidade

## Unitários

Settings, DTOs, validações, cliente Graph, URLs e handlers.

## Integração

Factory, sessão, Redis, extensão, hooks, blueprints e error pages.

## Contrato

Compatibilidade com a versão da extensão e com storage.

## End-to-end controlado

Tenant de homologação sem credenciais no CI público e fluxo real somente em ambiente protegido.

# Casos obrigatórios

- Login e callback mockados;
- State inválido;
- Sessão regenerada;
- Usuário não autorizado;
- Token silencioso e reautenticação;
- Graph 200, 401, 403, 429 e 5xx;
- Timeout e JSON inválido;
- Logout;
- Headers;
- Health;
- Múltiplos workers/sessões;
- Configuração inválida.

# Qualidade

- Ruff;
- mypy;
- pytest;
- Cobertura de branches;
- Bandit;
- pip-audit;
- Build da imagem;
- Scanner de imagem;
- gitleaks.

# Dados de teste

Somente IDs, claims e secrets fictícios.
