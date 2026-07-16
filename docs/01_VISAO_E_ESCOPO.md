# Visão e escopo

## Propósito

Servir como aplicação Flask de referência, executável e didática para a extensão MS Entra Auth.

## Público

- Desenvolvedores avaliando a extensão;
- Equipes que precisam de um ponto de partida seguro;
- Mantenedores que desejam comparar integração local e produção;
- Estudantes de autenticação web server-side.

## Objetivos

1. Demonstrar o contrato público da extensão;
2. Exibir configuração do Microsoft Entra ID;
3. Provar sessão server-side e múltiplos workers;
4. Mostrar integração mínima com Graph;
5. Fornecer telas acessíveis e erros seguros;
6. Oferecer testes reproduzíveis;
7. Documentar operação.

## Não objetivos

- Ser extensão;
- Esconder toda a configuração Microsoft;
- Fornecer autorização completa;
- Sincronizar grupos;
- Suportar outros frameworks;
- Criar App Registration automaticamente;
- Representar aplicação oficial.

## Critério de sucesso

Uma pessoa deve conseguir clonar, configurar ambiente de desenvolvimento, registrar redirect URI, iniciar Redis, executar a app, autenticar e visualizar o perfil seguindo apenas a documentação da release.
