# Arquitetura de segurança

`flask-ms-entra-auth` é o único dono de OAuth/OIDC, state, callback, token cache e logout de protocolo. O starter adiciona sessão server-side Redis, CSRF, headers, observabilidade e integração segura de identidade.

A sessão usa SID opaco assinado no navegador e payload protegido no Redis. Mantém timeout idle/absoluto, rotação periódica e pós-auth, revogação por identidade, schema estrito e operações atômicas.

Produção exige HTTPS, cookie Secure/HttpOnly, chaves criptográficas independentes, Redis TLS, trusted hosts explícitos, CSRF, debug desligado e namespace próprio por aplicação/ambiente.

CSP usa `self` por padrão. Origens externas só entram por allowlists validadas; `*`, `unsafe-inline` e `unsafe-eval` são rejeitados.
