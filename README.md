# Servidor MCP - Helpdesk

Este projeto propõe um **servidor MCP de Helpdesk** para disponibilizar operações sobre chamados a agentes de IA e outras aplicações clientes compatíveis com o Model Context Protocol (MCP).

Os chamados são registrados pela equipe de suporte técnico em um banco de dados. O servidor fornecerá ferramentas para:

- Listar chamados, inclusive com filtro por status.
- Consultar o histórico de chamados de um cliente.
- Atualizar o status de um chamado.

Nesta etapa, o servidor expõe apenas operações sobre dados, não uma interface para atendentes. O exemplo utilizará dados fictícios, será executado localmente e não terá autenticação real; não deve ser usado com dados reais nem considerado pronto para produção.

Consulte a [missão do projeto](specs/missao.md) para conhecer o propósito, os utilizadores, o escopo inicial e os limites do exemplo.

A [especificação da pilha de tecnologia](specs/pilha-tecnologia.md) registra as decisões de implementação, o esquema SQLite, a inicialização com dados fictícios e a execução local via `stdio`. As dependências Python estão listadas em `requirements.txt`.

O [roadmap de funcionalidades](specs/roadmap.md) organiza as três tools previstas em fases de definição, implementação e validação. Os nomes de variáveis, tabelas, atributos e funções do código serão em português.

## Executar o servidor

Com Python 3.11 ou superior, prepare o ambiente e inicie o servidor MCP:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m helpdesk_mcp.server
```

Na primeira execução, o servidor cria `data/helpdesk.sqlite3`, o esquema SQLite e
chamados fictícios. Para usar outro arquivo de banco, defina `HELPDESK_DB_PATH`.
O transporte do servidor é `stdio`; a tool `listar_chamados` aceita o parâmetro
opcional `status` (`aberto`, `em_andamento`, `resolvido` ou `fechado`).

Execute os testes com `python -m unittest discover -s tests`.
