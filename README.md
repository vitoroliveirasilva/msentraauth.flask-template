# MS Entra Auth: template Flask

[![CI](https://github.com/vitoroliveirasilva/msentraauth.flask-template/actions/workflows/ci.yml/badge.svg?branch=prod)](https://github.com/vitoroliveirasilva/msentraauth.flask-template/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Aplicação Flask de referência para integrar a extensão [`flask-ms-entra-auth`](https://github.com/vitoroliveirasilva/msentraauth.flask-extension) com sessão Redis server-side, Microsoft Graph, vínculo local por hook, observabilidade, segurança de navegador, CI e execução em contêiner.

O projeto demonstra uma base pronta para adaptação em produção. Autenticação fica na extensão e autorização, usuários de negócio e regras da aplicação continuam sob responsabilidade do consumidor.

## O que está implementado

- Application factory e pacote em estrutura `src`;
- Login, callback, identidade, aquisição silenciosa e logout pela extensão `flask-ms-entra-auth` 1.x;
- Sessão Flask no Redis com SID opaco assinado, TTL, limite de payload e rotação após autenticação;
- Descarte de cookies inválidos, expirados ou associados a payload corrompido;
- `RedisAuthStorage` com consumo atômico de uso único por Lua;
- Cliente Microsoft Graph para `GET /me`, com `$select` mínimo, timeouts e retries limitados;
- Vínculo local demonstrativo por hook, sem duplicar OAuth/OIDC;
- Jinja, CSRF, CSP, trusted hosts e headers defensivos;
- Request ID sanitizado e logs sem tokens, códigos de autorização, claims completas ou query string do callback;
- Health checks de liveness e readiness;
- Gunicorn, Docker multi-stage, usuário não-root e Compose;
- CI em Python 3.11, 3.12, 3.13 e 3.14;
- Testes unitários, integração com Redis real, auditoria e inspeção dos artefatos.

## Arquitetura

```text
Navegador
   |
   v
Flask + Jinja + CSRF
   |
   +-- flask-ms-entra-auth 1.x
   |      +-- MSAL / Authorization Code Flow
   |      +-- State, identidade, token cache e hooks
   |
   +-- RedisSessionInterface ----+
   +-- RedisAuthStorage ----------+--> Redis privado
   +-- GraphClient ------------------> Microsoft Graph
   +-- Health, logs e headers
```

O navegador recebe somente um SID assinado. Sessão, fluxo, identidade e token cache permanecem no servidor. O access token delegado é usado apenas durante a chamada server-side ao Microsoft Graph.

## Requisitos

- Python 3.11 ou superior;
- Redis 6.2 ou superior;
- App Registration single-tenant no Microsoft Entra ID;
- Permissão delegada `User.Read`;
- Extensão `flask-ms-entra-auth>=1.0,<2` disponível no PyPI ou instalada localmente.

## Início rápido no PowerShell

```powershell
cd C:\Users\vitor.silva\Downloads\Github\msentraauth.flask-template

py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

Copy-Item .env.example .env
```

Gere um segredo de sessão:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Edite `.env`, substitua todos os placeholders e inicie um Redis local. Depois execute:

```powershell
python -m flask --app wsgi:app run --debug
```

Acesse `http://localhost:5000`.

## Desenvolvimento conjunto com a extensão

Para testar mudanças ainda não publicadas da extensão:

```powershell
python -m pip install -e "..\msentraauth.flask-extension"
python -m pip install -e ".[dev]"
```

Essa instalação editável é apenas para desenvolvimento. Em uma imagem ou deploy normal, a extensão é resolvida pelo índice configurado.

## Docker Compose

1. Copie `.env.example` para `.env`;
2. Preencha as credenciais reais;
3. Mantenha `APP_BASE_URL=http://localhost:5000` para o ambiente local;
4. Execute:

```powershell
docker compose up --build
```

A aplicação fica disponível em `http://localhost:5000`. O Redis não publica porta no host e é acessível apenas pela rede do Compose.

O Compose é uma referência local e de homologação. Em produção, prefira Redis gerenciado, TLS, backups, métricas, secret manager e um proxy HTTPS conhecido.

## Configuração do Microsoft Entra ID

No App Registration:

1. Configure a aplicação como single-tenant;
2. Adicione a plataforma **Web**;
3. Registre exatamente `http://localhost:5000/auth/callback` para desenvolvimento;
4. Registre a URI HTTPS real para produção;
5. Adicione a permissão delegada `User.Read`;
6. Conceda consentimento conforme a política do tenant;
7. Crie uma credencial e armazene-a fora do Git.

Valores centrais do `.env`:

```dotenv
APP_BASE_URL=http://localhost:5000
APP_TRUSTED_HOSTS=localhost,127.0.0.1
MS_ENTRA_CLIENT_ID=...
MS_ENTRA_CLIENT_SECRET=...
MS_ENTRA_TENANT_ID=...
MS_ENTRA_REDIRECT_URI=http://localhost:5000/auth/callback
MS_ENTRA_SCOPES=User.Read
REDIS_URL=redis://localhost:6379/0
```

A configuração falha cedo quando encontra placeholders, segredo curto, origem divergente, host não confiável, porta inválida, ausência de `User.Read` ou postura insegura de produção.

## Produção

Configuração mínima esperada:

```dotenv
APP_ENV=production
APP_BASE_URL=https://app.exemplo.com
APP_TRUSTED_HOSTS=app.exemplo.com
APP_LOG_FORMAT=json
SESSION_COOKIE_SECURE=true
REDIS_TLS_REQUIRED=true
REDIS_URL=rediss://usuario:senha@redis.exemplo.com:6380/0
```

Também é necessário:

- Fornecer secrets por secret manager;
- Declarar `PROXY_X_*` somente de acordo com a topologia real;
- Restringir rede e credenciais do Redis;
- Configurar CA do Redis pelo URI/opções suportadas pelo redis-py quando aplicável;
- Substituir o registro local em memória por repositório transacional, caso a aplicação precise de vínculo persistente;
- Implementar autorização de negócio separadamente.

## Endpoints

| Método | Endpoint         | Finalidade                                 |
| ------ | ---------------- | ------------------------------------------ |
| `GET`  | `/`              | Página inicial                             |
| `GET`  | `/auth/login`    | Inicia autenticação                        |
| `GET`  | `/auth/callback` | Callback do Microsoft Entra ID             |
| `POST` | `/auth/logout`   | Remove autenticação local                  |
| `GET`  | `/profile`       | Perfil protegido obtido do Microsoft Graph |
| `GET`  | `/logged-out`    | Confirmação de logout local                |
| `GET`  | `/health/live`   | Processo ativo                             |
| `GET`  | `/health/ready`  | Redis disponível                           |

O logout é local e não encerra todas as sessões Microsoft do usuário.

## Validação

PowerShell:

```powershell
.\scripts\validate.ps1
```

Linux/macOS:

```bash
./scripts/validate.sh
```

O gate executa:

- Ruff lint e formatação;
- mypy estrito;
- Compilação dos módulos;
- pytest com 100% de linhas e branches;
- Bandit;
- `pip-audit`;
- build de wheel e sdist;
- `twine check`;
- Inspeção dos artefatos;
- `pip check`.

## Testes e rede

MSAL, Microsoft Graph e Redis usam doubles determinísticos na suíte rápida. A CI adiciona um job com Redis real, sem usar credenciais Microsoft. A imagem Docker também é construída na CI.

## Limites deliberados

- Não inclui RBAC, grupos, app roles ou políticas de autorização;
- O registro local em memória é apenas uma demonstração de hook;
- Não é multi-tenant;
- Não encerra a sessão global Microsoft;
- Não inclui infraestrutura cloud específica;
- Não publica este template no PyPI.

## Documentação

O índice completo está em [`docs/README.md`](docs/README.md). Consulte especialmente:

- [Arquitetura](docs/02_ARQUITETURA.md);
- [Configuração do Microsoft Entra ID](docs/06_CONFIGURACAO_MICROSOFT_ENTRA_ID.md);
- [Segurança](docs/09_SEGURANCA.md);
- [Deploy e operação](docs/11_DEPLOY_E_OPERACAO.md);
- [Solução de problemas](docs/15_SOLUCAO_DE_PROBLEMAS.md);
- [Status de implementação](docs/implementation/status.md).

## Licença e marcas

Distribuído sob a [Licença MIT](LICENSE). Este é um projeto independente e não oficial, sem afiliação, manutenção ou endosso da Microsoft.
