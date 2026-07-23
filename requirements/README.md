# Dependências reproduzíveis

## Finalidade

Os arquivos `*.constraints.txt` fixam as versões diretas validadas pelo template e são usados por
CI, Docker e scripts locais. Eles impedem que uma execução comum selecione silenciosamente uma nova
versão direta dentro dos intervalos declarados no `pyproject.toml`.

Eles **não são apresentados como lock transitivo completo**. Um lock com hashes exige resolução em
ambiente conectado e confiável para todas as versões Python suportadas e deve ser revisado como uma
mudança de supply chain.

## Regeneração obrigatória

Execute em um checkout limpo, usando Python 3.14, `pip==26.1.2` e `pip-tools` fixados:

```bash
python -m venv .lock-venv
. .lock-venv/bin/activate
python -m pip install --constraint requirements/build.constraints.txt pip==26.1.2 pip-tools==7.6.0
pip-compile --resolver=backtracking --generate-hashes --strip-extras   --output-file=requirements/runtime.lock.txt requirements/runtime.in
pip-compile --resolver=backtracking --generate-hashes --strip-extras   --output-file=requirements/development.lock.txt requirements/development.in
```

No PowerShell, ative `.lock-venv\Scripts\Activate.ps1` e execute os mesmos comandos Python.

## Revisão

1. Não edite locks gerados manualmente.
2. Revise versão, origem, hash, licença e vulnerabilidades de cada mudança.
3. Execute a matriz Python 3.11 a 3.14.
4. Execute `pip-audit` sobre os ambientes instalados pelos locks.
5. Atualize um grupo por PR. Actions, imagens-base e dependências críticas não devem ser agrupadas.
6. Registre a data, o motivo e os digests no relatório da alteração.
7. Preserve o lock anterior para rollback.

## Uso

Enquanto os locks transitivos com hashes não forem gerados e aprovados, use as constraints:

```bash
python -m pip install --constraint requirements/development.constraints.txt -e ".[dev]"
```

Quando os locks existirem, os scripts e workflows devem migrar para:

```bash
python -m pip install --require-hashes -r requirements/development.lock.txt
python -m pip install --no-deps -e .
```

A ausência dos locks transitivos mantém `SC-004` e `SC-005` como `PARCIAL`.
