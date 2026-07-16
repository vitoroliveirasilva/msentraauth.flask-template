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

## URIs planejadas

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

A URI enviada deve corresponder ao registro (não usar wildcard ou domínio não controlado).

## Credencial

- Nunca em Git;
- Nunca no frontend;
- Nunca em logs;
- Rotação antes da expiração;
- Acesso pelo menor número de identidades;
- Certificado é evolução desejável.

## Single-tenant

É o modo inicial. Multi-tenant exige validação de issuer, allowlist, consentimento e modelo de autorização próprio.
