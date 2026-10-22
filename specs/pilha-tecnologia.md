# Pilha de tecnologia

## Decisões obrigatórias

- **Linguagem:** Python 3.11 ou superior.
- **Ambiente:** ambiente virtual local (`venv`) para isolar as dependências.
- **Servidor MCP:** biblioteca `fastmcp`, responsável por declarar o servidor e expor as ferramentas.
- **Persistência:** SQLite, usando a biblioteca padrão `sqlite3` do Python.
- **Transporte:** `stdio`, para execução local e comunicação MCP por entrada e saída padrão.
- **Dados de demonstração:** na primeira inicialização, criar o banco, o esquema e registros fictícios automaticamente. Não recriar nem sobrescrever dados quando o banco já possuir chamados.
- **Nomenclatura:** nomes de variáveis, tabelas, atributos e funções serão em português para facilitar o entendimento do código. Os nomes das tools MCP também seguirão os nomes definidos em português neste projeto.

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

### `clientes`

Armazena a identidade necessária para associar chamados ao cliente:

- `id`: identificador inteiro, chave primária.
- `nome`: nome fictício do cliente, obrigatório.
- `email`: e-mail fictício, opcional e único quando informado.

### `chamados`

Armazena o estado atual e os dados de consulta do chamado:

- `id`: identificador inteiro, chave primária.
- `cliente_id`: chave estrangeira para `clientes.id`, obrigatória.
- `descricao`: descrição do chamado, obrigatória.
- `status`: estado atual, restrito a `aberto`, `em_andamento`, `resolvido` ou `fechado`.
- `criado_em`: data e hora UTC de criação, obrigatória.
- `atualizado_em`: data e hora UTC da atualização mais recente, obrigatória.

### `historico_status_chamado`

Armazena a linha do tempo de status, inclusive o status inicial, para permitir consultar o histórico de um cliente ou de um chamado:

- `id`: identificador inteiro, chave primária.
- `chamado_id`: chave estrangeira para `chamados.id`, obrigatória.
- `status`: status registrado, com os mesmos valores permitidos em `chamados.status`.
- `alterado_em`: data e hora UTC em que a transição ocorreu, obrigatória.

As datas serão armazenadas como texto ISO 8601 em UTC. Criar índices em `chamados(cliente_id, criado_em)`, `chamados(status)` e `historico_status_chamado(chamado_id, alterado_em)` para apoiar as consultas previstas. As conexões devem habilitar as chaves estrangeiras do SQLite.

## Inicialização e dados fictícios

Na inicialização do servidor, a aplicação deverá:

1. Abrir ou criar o arquivo do banco e criar as tabelas e índices com operações idempotentes, como `CREATE TABLE IF NOT EXISTS`.
2. Inserir um conjunto pequeno e determinístico de clientes e chamados fictícios quando a tabela `chamados` estiver vazia; clientes de demonstração devem ser identificados por e-mails fictícios únicos e inseridos sem duplicação.
3. Criar, para cada chamado fictício, um registro inicial em `historico_status_chamado`.
4. Fazer a criação do esquema e a carga inicial em transação, de modo que uma falha não deixe uma carga parcial.

Se já houver chamados, a inicialização não deve inserir novamente os dados de demonstração nem substituir dados existentes.

## Ferramentas MCP previstas

As ferramentas iniciais devem corresponder ao escopo da missão:

- `listar_chamados`: listar chamados, com filtro opcional por status.
- `buscar_historico_cliente`: receber o identificador numérico `cliente_id` e listar os chamados desse cliente com seus eventos de status em ordem cronológica. Para cliente cadastrado sem chamados, retornar uma lista vazia; para identificador sem cliente correspondente, sinalizar erro de cliente não encontrado.
- `atualizar_status`: atualizar o status de um chamado e registrar a transição no histórico.

Atualizar o chamado e inserir o evento correspondente no histórico deve ocorrer na mesma transação. Se o status solicitado for igual ao atual, não deve ser criado um evento de transição duplicado. Consultas e atualizações devem usar parâmetros SQL, sem interpolar valores recebidos nas instruções SQL.

## Execução local

O servidor será iniciado como processo local e usará o transporte MCP `stdio`, conforme suportado pela biblioteca `fastmcp`. A saída padrão deve ser reservada à comunicação do protocolo; mensagens de diagnóstico devem ser enviadas à saída de erro.

O projeto é uma demonstração local com dados fictícios e não oferece autenticação real. Não deve ser usado com dados reais ou exposto como serviço de produção.
