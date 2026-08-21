# Ownership

| Elemento | Dono |
|---|---|
| OAuth/OIDC, state, callback, token cache, `/auth/*` | `flask-ms-entra-auth` |
| Redis/session/SID rotation/revocation | foundation gerada |
| `/login`, `/`, navbar e layout | aplicação |
| `/health/*` | blueprint `ops` |
| Graph profile | feature opcional |
| usuário local/RBAC | negócio da aplicação |
| CSP/headers | foundation, via configuração segura |
