# msentraauth.flask-template 2.x

Generator Copier de aplicações Flask com Microsoft Entra ID, sessão Redis server-side criptografada e baseline de segurança para produção.

> **Caminho oficial:** use Copier. O botão **Use this template** do GitHub não parametriza nome de package, namespace, cookie, features opcionais nem mantém o vínculo de atualização do template.

## Escolha seu caminho

- **Nova aplicação:** gere um projeto com Copier e desenvolva no projeto gerado.
- **Aplicação Flask existente:** não sobreponha este repositório; siga [`docs/INTEGRATING_EXISTING_APP.md`](docs/INTEGRATING_EXISTING_APP.md).
- **Manutenção deste generator:** siga [`docs/TEMPLATE_MAINTAINERS.md`](docs/TEMPLATE_MAINTAINERS.md).

## Quick Start

```powershell
cd C:\repos
pipx install "copier==9.17.0"
copier copy --vcs-ref v2.0.0 gh:vitoroliveirasilva/msentraauth.flask-template sistema-processos
cd .\sistema-processos
```

O diretório `sistema-processos` é a aplicação independente. O código Python fica em `src/<package_name>/`. Não crie a aplicação dentro deste repositório-fonte.

Rotas `/auth/login`, `/auth/callback` e `/auth/logout` pertencem a `flask-ms-entra-auth`. A aplicação gerada possui `/login` apenas como tela visual e mantém logout via `POST` protegido por CSRF.

O projeto gerado inclui validação fail-fast de ambiente, testes com cobertura mínima de 80%, Ruff, mypy, Bandit, pip-audit, CI, imagem imutável e Compose endurecido. Versione `.copier-answers.yml`, mas nunca coloque segredos nele.

Comece por [`docs/00_COMECE_AQUI.md`](docs/00_COMECE_AQUI.md).
