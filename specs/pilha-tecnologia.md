# Pilha de tecnologia

## Decisões obrigatórias

- **Linguagem:** Python 3.11 ou superior.
- **Ambiente:** ambiente virtual local (`venv`) para isolar as dependências.
- **Servidor MCP:** biblioteca `fastmcp`, responsável por declarar o servidor e expor as ferramentas.
- **Persistência:** SQLite, usando a biblioteca padrão `sqlite3` do Python.
- **Transporte:** `stdio`, para execução local e comunicação MCP por entrada e saída padrão.
- **Dados de demonstração:** na primeira inicialização, criar o banco, o esquema e registros fictícios automaticamente. Não recriar nem sobrescrever dados quando o banco já possuir chamados.

## Dependências e ambiente

A dependência externa da aplicação será `fastmcp`, registrada em `requirements.txt`. O acesso ao SQLite usa `sqlite3`, incluído no Python, portanto não requer uma dependência adicional.

Para preparar o ambiente a partir da raiz do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, a ativação pode ser feita com `.venv\Scripts\activate`.

## Banco de dados

O arquivo SQLite padrão será `data/helpdesk.sqlite3`, relativo à raiz do projeto. A inicialização deverá criar o diretório pai quando necessário. Para facilitar testes e execuções isoladas, a implementação poderá aceitar o caminho do banco por configuração, mantendo esse caminho como padrão.

O esquema inicial terá três tabelas:

### `customers`

Armazena a identidade necessária para associar chamados ao cliente:

- `id`: identificador inteiro, chave primária.
- `name`: nome fictício do cliente, obrigatório.
- `email`: e-mail fictício, opcional e único quando informado.

### `tickets`

Armazena o estado atual e os dados de consulta do chamado:

- `id`: identificador inteiro, chave primária.
- `customer_id`: chave estrangeira para `customers.id`, obrigatória.
- `description`: descrição do chamado, obrigatória.
- `status`: estado atual, restrito a `open`, `in_progress`, `resolved` ou `closed`.
- `created_at`: data e hora UTC de criação, obrigatória.
- `updated_at`: data e hora UTC da atualização mais recente, obrigatória.

### `ticket_status_history`

Armazena a linha do tempo de status, inclusive o status inicial, para permitir consultar o histórico de um cliente ou de um chamado:

- `id`: identificador inteiro, chave primária.
- `ticket_id`: chave estrangeira para `tickets.id`, obrigatória.
- `status`: status registrado, com os mesmos valores permitidos em `tickets.status`.
- `changed_at`: data e hora UTC em que a transição ocorreu, obrigatória.

As datas serão armazenadas como texto ISO 8601 em UTC. Criar índices em `tickets(customer_id, created_at)`, `tickets(status)` e `ticket_status_history(ticket_id, changed_at)` para apoiar as consultas previstas. As conexões devem habilitar as chaves estrangeiras do SQLite.

## Inicialização e dados fictícios

Na inicialização do servidor, a aplicação deverá:

1. Abrir ou criar o arquivo do banco e criar as tabelas e índices com operações idempotentes, como `CREATE TABLE IF NOT EXISTS`.
2. Inserir um conjunto pequeno e determinístico de clientes e chamados fictícios quando a tabela `tickets` estiver vazia; clientes de demonstração devem ser identificados por e-mails fictícios únicos e inseridos sem duplicação.
3. Criar, para cada chamado fictício, um registro inicial em `ticket_status_history`.
4. Fazer a criação do esquema e a carga inicial em transação, de modo que uma falha não deixe uma carga parcial.

Se já houver chamados, a inicialização não deve inserir novamente os dados de demonstração nem substituir dados existentes.

## Ferramentas MCP previstas

As ferramentas iniciais devem corresponder ao escopo da missão:

- `list_tickets`: listar chamados, com filtro opcional por status.
- `get_customer_ticket_history`: listar os chamados de um cliente e seus eventos de status em ordem cronológica.
- `update_ticket_status`: atualizar o status de um chamado e registrar a transição no histórico.

Atualizar o chamado e inserir o evento correspondente no histórico deve ocorrer na mesma transação. Se o status solicitado for igual ao atual, não deve ser criado um evento de transição duplicado. Consultas e atualizações devem usar parâmetros SQL, sem interpolar valores recebidos nas instruções SQL.

## Execução local

O servidor será iniciado como processo local e usará o transporte MCP `stdio`, conforme suportado pela biblioteca `fastmcp`. A saída padrão deve ser reservada à comunicação do protocolo; mensagens de diagnóstico devem ser enviadas à saída de erro.

O projeto é uma demonstração local com dados fictícios e não oferece autenticação real. Não deve ser usado com dados reais ou exposto como serviço de produção.
