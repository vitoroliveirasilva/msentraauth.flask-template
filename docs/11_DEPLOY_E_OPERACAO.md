# Deploy e operação

## Servidor

Produção usa WSGI como Gunicorn em Linux ou servidor equivalente (o servidor de desenvolvimento não é opção de produção).

## Topologia

```text
Cliente -> Proxy HTTPS -> WSGI Flask -> Redis
                              |
                              +-> Entra ID
                              +-> Graph
```

## Proxy

`ProxyFix` somente quando necessário e com número exato de proxies confiáveis (hosts devem ser validados).

## Redis

- Privado;
- Autenticação;
- TLS quando necessário;
- Timeout curto;
- TTL;
- Sem exposição pública;
- Monitoramento de memória.

## Container

- Imagem slim;
- Usuário não root;
- Build em estágios;
- Sem `.env`;
- Sem `.git`;
- Health check;
- Dependências reproduzíveis;
- Scan de vulnerabilidade;
- Filesystem read-only quando possível.

## Timeouts

Graph e Redis devem falhar antes do timeout do worker e proxy e load balancer precisam de valores coerentes.
