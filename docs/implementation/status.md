# Status de implementação

## Implementado

- Application factory em estrutura `src`;
- Extensão `flask-ms-entra-auth` 1.x como único motor OAuth/OIDC;
- Sessão Redis com SID assinado, payload server-side, TTL e rotação após login;
- Persistência condicional com `NX`/`XX`, impedindo a recriação de SID removido por requisição concorrente;
- Descarte de cookie após assinatura inválida ou payload corrompido, com preservação de referências assinadas sem chave para evitar corrida com rotação;
- Preservação de sessão e resposta `503` durante falhas de leitura, gravação ou exclusão no Redis;
- Substituição sanitizada da resposta quando a sessão não pode ser serializada ou excede o limite;
- Ausência de escrita Redis e cookie para sessões anônimas vazias;
- `Vary: Cookie` em respostas que consultam a sessão;
- `RedisAuthStorage` com TTL e consumo atômico;
- Vínculo local demonstrativo, thread-safe, limitado por capacidade e posterior à rotação bem-sucedida do SID;
- Microsoft Graph `/me` com `$select`, timeouts, retries estritamente limitados, DTO e separação entre falha de rede e erro interno;
- Configuração fail-fast também para instâncias de `AppSettings` injetadas diretamente;
- Produção exige Redis TLS, validação de certificado e hostname, CSRF ativo e modo de teste desabilitado;
- `REDIS_URL` impede que parâmetros de query substituam opções binárias, timeouts, health check e verificações TLS definidas pela aplicação;
- Endereço-base sem query ou backslash e redirect URI limitada e validada conforme o contrato single-tenant do Microsoft Entra;
- Callback legado restrito a caminho estático, não-raiz e sem colisão;
- Base do Microsoft Graph HTTPS e sem query string pré-configurada;
- Interface Jinja, CSRF, CSP, trusted hosts e headers de segurança;
- Access log do Gunicorn sem query string do callback;
- Request ID e logs JSON/texto sanitizados com campos permitidos;
- Static assets e health checks sem carregamento ou persistência de sessão, com liveness independente, readiness por `PING` mais round-trip atômico no Redis e tentativa de limpeza da chave efêmera mesmo em falhas;
- CI com Redis real, inspeção de artefatos e smoke test da imagem não-root;
- Publicação GHCR restrita a tag no histórico de `prod`, com smoke test pré-push e verificação do digest;
- GitHub Release com `wheel` e `sdist` validados e anexados, sem publicação do template no PyPI;
- Gunicorn, Docker e Compose com validações operacionais;
- Scripts locais de validação independentes do diretório corrente e com interrupção confiável na primeira falha;
- Erros HTTP sanitizados preservando headers semânticos obrigatórios, incluindo `Allow` em respostas 405;
- Detecção precisa de placeholders, sem bloquear identificadores ou credenciais legítimos por correspondência parcial;
- Alias de callback com validação autônoma de caracteres de controle e formas inseguras;
- Documentação operacional e troubleshooting.

- Envelope AES-256-GCM versionado para payload de sessão Redis, com HKDF e key ring;
- Timeout ocioso e absoluto, atividade amortizada e renovação periódica atômica do SID;
- Revogação por SID e revisão pseudônima de identidade;
- Schema estrito, limites antes/depois da proteção e limpeza compare-and-delete;
- Namespaces independentes para sessão, revogação e auth storage;
- Suporte a CA privada do Redis por arquivo.

## Limites

Redis ACL, separação física de credenciais, TLS real e backup/restauração ainda exigem evidência externa. O registro local em memória é demonstrativo, autorização de negócio não está incluída e a configuração real de Entra ID, Redis, proxy, secrets, monitoramento e deploy permanece responsabilidade do consumidor.

## Programa de hardening de segurança

O hardening de sessão `SEC-03` foi implementado sobre `dev` no SHA `17187caa25bf4003e017e8532568d3d36c45df62` e permanece `PARCIAL` até a suíte integral e Redis TLS real serem executados.

A fundação documental `SEC-00` foi incorporada à branch `dev`. A `SEC-01` endureceu supply chain
e permanece parcial pelos gates e locks ainda pendentes. A `SEC-02` foi implementada sobre o SHA
`5e4d24f3522b6105da3538948db8f21bbbb1c675`, com segredos por finalidade, key ring do SID,
secret mounts, validações fail-fast e transporte Microsoft Graph restrito. A etapa permanece
`PARCIAL` até a suíte integral ser executada e os controles dependentes da extensão ou da
infraestrutura receberem evidência real. A `SEC-03` também está implementada parcialmente;
`SEC-04` a `SEC-06` permanecem abertas.

Consulte:

- [baseline e divergências;](../seguranca/00_BASELINE_E_ESCOPO.md)
- [matriz de 156 controles;](../seguranca/02_MATRIZ_DE_RISCOS_E_CONTROLES.md)
- [status rastreável;](../seguranca/07_STATUS.md)
- [configuração, Entra e Graph;](../seguranca/09_CONFIGURACAO_ENTRA_GRAPH.md)
- [sessão Redis e ciclo de vida.](../seguranca/10_SESSAO_REDIS.md)

A conclusão do plano funcional em `docs/13_PLANO_MESTRE.md` não implica conclusão do programa
de hardening.
