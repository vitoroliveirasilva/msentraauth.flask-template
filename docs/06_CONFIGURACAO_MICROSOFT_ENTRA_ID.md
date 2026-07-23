# Configuração do Microsoft Entra ID

## App Registration

1. Crie uma aplicação **single-tenant**;
2. Adicione a plataforma Web;
3. Cadastre a redirect URI exata de cada ambiente;
4. Conceda somente a permissão delegada `User.Read`;
5. Armazene a credencial em secret manager e exponha-a por secret mount;
6. Planeje a rotação antes da expiração.

A versão `1.0.0` de `flask-ms-entra-auth` aceita client secret. Certificado e workload
identity permanecem evolução da extensão e não são simulados pelo template.

## Identificadores

Em produção, `MS_ENTRA_CLIENT_ID` deve ser UUID. `MS_ENTRA_TENANT_ID` deve ser o UUID do tenant
ou um domínio verificado específico. Os aliases `common`, `organizations` e `consumers` são
rejeitados para preservar o contrato single-tenant.

## Redirect URI

Referências:

```text
http://localhost:5000/auth/callback
https://app.example.com/auth/callback
```

A URI deve:

- usar a mesma origem de `APP_BASE_URL`;
- possuir caminho estático, não-raiz e sem barra final;
- não conter query, fragmento, credenciais, controles ou separadores codificados;
- ter no máximo 256 caracteres;
- corresponder exatamente ao App Registration.

Callbacks legados, como `/getAToken`, continuam suportados quando obedecem ao mesmo contrato.
`/logged-out` é confirmação de logout local e não é redirect URI do App Registration.

## Credencial

Use `MS_ENTRA_CLIENT_SECRET_FILE=/run/secrets/...` em produção. `MS_ENTRA_CLIENT_SECRET` e a
variante `_FILE` são mutuamente exclusivas. O valor nunca deve aparecer em Git, imagem, logs,
artefatos ou argumentos de processo.

## CAE e claims challenge

O cliente Graph detecta e valida um claims challenge sem registrar as claims. O template retorna
`401` sem redirecionamento automático, evitando loop. A repetição segura da autenticação com
`claims` depende de suporte explícito da extensão e permanece `BLOQUEADO_EXTENSAO`.
