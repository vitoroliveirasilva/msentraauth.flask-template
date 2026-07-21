# Critérios de aceite

| Critério                                 | Estado            |
| ---------------------------------------- | ----------------- |
| Factory sem estado global por usuário    | Atendido          |
| Extensão 1.x como único motor OAuth/OIDC | Atendido          |
| Sessão e cache server-side               | Atendido          |
| Redis com consumo atômico                | Atendido          |
| Hook local antes da sessão               | Atendido          |
| Graph com timeout e DTO                  | Atendido          |
| Token somente no servidor                | Atendido          |
| CSRF, CSP e cookies seguros              | Atendido          |
| Health e request ID                      | Atendido          |
| Testes sem rede e Redis real na CI       | Atendido          |
| Python 3.11 a 3.14                       | Configurado na CI |
| Docker não-root                          | Atendido          |
| Documentação e comandos coerentes        | Atendido          |
