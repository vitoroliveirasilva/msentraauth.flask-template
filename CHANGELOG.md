# Changelog

## 2.0.0 - 2026-08-21

### Breaking

- O repositório passa de aplicação de referência copiável para generator Copier canônico.
- O package, a distribuição, branding, namespace Redis, cookie e artefatos de deploy passam a pertencer ao projeto gerado.
- Graph deixa de ser obrigatório e é desabilitado por padrão.
- UI, health checks e autenticação visual passam a ter blueprints separados e templates namespaced.
- O registro local de usuários em memória deixa de fazer parte do caminho padrão.

### Security

- Preservados sessão Redis server-side, envelope AEAD, rotação/revogação de SID, schema estrito, CSRF, fail-fast de produção, trusted hosts e ProxyFix explícito.
- CSP passa a ter allowlists externas explícitas e validadas sem liberar `*`, `unsafe-inline` ou `unsafe-eval`.
- Copier mínimo atualizado para 9.17.1, incluindo correções de segurança do mecanismo de templates.
