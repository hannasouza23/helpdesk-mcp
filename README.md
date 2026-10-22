# Servidor MCP - Helpdesk

Este projeto propõe um **servidor MCP de Helpdesk** para disponibilizar operações sobre chamados a agentes de IA e outras aplicações clientes compatíveis com o Model Context Protocol (MCP).

Repositório remoto: [github.com/hannasouza23/helpdesk-mcp](https://github.com/hannasouza23/helpdesk-mcp).

Os chamados são registrados pela equipe de suporte técnico em um banco de dados. O servidor disponibiliza ferramentas para:

- Listar chamados, inclusive com filtro por status.
- Consultar o histórico de chamados de um cliente.
- Atualizar o status de um chamado, registrando cada transição sem substituir o histórico.

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
python src/server.py
```

Na primeira execução, o servidor cria `data/helpdesk.sqlite3`, o esquema SQLite e
chamados fictícios. Para usar outro arquivo de banco, defina `HELPDESK_DB_PATH`.
O transporte do servidor é `stdio`. A tool `listar_chamados` aceita o parâmetro
opcional `status` (`aberto`, `em_andamento`, `resolvido` ou `fechado`), e
`buscar_historico_cliente` recebe o `cliente_id` numérico para retornar os
chamados do cliente e seus eventos de status persistidos. `atualizar_status`
recebe `chamado_id` e `novo_status`; a alteração e seu evento histórico são
gravados na mesma transação. Os status aceitos são `aberto`, `em_andamento`,
`resolvido` e `fechado`.

## Configurar o servidor MCP no VS Code

O arquivo `.vscode/mcp.json` contém caminhos absolutos para o interpretador
Python e para `src/server.py`. Esses caminhos são específicos da máquina em que
o arquivo foi configurado. Para reproduzir a execução em outra máquina, ajuste
`command` para o interpretador do ambiente virtual criado localmente e o caminho
em `args` para o arquivo `src/server.py` na cópia local do projeto. No Linux ou
macOS, o interpretador costuma estar em `.venv/bin/python`; no Windows, em
`.venv/Scripts/python.exe`. Ambos os valores devem apontar para caminhos
absolutos válidos na máquina que executará o servidor.

Execute os testes com `python -m unittest discover -s tests`. O código da
aplicação fica em `src/`; o teste de integração também valida o ponto de entrada
configurado em `.vscode/mcp.json` via transporte `stdio`.
