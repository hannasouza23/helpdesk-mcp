# Servidor MCP - Helpdesk

Este projeto propõe um **servidor MCP de Helpdesk** para disponibilizar operações sobre chamados a agentes de IA e outras aplicações clientes compatíveis com o Model Context Protocol (MCP).

Os chamados são registrados pela equipe de suporte técnico em um banco de dados. O servidor fornecerá ferramentas para:

- Listar chamados, inclusive com filtro por status.
- Consultar o histórico de chamados de um cliente.
- Atualizar o status de um chamado.

Nesta etapa, o servidor expõe apenas operações sobre dados, não uma interface para atendentes. O exemplo utilizará dados fictícios, será executado localmente e não terá autenticação real; não deve ser usado com dados reais nem considerado pronto para produção.

Consulte a [missão do projeto](specs/missao.md) para conhecer o propósito, os utilizadores, o escopo inicial e os limites do exemplo.