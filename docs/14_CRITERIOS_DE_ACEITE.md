# Critérios de aceite

## Aplicação

- Factory;
- Config fail-fast;
- Debug não hardcoded;
- WSGI;
- Rotas organizadas.

## Extensão

- Dependência normal;
- Nenhum fluxo MSAL duplicado;
- Identity sem token;
- Reautenticação controlada.

## Sessão

- Server-side;
- Cookies seguros em produção;
- ID regenerado;
- Logout limpa estado;
- Múltiplos workers.

## Graph

- Timeout;
- DTO;
- Status tratados;
- `$select`;
- Token fora de logs.

## Segurança

- State inválido rejeitado;
- Ppen redirect rejeitado;
- Logout POST com CSRF;
- Headers;
- Secrets externos;
- Scanners sem crítico não aceito.

## Qualidade

- Testes e cobertura;
- Lint e typing;
- Docs;
- Imagem validada;
- Health;
- Operação documentada.