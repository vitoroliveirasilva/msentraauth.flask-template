# SEC-02: configuração, segredos, Entra ID e Graph

## Baseline

- Branch: `dev`
- SHA: `5e4d24f3522b6105da3538948db8f21bbbb1c675`
- Relação com `prod`: divergente, 15 commits à frente e 4 atrás
- Merge-base: `f6751f4248265a66c0df3d703ad8c2180c15df52`

## Implementação

1. Segredos por finalidade e key ring de assinatura do SID.
2. Leitura por secret mount com exclusividade entre valor e `_FILE`.
3. Validação criptográfica e independência em produção.
4. URLs, hosts, tenant, callback e limites com fail-fast.
5. Graph global allowlisted, sem redirects, proxy herdado ou `.netrc`.
6. Limite de resposta, DTO, retry e `Retry-After`.
7. Erros distintos e claims challenge sem vazamento ou loop.
8. User-Agent derivado da versão instalada.

## Compatibilidade

Em desenvolvimento e testes, ausência de `SESSION_SIGNING_KEYS` e `WTF_CSRF_SECRET_KEY` mantém o
fallback para `APP_SECRET_KEY`. Produção exige os valores separados. Cookies assinados por uma
chave anterior são aceitos somente enquanto ela estiver no ring e são reemitidos pela chave ativa.

## Bloqueios honestos

- `CFG-013`: secret manager e rotação real dependem da plataforma.
- `ID-011` e `ID-012`: o template detecta o challenge e evita loop, mas não pode repetir OAuth com
  claims sem contrato da extensão.
- `ID-013`: certificado/workload identity depende da extensão.
- `ID-014`: tenant é validado; issuer continua responsabilidade da extensão.
- `ID-016`: firewall e egress dependem da infraestrutura.

## Migração

Antes de produção, gere três materiais independentes: `APP_SECRET_KEY`,
`WTF_CSRF_SECRET_KEY` e a chave ativa de `SESSION_SIGNING_KEYS`. Para rotacionar o SID, adicione a
nova chave no início, mantenha a anterior por no máximo uma vida útil de sessão e depois remova-a.
