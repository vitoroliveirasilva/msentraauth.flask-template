# Visão e escopo

O template é uma aplicação Flask de referência que demonstra a extensão `flask-ms-entra-auth` em um cenário próximo de produção.

## Incluído

- Application factory;
- Sessão e storage Redis;
- Login, callback, logout e identidade fornecidos pela extensão;
- Vínculo local demonstrativo;
- Perfil Microsoft Graph;
- Interface Jinja, CSRF e headers;
- Logs, health checks, testes, Gunicorn e Docker.

## Fora do escopo

- Autorização empresarial, grupos e app roles;
- Banco de usuários definitivo;
- Graph genérica;
- Multi-tenant, B2C/External ID e múltiplos provedores;
- Gerenciamento de secrets ou infraestrutura cloud específica.
