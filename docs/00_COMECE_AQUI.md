# Comece aqui

Este repositório é a fonte de um **generator Copier**. Ele gera uma aplicação Flask independente com Microsoft Entra ID, sessão Redis server-side e baseline de segurança.

## Nova aplicação

Execute Copier fora deste diretório. A pasta de destino criada pelo Copier é o projeto que você abre no VS Code e versiona. Adicione features em `src/<package_name>/blueprints/` e serviços de negócio fora da infraestrutura de autenticação/sessão.

## Aplicação existente

Não copie o template sobre a aplicação. Siga [INTEGRATING_EXISTING_APP.md](INTEGRATING_EXISTING_APP.md) e incorpore apenas as partes necessárias.

## Customização

- Home: `templates/main/home.html`
- Navbar: `templates/components/navbar.html`
- Login visual: `templates/auth/login.html`
- CSS: `static/css/app.css`
- JS: `static/js/app.js`
- Rotas reservadas da extensão: `/auth/login`, `/auth/callback`, `/auth/logout`
- Health: `/health/live` e `/health/ready`

Graph é opcional. `User.Read` permanece como escopo mínimo da extensão; sem `include_graph_example`, a rota `/profile`, o cliente Graph e seus testes não são gerados.

Para atualização futura, mantenha `.copier-answers.yml` versionado e use `copier update` com working tree limpa.
