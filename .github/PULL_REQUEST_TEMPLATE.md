## Resumo

Descreva de forma objetiva o problema resolvido ou a evolução entregue.

## Tipo da alteração

- [ ] Nova funcionalidade
- [ ] Correção
- [ ] Refatoração
- [ ] Documentação
- [ ] Testes ou qualidade
- [ ] Segurança
- [ ] Infraestrutura, container ou deploy
- [ ] Release

## Principais mudanças

- 

## Fronteira entre template e extensão

- [ ] A mudança pertence ao template Flask.
- [ ] Não duplica OAuth, callback, `state`, token cache ou identidade já fornecidos pela extensão.
- [ ] Mudanças genéricas de autenticação foram direcionadas ao repositório `msentraauth.flask-extension`.
- [ ] Não se aplica, com justificativa abaixo.

Justificativa, quando necessária:

## Como validar

Linux ou macOS:

```bash
./scripts/validate.sh
```

PowerShell:

```powershell
.\scripts\validate.ps1
```

Inclua também cenários manuais, URLs, variáveis de ambiente sanitizadas ou fluxos relevantes:

## Impactos

- [ ] Altera variáveis de ambiente ou configuração pública.
- [ ] Altera login, callback, logout ou comportamento de sessão.
- [ ] Altera integração com Redis ou Microsoft Graph.
- [ ] Altera vínculo ou autorização local.
- [ ] Altera headers, cookies ou segurança do navegador.
- [ ] Altera Docker, imagem GHCR ou operação em produção.
- [ ] Exige ação de migração após o deploy.
- [ ] Não possui impacto operacional adicional.

## Segurança e privacidade

- [ ] Nenhum segredo, token, cookie, código de autorização ou dado pessoal foi incluído.
- [ ] Logs e mensagens de erro não expõem payloads do Entra ID ou Microsoft Graph.
- [ ] Entradas externas continuam validadas e tratadas defensivamente.
- [ ] Alterações de sessão, cookies e headers foram revisadas quanto à segurança.
- [ ] Vulnerabilidades foram comunicadas pelo canal privado, quando aplicável.

## Testes e qualidade

- [ ] `./scripts/validate.sh` ou `.\scripts\validate.ps1` foi executado com sucesso.
- [ ] Os testes cobrem o comportamento novo ou alterado.
- [ ] A cobertura integral exigida pelo projeto foi preservada.
- [ ] Lint, formatação, tipagem, Bandit, auditoria e build passaram.
- [ ] A documentação foi atualizada quando necessário.

## Checklist final

- [ ] A alteração está baseada na branch `dev` atualizada.
- [ ] O escopo do PR é pequeno, coeso e revisável.
- [ ] Não há arquivos temporários, credenciais ou alterações fora do escopo.
- [ ] Commits e título seguem o padrão do projeto.
- [ ] Concordo em seguir o código de conduta do projeto.
