# Segurança

- Sessão Redis com SID assinado, payload server-side e limite de 64 KiB;
- Rotação do SID depois da autenticação para reduzir session fixation;
- Persistência condicional `NX`/`XX` para impedir que requisições concorrentes recriem SIDs removidos;
- Descarte de cookies inválidos, expirados ou associados a payload corrompido, inclusive sem refresh por requisição;
- Storage atômico Redis para transações de uso único;
- CSRF em formulários e logout por POST;
- CSP, HSTS em HTTPS, anti-frame, nosniff, COOP, CORP e Permissions Policy;
- Trusted hosts e URLs externas validadas;
- Request ID sanitizado;
- Logs sem tokens, claims, SID, auth code, state ou corpo Graph;
- Access log do Gunicorn sem query string;
- Container não-root, filesystem read-only no Compose e `no-new-privileges`;
- Microsoft Graph com escopo e campos mínimos;
- Limite de corpo e quantidade de partes de formulário.

Autenticação não substitui autorização. O hook local demonstra vínculo e rotação de sessão, não papéis ou permissões.
