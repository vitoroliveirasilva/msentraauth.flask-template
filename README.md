# MS Entra Auth: template Flask

Template de aplicação Flask planejado para demonstrar de ponta a ponta, uma integração com Microsoft Entra ID usando a extensão [`flask-ms-entra-auth`](https://github.com/vitoroliveirasilva/msentraauth.flask-extension), sessão server-side, Microsoft Graph, testes, operação e práticas de produção.

## Finalidade

Este projeto não é a biblioteca reutilizável. Sendo assim, ele é uma aplicação de referência para mostrar como:

- Configurar um App Registration;
- Instalar e inicializar a extensão;
- Usar application factory;
- Armazenar sessão e token cache no servidor;
- Autenticar e encerrar sessão;
- Consultar o perfil em Microsoft Graph;
- Vincular uma identidade externa a um usuário local;
- Tratar falhas sem vazar detalhes;
- Executar testes e deploy com configuração segura.

## Relação entre os projetos

```text
msentraauth.flask-extension
              ↓
       fornece o núcleo
              ↓
  msentraauth.flask-template
              ↓
mostra uso completo e produção
```

- extensão: [`vitoroliveirasilva/msentraauth.flask-extension`](https://github.com/vitoroliveirasilva/msentraauth.flask-extension);
- template: `vitoroliveirasilva/msentraauth.flask-template`.

## Estado

|                     Área | Estado            |
| -----------------------: | :---------------- |
| Documentação de fundação | Definida          |
|         Protótipo legado | Presente          |
|       Extensão consumida | Ainda não         |
|         Arquitetura-alvo | Definida          |
|                 Migração | Planejada         |
|       Testes de produção | Não implementados |
|          Deploy validado | Não validado      |
|          Release estável | Inexistente       |

## Arquitetura-alvo

```text
Navegador
   |
   v
Aplicação Flask
   |
   +-- flask-ms-entra-auth
   +-- Sessão server-side
   +-- Usuário local opcional
   +-- Cliente Microsoft Graph
   +-- Templates e tratamento de erros
   +-- Observabilidade
   |
   +--> Microsoft Entra ID
   +--> Microsoft Graph
   +--> Redis
```

## Funcionalidades

- Login e logout Microsoft Entra ID;
- Callback seguro;
- Perfil da Microsoft Graph;
- Sessão distribuída;
- Renovação silenciosa de token pela extensão;
- Telas de estado e erros;
- Health checks;
- Logs estruturados sem PII sensível;
- Docker e servidor WSGI;
- Testes unitários, integração e segurança;
- Documentação de configuração e deploy.

## O que o template não é

- Pacote para PyPI;
- Substituto da extensão;
- Plataforma de identidade completa;
- Solução multi-provedor;
- Sistema de autorização empresarial;
- Aplicação oficial da Microsoft.

## Variáveis planejadas

Consulte [`.env.example`](.env.example).

## Documentação

Índice: [`docs/README.md`](docs/README.md).

## Branches

- `dev`: desenvolvimento;
- `prod`: versão considerada estável.

## Segurança

Relatos sensíveis devem seguir [`SECURITY.md`](SECURITY.md).

## Licença e marcas

Licenciado sob a [Licença MIT](LICENSE). Este é um projeto independente, não oficial e sem qualquer afiliação, manutenção ou endosso da Microsoft. Microsoft, Microsoft Entra, Microsoft Graph e MSAL são marcas registradas de seus respectivos proprietários.
