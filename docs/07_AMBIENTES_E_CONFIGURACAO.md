# Ambientes e configuração

A fonte executável é `.env.example`. Configurações inválidas geram `SettingsError` antes da
aplicação servir requisições. Instâncias de `AppSettings` construídas diretamente passam pelas
mesmas invariantes.

## Segredos

Segredos suportados por arquivo:

- `APP_SECRET_KEY_FILE`;
- `SESSION_SIGNING_KEYS_FILE`;
- `WTF_CSRF_SECRET_KEY_FILE`;
- `MS_ENTRA_CLIENT_SECRET_FILE`;
- `REDIS_URL_FILE`.

O caminho deve ser absoluto e apontar para arquivo UTF-8 regular de até 16 KiB. A variável direta
e sua variante `_FILE` não podem coexistir.

Em produção:

- `APP_SECRET_KEY`, `WTF_CSRF_SECRET_KEY` e cada chave de `SESSION_SIGNING_KEYS` devem ser base64
  URL-safe e codificar pelo menos 32 bytes;
- todos os segredos devem ser independentes;
- a primeira chave do ring assina novos cookies e até quatro chaves anteriores verificam cookies
  durante uma janela controlada de rotação;
- `DEBUG=false`, `TESTING=false` e `WTF_CSRF_ENABLED=true` são obrigatórios.

Desenvolvimento preserva compatibilidade: ring e chave CSRF vazios usam `APP_SECRET_KEY`.

## URLs e hosts

- `APP_BASE_URL` contém somente a origem, sem path, query, fragmento ou credenciais;
- `APP_TRUSTED_HOSTS` aceita hosts exatos, sem `*` ou padrões por sufixo;
- redirect URI usa a mesma origem e um path estático não ambíguo;
- Redis usa `rediss://` quando TLS é obrigatório;
- opções Redis controladas pela aplicação não podem ser sobrescritas pela query;
- `GRAPH_BASE_URL` aceita somente `https://graph.microsoft.com/v1.0` nesta versão.

## Limites

Timeouts, TTLs, retries, tamanho da resposta Graph, health interval e proxy hops possuem limites
superiores. `NaN`, infinito, zero onde proibido e números excessivos interrompem o startup.

## Produção

Além das regras acima, produção exige HTTPS, cookie Secure, Redis TLS, client ID UUID e tenant
específico. Configuração soberana ou multi-cloud só deve ser habilitada quando a extensão possuir
contrato de authority/issuer correspondente.

## Sessão Redis protegida

Produção exige `SESSION_PAYLOAD_KEYS` independente e `SESSION_NAMESPACE` único. Configure também
`SESSION_ABSOLUTE_TIMEOUT_SECONDS`, `SESSION_SID_RENEWAL_SECONDS`,
`SESSION_ACTIVITY_UPDATE_SECONDS`, `SESSION_CLOCK_SKEW_SECONDS` e `SESSION_SCHEMA_STRICT=true`.
Chaves de aplicação adicionais na sessão devem ser declaradas em `SESSION_ALLOWED_KEYS`; a metadata
privada da extensão é aceita por contrato próprio.

`REDIS_CA_CERTS_FILE` aponta para uma CA privada quando o serviço TLS não usa a cadeia pública. O
arquivo deve ser absoluto, regular e legível. Não desabilite hostname ou validação de certificado.
