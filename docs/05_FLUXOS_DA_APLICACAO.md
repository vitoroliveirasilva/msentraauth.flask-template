# Fluxos da aplicação

## Acesso inicial

Usuário anônimo acessa rota protegida, é direcionado à entrada e inicia login pela extensão.

## Autenticação

```text
GET /auth/login
  -> extensão cria flow
  -> redireciona ao Entra
  -> callback
  -> extensão valida flow/state
  -> hook vincula usuário local
  -> sessão é regenerada
  -> destino local
```

## Perfil

```text
GET /perfil
  -> rota protegida
  -> extensão adquire token silencioso
  -> GraphClient chama /me com timeout
  -> DTO valida resposta
  -> template renderiza campos permitidos
```

## Token expirado

A extensão tenta cache e refresh silencioso. Se não houver token utilizável, o usuário é direcionado a nova autenticação com mensagem segura.

## Graph indisponível

A aplicação exibe página temporária, registra request ID e não invalida a sessão automaticamente em falha `5xx`.

## Logout

```text
POST /auth/logout
  -> CSRF
  -> limpa usuário, sessão e cache
  -> logout Microsoft opcional
  -> página de saída
```

## Usuário autenticado, mas não autorizado

Autenticação e autorização são diferentes, logo, o hook local pode negar acesso com `403` sem classificar a credencial Microsoft como inválida.
