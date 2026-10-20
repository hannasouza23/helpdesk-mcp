# Missão do servidor MCP de Helpdesk

## Propósito

Disponibilizar operações de helpdesk por meio de um servidor MCP para que agentes e aplicações clientes possam consultar chamados e atualizar seu status. O servidor busca facilitar o acesso às informações de suporte e a execução de atualizações simples por meio de ferramentas compatíveis com MCP, sem exigir que o cliente acesse diretamente o banco de dados.

## Problema que resolve

Os chamados de suporte são registrados em um banco de dados e precisam ser consultados e atualizados pela equipe de suporte. O servidor MCP oferece uma interface padronizada para que agentes e aplicações clientes MCP no ambiente local realizem essas operações sobre os dados.

## Utilizadores

As ferramentas serão utilizadas por agentes de IA e por outras aplicações clientes compatíveis com o Model Context Protocol (MCP), como clientes que precisem consultar chamados ou atualizar seu status.

## Escopo inicial

O escopo inicial limita-se a operações sobre chamados:

- Listar chamados, com possibilidade de filtrar por status.
- Consultar o histórico de chamados de um cliente.
- Atualizar o status de um chamado.

O servidor não inclui uma interface própria para atendentes. A criação, exclusão e outras operações sobre chamados não fazem parte deste escopo inicial.

## Limites e premissas do exemplo

- Os dados utilizados serão fictícios e destinados a demonstração.
- O uso será local, sem disponibilização como serviço de produção.
- Não haverá autenticação real; portanto, o exemplo não deve ser tratado como seguro para dados reais ou para uso em ambientes expostos.
