# Fluxos da aplicação

## Login

`/auth/login` inicia o fluxo pela extensão. O state e a transação ficam no Redis e o cookie recebe somente referência server-side.

## Callback

A extensão consome a transação uma única vez, valida o retorno MSAL, cria `Identity` e executa o hook local antes de persistir a sessão.

## Perfil

`/profile` exige autenticação, solicita token silencioso server-side e chama `GET /me` com `$select` limitado.

## Logout

`POST /auth/logout` remove fluxo, identidade e token cache da sessão atual. O logout local não encerra todas as sessões Microsoft.
