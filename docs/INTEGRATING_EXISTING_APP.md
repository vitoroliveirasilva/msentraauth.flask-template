# Integrando em uma aplicação Flask existente

Não aplique o repositório template por cima de uma aplicação existente. Faça integração incremental:

1. inventarie a factory e extensões atuais;
2. instale `flask-ms-entra-auth` e configure a extensão no `create_app` existente;
3. preserve `base.html`, home, navbar, handlers e `wsgi.py` atuais;
4. mantenha um único `extensions.py` e uma única instância de `CSRFProtect`;
5. integre Redis/session apenas se desejar o mesmo contrato server-side, preservando a ordem de inicialização;
6. não registre a demonstração Graph automaticamente;
7. não sobreponha `/auth/login`, `/auth/callback` ou `/auth/logout`;
8. revise CSP, trusted hosts, proxy e cookies no contexto do sistema existente;
9. rode a matriz de regressão da aplicação.

O template é referência de arquitetura, não um pacote para merge cego.
