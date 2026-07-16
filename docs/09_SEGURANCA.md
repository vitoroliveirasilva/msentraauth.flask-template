# Segurança

- Autenticação delegada à extensão;
- Sessão server-side;
- Tokens fora do usuário e do navegador;
- Configuração explícita;
- Menor privilégio;
- Erros sem detalhes internos;
- Logs sem credenciais;
- HTTPS em produção.

## Controles

| Risco | Controle |
|---|---|
| Login CSRF | State/nonce pela extensão |
| Session fixation | Regenerar ID após login |
| Cookie roubado | Secure, HttpOnly, SameSite |
| Token vazado | Cache server-side e redação |
| Open redirect | Destino local validado |
| Host poisoning | TRUSTED_HOSTS e URI explícita |
| Forced logout | POST + CSRF |
| Clickjacking | CSP frame-ancestors e X-Frame-Options |
| XSS | Autoescape, CSP e sem `safe` indevido |
| Dependência vulnerável | Lock, auditoria e atualização |
| Redis exposto | Rede privada, auth, TLS e TTL |

## Headers

- Content-Security-Policy;
- Strict-Transport-Security em HTTPS completo;
- X-Content-Type-Options;
- X-Frame-Options;
- Referrer-Policy;
- Permissions-Policy.

## Cookies

Produção deve usar Secure, HttpOnly, SameSite Lax, nome exclusivo, TTL e rotação de sessão.

## Logs proibidos

Auth code, tokens, cookie, segredo, cache, claims completas e query string do callback.

## Responsabilidade externa

Políticas de Conditional Access, MFA, consentimento, rotação de secret e configuração do tenant precisam ser administradas fora do código.
