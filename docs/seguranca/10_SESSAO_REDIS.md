# Sessão Redis, integridade e ciclo de vida

## Envelope

O navegador recebe somente o SID opaco assinado. O Redis armazena um envelope JSON compacto com
`v`, `kid`, `nonce` e `ciphertext`. O conteúdo é protegido por AES-256-GCM; versão, namespace, SID
e `kid` entram como dados autenticados adicionais. O plaintext autenticado contém timestamps,
revisão pseudônima de identidade e o mapa de sessão validado.

`SESSION_PAYLOAD_KEYS` é independente de `APP_SECRET_KEY`, `SESSION_SIGNING_KEYS` e
`WTF_CSRF_SECRET_KEY`. A primeira chave é ativa. As anteriores podem abrir envelopes durante a
rotação e provocam rewrap imediato quando o estado é persistido.

## Ciclo de vida

- `SESSION_LIFETIME_SECONDS`: timeout ocioso e TTL máximo renovável;
- `SESSION_ABSOLUTE_TIMEOUT_SECONDS`: limite desde a criação, nunca renovado por atividade;
- `SESSION_SID_RENEWAL_SECONDS`: intervalo de renovação atômica do SID;
- `SESSION_ACTIVITY_UPDATE_SECONDS`: amortiza escrita de `last_seen_at`;
- `SESSION_CLOCK_SKEW_SECONDS`: tolerância máxima para relógio, limitada a 300 segundos.

A expiração é verificada na leitura e novamente antes da escrita. O cookie expira no limite
absoluto autenticado, e o TTL Redis nunca ultrapassa o menor valor entre idle e tempo absoluto
restante.

## Rotação e concorrência

A rotação carregada executa Lua com duas chaves: confirma que o envelope antigo ainda é exatamente
o lido, cria o novo SID com `NX` e TTL, e só então remove o antigo. Uma requisição concorrente não
pode ressuscitar o SID removido porque gravações comuns continuam condicionais por `NX`/`XX`.

Envelope inválido, expirado ou revogado é removido por compare-and-delete. Se o valor mudar entre
a leitura e a limpeza, a aplicação preserva o estado concorrente e trata o backend como
indisponível, em vez de apagar dados que não analisou.

## Revogação

`revoke_session(sid)` remove imediatamente uma sessão conhecida. `revoke_identity(tenant_id,
object_id)` incrementa uma revisão persistente pseudônima. Sessões vinculadas guardam a revisão
observada e são invalidadas na próxima leitura quando o contador divergir. O fingerprint não
armazena tenant ou object ID em claro.

## Schema e limites

Em modo estrito são aceitos `_permanent`, a chave privada `_msentra_<hash>` da extensão com apenas
`session_id`/`flow_id`, e chaves declaradas em `SESSION_ALLOWED_KEYS`. Valores devem ser JSON
seguro, com limites de profundidade, itens, strings, inteiros, plaintext e envelope. Objetos Python
arbitrários, NaN, infinito, chaves desconhecidas e envelopes com campos extras são rejeitados.

## Redis de produção

O template suporta `rediss://`, validação de certificado/hostname e
`REDIS_CA_CERTS_FILE`. A infraestrutura deve fornecer ACL de menor privilégio, rede privada,
credenciais separadas quando sessão e auth storage forem fisicamente separados, monitoramento e
backup sem material criptográfico. Esses itens permanecem externos até haver evidência real.

## Migração

1. Gere chaves URL-safe independentes com 32 bytes ou mais.
2. Defina namespace único por aplicação e ambiente.
3. Implante todas as réplicas com o mesmo ring antes de ativar a chave nova.
4. Mantenha a chave anterior por pelo menos timeout absoluto + skew + margem.
5. Espere reautenticação das sessões `TaggedJSON` anteriores à SEC-03.
6. Valide login, concorrência, revogação e recuperação antes de remover chaves antigas.
