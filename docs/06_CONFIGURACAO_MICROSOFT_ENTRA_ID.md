# Configuração do Microsoft Entra ID

## App Registration

1. Acessar o Microsoft Entra admin center;
2. Criar registro de aplicação;
3. Escolher single-tenant inicialmente;
4. Adicionar plataforma Web;
5. Registrar redirect URI local e de produção;
6. Adicionar permissão delegada `User.Read`;
7. Criar client secret ou certificado;
8. Guardar a credencial em secret manager.

## URIs de referência

Desenvolvimento:

```text
http://localhost:5000/auth/callback
http://localhost:5000/auth/logged-out
```

Produção:

```text
https://seu-dominio/auth/callback
https://seu-dominio/auth/logged-out
```

A URI enviada deve corresponder ao registro (não use wildcard ou domínio não controlado).

### App Registration existente com outro callback

Quando o App Registration não puder ser alterado e já usar outro caminho na mesma origem, configure a URI exata em `MS_ENTRA_REDIRECT_URI`. Exemplo:

```dotenv
MS_ENTRA_REDIRECT_URI=http://localhost:5000/getAToken
```

O template registra esse caminho como alias direto da função de callback da extensão. Não há redirecionamento intermediário, e os parâmetros `code` e `state` continuam sendo validados pela extensão. O caminho não pode ser a raiz da aplicação nem colidir com outra rota `GET`.

## Credencial

- Nunca em Git;
- Nunca no frontend;
- Nunca em logs;
- Rotação antes da expiração;
- Acesso pelo menor número de identidades;
- Certificado é evolução desejável.

## Single-tenant

É o modo inicial. Multi-tenant exige validação de issuer, allowlist, consentimento e modelo de autorização próprio.
