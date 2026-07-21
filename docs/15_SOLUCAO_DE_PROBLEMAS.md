# Solução de problemas

## Pacote da extensão não encontrado

Confirme acesso ao PyPI e instale `flask-ms-entra-auth>=1.0,<2`. Para desenvolvimento conjunto, instale o repositório irmão em modo editável.

## `SettingsError`

Revise placeholders, tamanho dos secrets, HTTPS de produção, origem do redirect, host confiável, porta, `User.Read`, booleanos e URI Redis.

## `/health/ready` retorna 503

Confirme `REDIS_URL`, DNS, porta, TLS, autenticação, CA, firewall e permissões do Redis. O endpoint não testa Microsoft Graph.

## Callback ausente ou consumido

Verifique TTL, namespace, compartilhamento do Redis entre workers e suporte atômico. Não reutilize o mesmo callback.

## Graph retorna 401/403

Confirme consentimento de `User.Read`, conta do cache e App Registration. Refaça o login quando necessário e não registre a resposta bruta.

## Login retorna 400 localmente

Use host permitido, redirect exatamente registrado e `APP_BASE_URL` coerente com o navegador. Uma requisição com host não confiável recebe `400` simples e não renderiza detalhes.

## Cookie desaparece após uma falha

O comportamento é intencional quando assinatura, payload ou referência server-side é inválida. A aplicação remove o cookie obsoleto e exige uma nova sessão.

## Produção inicia, mas URLs usam HTTP

Não ative `ProxyFix` por tentativa. Determine quantos proxies confiáveis escrevem cada header e configure somente os campos `PROXY_X_*` correspondentes.
