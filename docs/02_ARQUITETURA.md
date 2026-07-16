# Arquitetura

```text
src/msentraauth_template/
├── __init__.py
├── settings.py
├── extensions.py
├── observability.py
├── security.py
├── auth/
│   ├── routes.py
│   ├── user.py
│   └── hooks.py
├── graph/
│   ├── client.py
│   ├── models.py
│   └── routes.py
├── web/
│   └── routes.py
├── templates/
└── static/
tests/
docs/
wsgi.py
```

## Camadas

### Aplicação

Factory, blueprints, config, handlers e integração de extensões.

### Autenticação

A extensão controla o protocolo enquant o template contém somente hooks, usuário local de demonstração e rotas específicas quando necessário.

### Graph

Cliente próprio com timeout, tratamento de status, DTO e `$select`.

### Sessão

Server-side, com Redis em produção e opção adequada para testes.

### Interface

Templates Jinja acessíveis, sem depender de respostas brutas do provedor.

### Operação

WSGI, Docker, health, logs e configuração de proxy.

## Regras

- Nenhuma regra de autenticação duplicada fora da extensão;
- Access token não é atributo de usuário;
- Rotas não chamam HTTP externo diretamente;
- Config falha cedo;
- Erros externos são traduzidos;
- Frontend usa `url_for`;
- Ambiente local não define padrão inseguro de produção.
