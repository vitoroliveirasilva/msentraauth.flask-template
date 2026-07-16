# Ambientes e configuração

## Development

- HTTP localhost permitido;
- Logs legíveis;
- Redis local;
- Debug controlado pelo comando Flask, nunca hardcoded.

## Testing

- Config isolada;
- Credenciais fictícias;
- MSAL e Graph mockados;
- Storage descartável;
- CSRF configurado conforme tipo de teste.

## Production

- HTTPS;
- Secret manager;
- Redis privado;
- Cookies seguros;
- Debug desligado;
- WSGI;
- Hosts confiáveis;
- Proxy configurado com contagens exatas.

# Validação fail-fast

A aplicação deve recusar inicialização quando faltar variável obrigatória, houver placeholder, URI inválida, secret curto ou configuração insegura de produção.

# Fonte de configuração

A factory recebe settings ou carrega ambiente e não deve importar objeto global configurado em import time.

# Variáveis

O catálogo está em [`.env.example`](../.env.example).

- Variáveis específicas da extensão usam `MS_ENTRA_`;
- variáveis da aplicação usam `APP_`, `SESSION_`, `REDIS_`, `GRAPH_` ou nomes claros.

# Proibição

- Fallback silencioso para produção;
- Interpretar string `false` como verdadeira;
- Confiar em `X-Forwarded-*` sem proxy conhecido;
- Construir redirect URI a partir de Host não validado.
