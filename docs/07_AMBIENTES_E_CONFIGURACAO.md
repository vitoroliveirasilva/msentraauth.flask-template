# Ambientes e configuração

- A fonte de referência é `.env.example`;
- Nenhum valor sensível possui padrão operacional e placeholders causam falha de inicialização;
- Instâncias de `AppSettings` construídas diretamente passam pelas mesmas invariantes antes de criar o cliente Redis ou configurar o Flask.

## Desenvolvimento

Loopback HTTP, cookie não-secure e Redis local são permitidos. CSRF pode ser desligado somente em desenvolvimento controlado ou testes automatizados.

## Produção

- `APP_BASE_URL` e redirect URI HTTPS na mesma origem, sem controles, backslash ou query no endereço-base;
- Host da aplicação presente em `APP_TRUSTED_HOSTS`;
- `SESSION_COOKIE_SECURE=true`;
- Secret de sessão com pelo menos 32 caracteres aleatórios;
- Client secret com pelo menos 24 caracteres;
- `User.Read` em `MS_ENTRA_SCOPES`;
- `REDIS_TLS_REQUIRED=true` e URI `rediss://`;
- `TESTING=false` e `WTF_CSRF_ENABLED=true`;
- Timeouts positivos e finitos, sem `NaN` ou infinito;
- Portas válidas e URLs sem fragmentos ou credenciais onde não permitidas;
- `GRAPH_BASE_URL` HTTPS sem query string, pois o cliente acrescenta o recurso e os parâmetros OData;
- Redirect URI com no máximo 256 caracteres, sem controles, caracteres não suportados ou domínio internacionalizado;
- Callback legado com caminho estático, não-raiz e sem sintaxe dinâmica de rota.

`ProxyFix` permanece desativado até que cada hop confiável seja declarado por `PROXY_X_*`. Valores acima de cinco são rejeitados para evitar configuração acidentalmente ampla.

- Configuração inválida gera `SettingsError` antes de servir requisições;
- Parâmetros numéricos do Gunicorn também falham cedo quando estão fora dos limites operacionais aceitos.
