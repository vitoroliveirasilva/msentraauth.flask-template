# Microsoft Graph

O template chama exclusivamente `GET /me` com `$select=id,displayName,userPrincipalName,mail`.
O access token permanece no servidor.

## Egress e transporte

- endpoint fixo `https://graph.microsoft.com/v1.0`;
- `requests.Session.trust_env=false`;
- sem `.netrc` ou autenticação herdada;
- TLS e hostname verification sempre ativos;
- redirects desabilitados para impedir reenvio do bearer;
- streaming com limite de corpo descompactado;
- `Content-Type` JSON obrigatório;
- pool reutilizável e retries limitados somente para `GET`.

## Respostas

O cliente distingue:

- `401`: credencial recusada;
- `403`: operação proibida;
- `429`: rate limit com `Retry-After` limitado;
- `5xx`: indisponibilidade transitória;
- `3xx`: redirect rejeitado;
- corpo grande, tipo inesperado, JSON inválido e DTO inválido: resposta externa inválida.

Campos do perfil possuem limites de tipo, tamanho e caracteres de controle. O `User-Agent` deriva
da versão instalada do pacote e não inclui host, usuário ou ambiente.

## Claims challenge

`WWW-Authenticate` com `claims` é limitado, parseado como JSON e normalizado em memória. O valor
não entra em logs ou resposta. Como a extensão `1.0.0` não recebe claims na aquisição de token, o
template responde `401` sem redirect automático. Isso evita loop e mantém a lacuna explícita.

## Cloud

Somente o cloud global é permitido. Endpoints soberanos exigem que authority, issuer, tenant e
Graph sejam tratados juntos pela extensão; aceitar somente uma URL alternativa no template seria
uma proteção ilusória e reabriria SSRF/configuração indevida.
