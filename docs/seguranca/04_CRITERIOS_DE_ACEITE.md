# Critérios de aceite e Definition of Done

## Definition of Done por controle

Um controle só pode ser `CONCLUIDO` quando:

1. implementação ou configuração real existe;
2. teste automatizado ou evidência externa válida existe;
3. a validação foi executada e registrada;
4. fluxos negativos, erros e edge cases foram considerados;
5. arquivos alterados estão mapeados ao controle;
6. documentação diretamente afetada está coerente;
7. risco residual e limitação estão explícitos;
8. nenhum gate foi reduzido;
9. o diff e o ZIP não contêm secrets;
10. o status foi atualizado.

## Gates que não podem ser reduzidos

- Ruff lint e format;
- mypy estrito;
- compilação dos módulos;
- pytest com 100% de linhas e branches;
- Bandit e auditoria de dependências;
- build, `twine check` e inspeção de artefatos;
- `pip check` em ambiente limpo;
- Redis real;
- validação do Compose;
- build e smoke da imagem não-root.

Etapas podem adicionar gates, mas não remover ou tornar opcionais os existentes sem ADR e
justificativa de segurança.

## Critérios específicos da SEC-00

- [x] Nenhum arquivo de runtime, dependência, workflow ou contêiner alterado.
- [x] SHA de `dev` registrado.
- [x] Relação `dev`/`prod` registrada sem sincronização.
- [x] 156 controles presentes e sem IDs duplicados.
- [x] Cada controle possui etapa, prioridade, responsabilidade, estado e evidência mínima.
- [x] Fronteiras entre template, extensão, consumidor e ambiente externo documentadas.
- [x] Divergências entre documentação, código e operação enumeradas.
- [x] Namespace `SEC` evita colisão com o plano funcional antigo.
- [x] Política de ADR e risco residual definida.
- [x] Padrão de patch e commit definido.
- [ ] Gates completos do repositório executados no ambiente local deste patch.

O último item permanece não comprovado nesta entrega porque o ambiente de geração não conseguiu
obter um checkout local completo pelo host GitHub. A alteração é exclusivamente Markdown, e
validações documentais foram executadas, mas isso não substitui `scripts/validate.*`.

## Bloqueadores

A entrega deve falhar quando houver:

- segredo ou dado pessoal;
- cobertura reduzida;
- teste removido;
- controle marcado concluído sem evidência;
- arquivo sem relação com a etapa;
- patch sobre SHA incompatível;
- sincronização não autorizada de branches;
- dependência da extensão ocultada;
- configuração externa declarada como concluída por documentação;
- alteração funcional na `SEC-00`.

## Risco residual da SEC-00

A etapa reduz risco de execução desordenada, mas não corrige vulnerabilidades técnicas. Todos os
controles de `SEC-01` a `SEC-06` permanecem `PENDENTE`, `PARCIAL`,
`BLOQUEADO_EXTENSAO` ou `BLOQUEADO_EXTERNO`.
