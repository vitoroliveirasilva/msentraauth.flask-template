# Security policy

Este repositório é a fonte do generator. Vulnerabilidades do template, da infraestrutura de sessão, da integração com Microsoft Entra ID ou do pipeline de geração devem ser reportadas de forma privada pelo mecanismo de Security Advisories do repositório.

Não publique tokens, client secrets, chaves de sessão, dados pessoais, dumps de Redis ou evidências contendo credenciais em issues públicas.

## Escopo

A baseline gerada preserva sessão Redis server-side, rotação/revogação de SID, CSRF, headers de segurança, CSP restritiva, validação fail-fast e o protocolo OAuth/OIDC delegado exclusivamente à extensão `flask-ms-entra-auth`.

Aplicações geradas passam a ter ciclo de vida próprio. Vulnerabilidades introduzidas apenas por código específico de uma aplicação devem ser tratadas no repositório dessa aplicação.
