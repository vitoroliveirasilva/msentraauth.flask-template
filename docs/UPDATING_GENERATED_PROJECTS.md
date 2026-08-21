# Atualizando projetos gerados

Antes de atualizar, confirme que o working tree está limpo e que `.copier-answers.yml` não contém segredos.

```powershell
git status
copier update
```

Depois, revise o diff, resolva conflitos, rode validação completa e registre a atualização do template em um commit separado no repositório da aplicação.
