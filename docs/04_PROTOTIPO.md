# Protótipo e migração

Fluxos antigos ou utilitários MSAL duplicados não devem ser reintroduzidos.

Migrações de aplicações existentes devem ocorrer incrementalmente: configuração, extensão, Redis, hooks locais, Graph e por fim interface/operação. Cada passo precisa manter testes de login, callback, logout e falha de storage.
