# Contribuindo

## Branches

- `dev`: desenvolvimento;
- `prod`: estado estável.

## Princípios

- O template consome a extensão;
- Não duplicar fluxo MSAL;
- Preservar escopo da etapa;
- Testes acompanham comportamento;
- Documentação em português;
- Código e identificadores podem seguir convenções técnicas em inglês.

## Ambiente pretendido

```bash
python -m venv venv
source venv\scripts\activate
python -m pip install -e ".[dev]"
```

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Vulnerabilidades seguem [`SECURITY.md`](SECURITY.md) e não devem ser discutidas publicamente antes de correção.
