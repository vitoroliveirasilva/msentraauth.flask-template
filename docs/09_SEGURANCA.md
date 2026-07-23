# Segurança

## Configuração e identidade

- Segredos criptográficos separados para Flask, SID e CSRF;
- key ring de SID com chave ativa e chaves anteriores de verificação;
- suporte a secret mounts por `_FILE`;
- produção rejeita segredo fraco, reutilizado, DEBUG, TESTING, HTTP, Redis sem TLS e CSRF desligado;
- hosts exatos, URL-base origin-only e callback estático sem query;
- single-tenant explícito;
- Graph restrito ao endpoint global oficial.

## Microsoft Graph

- bearer enviado somente ao host aprovado;
- redirects e `trust_env` desabilitados;
- TLS obrigatório;
- corpo, DTO, retries e `Retry-After` limitados;
- 401, 403, 429, 5xx e claims challenge tratados separadamente;
- claims não são registradas ou refletidas.

## Sessão

A SEC-02 altera somente a chave usada para assinar o SID e sua rotação. O payload Redis continua
no formato existente. MAC/AEAD do payload, timeout absoluto, revogação global e rotação atômica do
SID pertencem à SEC-03.

## Limites externos

Secret manager, política de egress, configuração real do tenant, certificado/workload identity e
suporte completo a CAE exigem evidência externa ou alteração da extensão. Documentação não marca
esses controles como concluídos.
