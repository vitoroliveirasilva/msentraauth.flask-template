# Ambientes e configuração

A fonte de referência é `.env.example`. Nenhum valor sensível possui padrão operacional e placeholders causam falha de inicialização.

## Desenvolvimento

Loopback HTTP, cookie não-secure e Redis local são permitidos. CSRF pode ser desligado somente em testes automatizados.

## Produção

- `APP_BASE_URL` e redirect URI HTTPS na mesma origem;
- Host da aplicação presente em `APP_TRUSTED_HOSTS`;
- `SESSION_COOKIE_SECURE=true`;
- Scret de sessão com pelo menos 32 caracteres aleatórios;
- Client secret com pelo menos 24 caracteres;
- `User.Read` em `MS_ENTRA_SCOPES`;
- `REDIS_TLS_REQUIRED=true` e URI `rediss://`;
- Portas válidas e URLs sem fragmentos ou credenciais onde não permitidas.

`ProxyFix` permanece desativado até que cada hop confiável seja declarado por `PROXY_X_*`. Valores acima de cinco são rejeitados para evitar configuração acidentalmente ampla.

Configuração inválida gera `SettingsError` antes de servir requisições.
