# Arquitetura

```text
Navegador
   |
   v
Flask + Jinja + CSRF
   |
   +-- flask-ms-entra-auth 1.x
   |      +-- MSAL e Authorization Code Flow
   |      +-- Identidade, hooks e auditoria
   |
   +-- RedisSessionInterface ----+
   +-- RedisAuthStorage ----------+--> Redis
   +-- GraphClient ------------------> Microsoft Graph
   +-- Health, logs e headers
```

A mesma conexão Redis é reutilizada, mas sessão e autenticação possuem prefixos distintos. O cookie contém apenas SID assinado. O token delegado existe somente durante a chamada server-side ao Graph.

## Estrutura

```text
src/msentraauth_template/
├── settings.py
├── session_backend.py
├── storage.py
├── auth/hooks.py
├── graph/client.py
├── graph/routes.py
├── web/routes.py
├── templates/
└── static/
```
