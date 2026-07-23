# ADR 012: envelope autenticado e ciclo de vida da sessão

## Estado

Aceita em 2026-07-23 para a `SEC-03`.

## Contexto

O cookie já continha somente um SID assinado, porém o payload Redis era `TaggedJSON` em claro,
sem integridade própria, timeout absoluto, renovação periódica ou revogação por identidade. A
rotação removia a chave antiga antes de o novo estado existir, criando uma janela entre operações.

## Decisão

1. Persistir novos payloads em envelope JSON versionado protegido por AES-256-GCM.
2. Derivar a chave AEAD por HKDF-SHA256 a partir de `SESSION_PAYLOAD_KEYS`, domínio separado das
   chaves de Flask, CSRF e assinatura do SID.
3. Vincular versão, namespace, SID e `kid` como AAD.
4. Autenticar `issued_at`, `last_seen_at`, `sid_rotated_at`, revisão pseudônima do usuário e dados.
5. Aceitar um ring ordenado: a primeira chave grava; anteriores somente leem e provocam rewrap.
6. Aplicar timeout ocioso e absoluto, skew limitado, atualização de atividade amortizada e
   renovação periódica do SID.
7. Rotacionar SID com Lua em uma única operação Redis: comparar o envelope antigo, criar o novo
   com `NX` e TTL, então remover o antigo.
8. Oferecer revogação de SID e revogação global por identidade por contador persistente.
9. Isolar namespaces de sessão, revogação e storage da extensão.
10. Rejeitar schema, tipos, profundidade, contagem de itens, tamanho e versões desconhecidas.

## Compatibilidade e migração

Não existe leitura automática do payload `TaggedJSON` legado. No primeiro acesso após a mudança,
sessões antigas são tratadas como inválidas, removidas por compare-and-delete e o usuário precisa
autenticar novamente. O corte evita um parser dual permanente e uma janela de downgrade.

Cookies assinados por chaves anteriores continuam aceitos enquanto a chave permanecer no ring.
Payloads lidos por chave AEAD anterior são regravados pela chave ativa. Uma chave antiga só deve
ser removida após a soma do timeout absoluto, skew máximo e margem operacional.

## Consequências

- Comprometimento de leitura do Redis deixa de expor conteúdo da sessão.
- Escrita no Redis não permite forjar payload válido sem a chave AEAD.
- Indisponibilidade ou estado ambíguo falha fechado para autenticação, sem confirmar sucesso falso.
- `cryptography` passa a ser dependência de runtime.
- ACL, TLS real, separação física e backup seguro continuam exigindo evidência externa.
