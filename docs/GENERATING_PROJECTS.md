# Gerando projetos

Use uma tag estável para aplicações reais. `dev` serve para testar o generator em desenvolvimento.

```powershell
cd C:\repos
pipx install "copier==9.17.0"
copier copy --vcs-ref v2.0.0 gh:vitoroliveirasilva/msentraauth.flask-template sistema-processos
cd sistema-processos
```

`project_slug` identifica repositório/serviço; `package_name` identifica imports Python. Eles podem ser diferentes. Valores deriváveis, como distribution name, namespace Redis e cookie, são gerados automaticamente.

Para testar mudanças locais do generator, use `copier copy --trust . <destino-vazio>`. O destino deve estar vazio; não gere dentro do repositório-fonte.
