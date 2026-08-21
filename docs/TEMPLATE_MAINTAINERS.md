# Mantenedores do template

O repositório raiz contém somente o generator e suas validações. A aplicação distribuída vive em `template/`; não mantenha uma segunda aplicação em `src/` na raiz.

Toda mudança deve ser exercitada pelo Copier oficial em pelo menos três renderizações: projeto sem Graph, projeto com Graph e projeto cujo package difere do slug. Valide compilação, Ruff, mypy, testes com cobertura, scanner de resíduos e build do contêiner. Mudanças em sessão, envelope, auth storage, callback, secrets, CSP, proxy ou headers são security-critical e exigem regressão específica.

Arquivos `.jinja` são processados pelo Copier. Templates HTML de runtime não têm esse sufixo e devem conter Jinja do Flask diretamente, sem blocos `raw` literais.
