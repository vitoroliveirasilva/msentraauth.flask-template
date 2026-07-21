# Segurança

Relate vulnerabilidades de forma privada pelo recurso **Private vulnerability reporting** do GitHub, quando habilitado. Não abra issue pública com client secret, auth code, access token, refresh token, cookie, SID, cache, claims completas ou dados pessoais reais.

## Regras de produção

- HTTPS e `SESSION_COOKIE_SECURE=true`;
- `APP_SECRET_KEY` longa, aleatória e fornecida por secret manager;
- Redis privado, autenticado e com TLS quando aplicável;
- `REDIS_TLS_REQUIRED=true` e URI `rediss://` em produção;
- Proxy hops configurados somente quando a topologia é conhecida;
- `User.Read` como escopo mínimo para a rota de perfil;
- Logs sem payloads de Entra, Graph ou query string do callback;
- Imagem executada como usuário não-root;
- Dependências, Actions e imagens auditadas continuamente;
- Branches e tags de produção protegidas;
- Rotação periódica de credenciais e plano de revogação.

## Limites

O registro local em memória é demonstrativo e não substitui banco transacional, autorização de negócio, trilha de auditoria persistente ou governança de identidades.
