# ADR-011: segredos separados e Graph global allowlisted

## Contexto

A configuração anterior reutilizava `SECRET_KEY` para múltiplas finalidades, não possuía key ring
e aceitava qualquer base HTTPS para o Graph. A extensão 1.0.0 recebe client secret e não expõe um
contrato de authority/cloud, certificado, workload identity ou claims challenge.

## Decisão

- Separar Flask, assinatura do SID e CSRF;
- aceitar ring ordenado de até cinco chaves para assinatura do SID;
- assinar somente com a primeira chave e verificar pelas demais durante rotação;
- aceitar secrets por arquivo absoluto e pequeno;
- em produção, exigir material base64 URL-safe de pelo menos 32 bytes e valores independentes;
- permitir somente `https://graph.microsoft.com/v1.0`;
- detectar claims challenge, mas não iniciar reautenticação automática sem suporte da extensão.

## Consequências

- produção exige novas variáveis antes do deploy;
- rotação pode ocorrer sem invalidar imediatamente todos os cookies;
- clouds soberanos permanecem bloqueados até authority, issuer e Graph evoluírem juntos;
- integridade/confidencialidade do payload Redis permanece para a SEC-03;
- certificado, federação e CAE completo exigem evolução da extensão.
