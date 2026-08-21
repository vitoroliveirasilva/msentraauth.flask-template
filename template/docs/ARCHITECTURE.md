# Arquitetura

A aplicação usa application factory e separa autenticação, infraestrutura, blueprints e features. OAuth/OIDC fica delegado ao `flask-ms-entra-auth`; a aplicação só fornece storage Redis, sessão server-side, hooks pós-autenticação e UI.

## Fronteiras

- `auth/`: integração e hooks, sem regra de negócio.
- `infrastructure/`: Redis, envelope AEAD, sessão, segurança e observabilidade.
- `blueprints/`: rotas HTTP da aplicação.
- `features/graph/`: integração Graph opcional.
- `application.py`: ponto explícito para registrar recursos de negócio.

A sessão do navegador contém apenas SID opaco assinado. O payload fica no Redis protegido por AEAD e possui timeout ocioso/absoluto, rotação de SID e revisão de revogação por identidade.
