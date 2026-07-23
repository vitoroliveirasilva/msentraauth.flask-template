# Checklist de configurações externas do hardening

Estes itens não podem ser concluídos apenas com arquivos no repositório.

## GitHub

- [ ] Branch `dev` protegida conforme o fluxo de desenvolvimento.
- [ ] Branch `prod` protegida contra push direto.
- [ ] Tags/releases protegidas e imutáveis.
- [ ] Actions permitidas por allowlist e SHA.
- [ ] `GITHUB_TOKEN` com padrão read-only.
- [ ] Environments para publicação com aprovação.
- [ ] Secret scanning e push protection.
- [ ] Code scanning.
- [ ] Dependency graph e Dependabot alerts.
- [ ] Private vulnerability reporting.
- [ ] CODEOWNERS e revisão para workflows/segurança.
- [ ] Cache e artifacts com retenção mínima.

## Microsoft Entra ID

- [ ] Aplicação single-tenant confirmada.
- [ ] Redirect URIs exatas por ambiente.
- [ ] Sem wildcard de redirect.
- [ ] Permissão delegada mínima `User.Read`.
- [ ] Consentimento revisado.
- [ ] Certificado ou credencial federada em produção, quando suportado.
- [ ] Client secret com expiração curta apenas como fallback controlado.
- [ ] Procedimento de rotação.
- [ ] Logs de sign-in monitorados.
- [ ] Conditional Access e CAE avaliados.
- [ ] Tenant/issuer/cloud alinhados ao Graph.

## Redis

- [ ] Endpoint privado.
- [ ] TLS com validação de certificado e hostname.
- [ ] CA gerenciada.
- [ ] ACL por usuário e namespace.
- [ ] Sem comandos administrativos desnecessários.
- [ ] Backup criptografado.
- [ ] Restore testado.
- [ ] Monitoramento de latência, memória, evictions e erros.
- [ ] Política de expiração e capacidade.
- [ ] Rotação de credenciais.
- [ ] Acesso administrativo auditado.

## Rede e proxy

- [ ] Entrada permitida somente pelo proxy/WAF.
- [ ] Acesso direto ao Gunicorn bloqueado.
- [ ] Hops e headers forwarded correspondem à topologia.
- [ ] TLS moderno e certificado válido.
- [ ] Egress restrito a Entra, Graph, Redis e dependências necessárias.
- [ ] DNS e proxy corporativo controlados.
- [ ] Rate limiting de borda.
- [ ] Limites de request no proxy.
- [ ] Health endpoints acessíveis apenas pelos componentes necessários.

## Secrets e operação

- [ ] Secret manager.
- [ ] Workload identity.
- [ ] Secrets não persistem em imagem, logs ou `.env`.
- [ ] Rotação emergencial testada.
- [ ] Inventário de dados.
- [ ] Retenção e descarte.
- [ ] Alertas e runbooks.
- [ ] Plano de incidente.
- [ ] Responsáveis e contatos.

## Regra de evidência

Cada item externo precisa registrar:

- ambiente e plataforma;
- data;
- responsável;
- configuração esperada;
- evidência observável;
- teste executado;
- resultado;
- limitação;
- plano de rollback ou rotação.

Até isso ocorrer, o estado continua `BLOQUEADO_EXTERNO`.
