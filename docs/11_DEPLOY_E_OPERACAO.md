# Deploy e operação

## Ordem

1. Disponibilizar `flask-ms-entra-auth` 1.x no índice configurado;
2. Configurar App Registration, secrets e redirect URI;
3. Provisionar Redis privado, autenticado, persistente e com TLS em produção;
4. Construir a imagem do template ou utilizar a imagem versionada do GHCR;
5. Executar atrás de proxy HTTPS conhecido;
6. Configurar corretamente `PROXY_X_*`;
7. Validar `/health/live` e `/health/ready`;
8. Executar smoke test de login, perfil Graph e logout;
9. Ativar métricas, alertas, backup e rotação de credenciais.

## Contêiner

O Dockerfile usa build multi-stage, Python slim, Gunicorn e UID/GID não-root. O access log utiliza somente o caminho da requisição, sem query string, para não registrar parâmetros do callback OAuth.

O Compose adiciona Redis persistente, health checks, reinício, filesystem read-only para a aplicação, `no-new-privileges`, remoção de capabilities da aplicação e rotação básica de logs. A CI valida o Compose, confirma o UID `10001` e executa a imagem final contra Redis real.

As variáveis numéricas do Gunicorn são validadas na inicialização. Valores não inteiros, portas inválidas, contagens negativas ou limites excessivos interrompem o processo com uma mensagem que identifica a variável incorreta.

## GitHub Container Registry

A publicação de uma Release dispara o workflow `Publish container`. A versão da tag deve corresponder ao campo `project.version` do `pyproject.toml` e o checkout precisa apontar exatamente para o commit dessa tag.

A execução manual aceita somente a branch `prod` ou a própria tag versionada. Mesmo nesses casos, o workflow compara o `HEAD` com o commit da tag antes de autenticar e publicar, evitando imagens sem correspondência com uma versão imutável.

A imagem é publicada em:

```text
ghcr.io/vitoroliveirasilva/msentraauth.flask-template
```

Para a versão `1.0.0`, as tags produzidas são:

```text
1.0.0
1.0
1
latest
sha-<commit>
```

A imagem inclui metadados OCI de versão e revisão, SBOM e proveniência de build. O workflow publica variantes para `linux/amd64` e `linux/arm64` e executa um smoke test contra Redis real antes de concluir.

Download:

```bash
docker pull ghcr.io/vitoroliveirasilva/msentraauth.flask-template:1.0.0
```

O contêiner não inclui Redis nem credenciais. A execução exige as mesmas variáveis documentadas em `.env.example` e um Redis acessível pela URL configurada em `REDIS_URL`.

A primeira publicação cria o Package com visibilidade privada por padrão. Após validar a imagem, altere uma única vez em **Package settings → Change visibility → Public**. Essa mudança é irreversível no GitHub.

## Publicação e recuperação

O fluxo recomendado é:

1. Aprovar a CI da branch `prod`;
2. Criar uma Release com tag `v<versão>` apontando para o commit aprovado;
3. Aguardar a validação da fonte, a publicação e o smoke test da imagem;
4. Tornar o Package público na primeira publicação;
5. Validar o pull pelo digest exibido no resumo do workflow.

Em rollback, use uma tag de versão anterior ou, para máxima imutabilidade, o digest OCI registrado pelo workflow. A tag `latest` representa apenas a Release estável mais recente e não deve substituir pinagem de versão em produção.

## Limites do Compose

O Compose é referência local e de homologação. Ele não substitui:

- Redis gerenciado ou clusterizado;
- TLS e certificados de produção;
- Secret manager;
- Backup e restauração testados;
- Limites e autoscaling do orquestrador;
- Observabilidade centralizada;
- WAF, rate limiting ou política de egress;
- Estratégia de rollout e rollback.
