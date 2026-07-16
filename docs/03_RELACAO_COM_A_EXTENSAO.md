# Relação com a extensão

## Dependência

O template deverá instalar `flask-ms-entra-auth` como dependência normal e durante desenvolvimento conjunto, poderá usar instalação editável local.

## Responsabilidades da extensão

- Fluxo MSAL;
- State/nonce;
- Callback;
- Token cache;
- Aquisição silenciosa;
- Identidade;
- Logout;
- Storage contract;
- Erros de autenticação.

## Responsabilidades do template

- Redis;
- Flask-Login, se adotado;
- Usuário local de demonstração;
- Cliente Graph;
- Interface;
- Docker;
- Observabilidade;
- Headers;
- Health checks;
- Documentação.

## Regra antirrepetição

O template não deve manter uma implementação paralela do fluxo. Deese modo, toda lacuna genérica deve ser discutida na extensão e toda necessidade específica permanece no template.

## Desenvolvimento conjunto

1. Definição do contrato na extensão;
2. Implementação de comportamento mínimo;
3. Consumo no template;
4. Identificação de fricção;
5. ajuste sem introduzir acoplamento visual.
