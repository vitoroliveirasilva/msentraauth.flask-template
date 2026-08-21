# Operação

- `/health/live`: liveness sem dependência de Redis ou sessão.
- `/health/ready`: valida ping e round-trip no Redis usando namespace da aplicação.
- Graph não participa da readiness do core.
- Logs incluem request ID, método, endpoint, status e duração, sem query string/token.
- Rode Gunicorn atrás de TLS/reverse proxy em produção.

Use um namespace e credenciais Redis exclusivos por aplicação e ambiente. Monitore latência, erros e uso de memória do Redis; readiness indisponível deve retirar a instância do balanceador sem reiniciar liveness em loop.

O contêiner roda sem root, com filesystem somente leitura, capabilities removidas e limites explícitos no Compose. Ajuste `PROXY_X_*` apenas à topologia real de proxies confiáveis e mantenha o encerramento gracioso maior que o timeout do balanceador.
