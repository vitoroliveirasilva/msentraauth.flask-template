# Migração 1.x para 2.x

A linha 2.x é uma mudança arquitetural. Não há migração segura por simples substituição de arquivos da aplicação 1.x.

Para projetos novos, gere novamente com Copier. Para aplicações reais já derivadas da 1.x, trate-as como aplicações existentes e integre incrementalmente a foundation atualizada. Preserve o código de negócio, compare configurações, migre namespace/cookie conscientemente e planeje invalidação de sessões se trocar chaves ou namespace.
