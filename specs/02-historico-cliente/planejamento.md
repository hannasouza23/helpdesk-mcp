# Planejamento: buscar histórico de cliente

As tarefas estão agrupadas em passos pequenos e devem ser executadas na ordem abaixo.

1. **Confirmar o contrato**
   - Revisar o parâmetro obrigatório `cliente_id`, os campos retornados, as ordenações e os casos de cliente sem chamados e cliente inexistente.
   - Resolver eventuais divergências com a Constituição antes de implementar.
2. **Preparar a consulta ao banco**
   - Reutilizar a conexão, o esquema e os índices definidos para `clientes`, `chamados` e `historico_status_chamado`.
   - Consultar a existência do cliente separadamente da existência de chamados, preservando a distinção entre os dois casos.
3. **Implementar a consulta do histórico**
   - Criar a função de consulta e a tool MCP `buscar_historico_cliente`, recebendo `cliente_id`.
   - Buscar somente os chamados do cliente e associar os eventos de status persistidos a cada chamado.
   - Aplicar as ordenações determinísticas e usar parâmetros SQL.
   - Retornar lista vazia para cliente existente sem chamados e erro explícito para cliente inexistente ou entrada inválida.
4. **Adicionar testes da funcionalidade**
   - Cobrir cliente com um ou mais chamados, eventos em ordem cronológica e exclusão dos dados de outros clientes.
   - Cobrir cliente existente sem chamados, cliente inexistente, entrada inválida e chamado sem eventos persistidos.
   - Verificar ordenação determinística inclusive quando houver datas iguais.
5. **Executar a validação**
   - Rodar os testes relevantes e verificar a tool pelo servidor MCP via `stdio`.
   - Confirmar que as respostas correspondem ao contrato e não causam regressões nas operações existentes.
