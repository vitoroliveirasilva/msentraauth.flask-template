# Segurança

- Sessão Redis com SID assinado, payload server-side e limite de 64 KiB;
- Rotação do SID depois da autenticação para reduzir session fixation;
- Vínculo local realizado somente após a rotação bem-sucedida do SID;
- Persistência condicional `NX`/`XX` para impedir que requisições concorrentes recriem SIDs removidos;
- Descarte de cookies inválidos, expirados ou associados a payload corrompido, inclusive sem refresh por requisição;
- Preservação do cookie em indisponibilidade transitória do Redis, com bloqueio temporário e resposta `503` nas rotas dependentes de sessão;
- Sessões anônimas vazias não geram cookie nem chave Redis;
- Respostas que consultam a sessão incluem `Vary: Cookie`;
- Storage atômico Redis para transações de uso único;
- Produção exige HTTPS, cookie secure, Redis TLS, CSRF ativo e `TESTING=false`;
- Timeouts precisam ser positivos e finitos;
- CSRF em formulários e logout por POST;
- CSP, HSTS em HTTPS, anti-frame, nosniff, COOP, CORP e Permissions Policy;
- Trusted hosts e URLs externas validadas;
- Alias de callback restrito a caminho estático e seguro;
- Request ID sanitizado;
- Logs JSON e texto usam campos permitidos, linha única e somente o tipo de exceção;
- Logs não incluem tokens, claims, SID, auth code, state ou corpo Graph;
- Access log do Gunicorn sem query string;
- Container não-root, filesystem read-only no Compose e `no-new-privileges`;
- Publicação de imagem vinculada ao commit da tag versionada;
- Microsoft Graph com escopo e campos mínimos, retentativas limitadas e sem espera externa não delimitada;
- Limite de corpo e quantidade de partes de formulário.

Autenticação não substitui autorização. O hook local demonstra vínculo e rotação de sessão, não papéis ou permissões. O registro em memória é limitado, mas continua sendo apenas uma demonstração e deve ser substituído quando houver persistência de usuários de negócio.
