# Solução de problemas

## Pacote da extensão não encontrado

Confirme acesso ao PyPI e instale `flask-ms-entra-auth>=1.0,<2`. Para desenvolvimento conjunto, instale o repositório irmão em modo editável.

## `SettingsError`

Revise placeholders, tamanho dos secrets, HTTPS de produção, `APP_BASE_URL` sem query ou backslash, origem e formato do redirect, limite de 256 caracteres, host confiável, porta, `User.Read`, booleanos, timeouts finitos, `GRAPH_BASE_URL` sem query, `TESTING=false`, CSRF ativo e URI Redis com TLS em produção.

## `/health/ready` retorna 503

Confirme `REDIS_URL`, DNS, porta, TLS, autenticação, CA, firewall e permissões de `PING`, gravação e Lua/EVAL no Redis. O endpoint executa um round-trip efêmero e não testa Microsoft Graph.

## Aplicação retorna 503 de sessão

Falhas de leitura, gravação ou exclusão no Redis bloqueiam temporariamente a operação e enviam `Retry-After: 5`. O cookie não é removido e respostas de sucesso ou redirecionamento são substituídas por `503`, evitando confirmar uma alteração de sessão que não foi persistida. Corrija a conectividade e repita a requisição.

## Callback ausente ou consumido

Verifique TTL, namespace, compartilhamento do Redis entre workers e suporte atômico. Não reutilize o mesmo callback.

## Graph retorna 401/403

Confirme consentimento de `User.Read`, conta do cache e App Registration. Refaça o login quando necessário e não registre a resposta bruta.

## Login retorna 400 localmente

Use host permitido, redirect exatamente registrado e `APP_BASE_URL` coerente com o navegador. Uma requisição com host não confiável recebe `400` simples e não renderiza detalhes.

## Cookie desaparece após uma falha

A remoção é intencional quando a assinatura é inválida ou o payload está corrompido. Uma referência ainda assinada cuja chave Redis não existe é tratada como sessão anônima sem apagar o cookie na resposta vazia, evitando corrida com a rotação de SID. Indisponibilidade transitória do Redis também preserva o cookie.

## Produção inicia, mas URLs usam HTTP

Não ative `ProxyFix` por tentativa. Determine quantos proxies confiáveis escrevem cada header e configure somente os campos `PROXY_X_*` correspondentes.
