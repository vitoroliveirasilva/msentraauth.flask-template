# Solução de problemas

## Redirect URI incompatível

Confirmar protocolo, host, porta, caminho e barra final no App Registration e na variável local.

## Secret inválido ou expirado

Criar nova credencial, atualizar secret manager e revogar a anterior (não registrar o valor em log).

## Login retorna state inválido

Verificar persistência da sessão, cookies, Redis, domínio, SameSite, proxy e múltiplas instâncias.

## Usuário perde login entre requests

Verificar se sessão é compartilhada, TTL, cookie, chave secreta consistente e balanceador.

## Graph retorna 401

Solicitar token novamente pela extensão e não reutilizar token armazenado em usuário.

## Graph retorna 403

Verificar scope, consentimento e políticas do tenant.

## Graph retorna 429

Respeitar `Retry-After`, reduzir chamadas e evitar retry agressivo.

## Callback funciona localmente e falha em produção

Verificar HTTPS, proxy, Host, redirect URI, cookies Secure e headers encaminhados.

## Redis indisponível

Readiness deve falhar e logs devem mostrar evento sanitizado. Verificar rede, DNS, TLS, credencial e limites.

## Não usar como correção

- Desligar validação de state;
- Remover Secure em produção;
- Logar token;
- Usar `verify=False`;
- Aumentar timeout indefinidamente;
- Ativar debug público.
