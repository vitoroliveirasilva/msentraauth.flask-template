# Deploy e operação

## Ordem

1. Disponibilizar `flask-ms-entra-auth` 1.x no índice configurado;
2. Configurar App Registration, secrets e redirect URI;
3. Provisionar Redis privado, autenticado, persistente e preferencialmente com TLS;
4. Construir a imagem do template;
5. Executar atrás de proxy HTTPS conhecido;
6. Configurar corretamente `PROXY_X_*`;
7. Validar `/health/live` e `/health/ready`;
8. Executar smoke test de login, perfil Graph e logout;
9. Ativar métricas, alertas, backup e rotação de credenciais.

## Contêiner

O Dockerfile usa build multi-stage, Python slim, Gunicorn e UID/GID não-root. O access log utiliza somente o caminho da requisição, sem query string, para não registrar parâmetros do callback OAuth.

O Compose adiciona Redis persistente, health checks, reinício, filesystem read-only para a aplicação, `no-new-privileges`, remoção de capabilities da aplicação e rotação básica de logs.

## Limites do Compose

O Compose é referência local e de homologação. Ele não substitui:

- Redis gerenciado ou clusterizado;
- TLS e certificados de produção;
- Secret manager;
- Backup e restauração testados;
- Limites e autoscaling do orquestrador;
- Observabilidade centralizada;
- WAF, rate limiting ou política de egress;
- Estratégia de rollout e rollback.
