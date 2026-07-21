# Contribuindo

## Ambiente

```bash
python -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev]"
```

Durante desenvolvimento conjunto, instale primeiro o repositório irmão:

```bash
venv/bin/python -m pip install -e ../msentraauth.flask-extension
venv/bin/python -m pip install -e ".[dev]"
```

Em produção e na CI normal, a extensão vem do índice como `flask-ms-entra-auth>=1.0,<2`.

## Gate obrigatório

```bash
./scripts/validate.sh
```

No PowerShell:

```powershell
.\scripts\validate.ps1
```

O gate inclui lint, formatação, tipagem, compilação, testes com cobertura integral, Bandit, auditoria de dependências, build, Twine, inspeção de artefatos e `pip check`.

## Fronteiras

- Não duplique OAuth, callback, state, token cache ou identidade no template;
- Mudanças genéricas de autenticação pertencem à extensão;
- Redis, Graph, interface, vínculo local e operação permanecem neste projeto;
- Não registre tokens, auth codes, state, SID, claims completas ou respostas brutas do Graph.