# Roadmap de funcionalidades

As funcionalidades serão desenvolvidas nesta ordem, uma por vez. Cada fase define um objetivo e um critério geral de conclusão; os detalhes de implementação serão especificados ao iniciar cada funcionalidade.

## 1. Listar chamados

Tool MCP: `listar_chamados`, com filtro opcional por status.

**Status:** concluída em 22/10/2026 às 11:29 (UTC−03:00).

### Fase 1 — Definir o contrato

- **Objetivo:** definir o comportamento esperado da listagem e do filtro opcional.
- **Critério de conclusão:** entradas, resultados e comportamento do filtro estão descritos e aprovados para implementação.

### Fase 2 — Implementar a listagem

- **Objetivo:** disponibilizar a tool para consultar chamados, com ou sem filtro de status.
- **Critério de conclusão:** a tool retorna os chamados correspondentes ao filtro informado ou todos os chamados quando nenhum filtro é fornecido.

### Fase 3 — Validar a funcionalidade

- **Objetivo:** verificar a listagem e o filtro por meio do servidor MCP.
- **Critério de conclusão:** testes confirmam os resultados esperados com filtro e sem filtro, sem regressões nas operações existentes.

## 2. Buscar histórico de cliente

Tool MCP: `buscar_historico_cliente`, consultando os chamados de um cliente.

### Fase 1 — Definir o contrato

- **Objetivo:** definir como identificar o cliente por `cliente_id` numérico e quais informações dos chamados compõem seu histórico.
- **Critério de conclusão:** entrada, resultados e comportamento distinto para cliente cadastrado sem chamados e identificador sem cliente correspondente estão descritos e aprovados para implementação.

### Fase 2 — Implementar a consulta

- **Objetivo:** disponibilizar a tool para consultar os chamados associados ao cliente identificado por `cliente_id`.
- **Critério de conclusão:** a tool retorna somente os chamados do cliente solicitado e seus eventos de status em ordem cronológica, retorna lista vazia para cliente cadastrado sem chamados e sinaliza erro apropriado quando o cliente não existe.

### Fase 3 — Validar a funcionalidade

- **Objetivo:** verificar a consulta de histórico por meio do servidor MCP.
- **Critério de conclusão:** testes confirmam o histórico para clientes com e sem chamados, distinguem cliente inexistente de lista vazia e não identificam regressões nas operações existentes.

## 3. Atualizar status

Tool MCP: `atualizar_status`, alterando o status de um chamado existente.

### Fase 1 — Definir o contrato

- **Objetivo:** definir os status aceitos e o comportamento para chamado inexistente ou atualização inválida.
- **Critério de conclusão:** entradas, resultados, erros e efeitos da atualização estão descritos e aprovados para implementação.

### Fase 2 — Implementar a atualização

- **Objetivo:** disponibilizar a tool para alterar o status de um chamado existente e registrar a alteração no histórico.
- **Critério de conclusão:** a tool atualiza o status do chamado e mantém seu histórico consistente conforme o contrato.

### Fase 3 — Validar a funcionalidade

- **Objetivo:** verificar a atualização de status por meio do servidor MCP.
- **Critério de conclusão:** testes confirmam a alteração e seu registro no histórico, além do comportamento para entradas inválidas e chamados inexistentes, sem regressões nas operações existentes.
