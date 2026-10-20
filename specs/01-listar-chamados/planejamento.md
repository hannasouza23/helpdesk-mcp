# Planejamento: listar chamados

As tarefas estão agrupadas em passos pequenos e devem ser executadas na ordem abaixo.

1. **Confirmar o contrato**
   - Revisar entradas, status aceitos, campos de saída, ordenação e comportamento para lista vazia.
   - Resolver eventuais divergências com a Constituição antes de implementar.
2. **Preparar a persistência para a listagem**
   - Reutilizar a conexão e o esquema SQLite definidos para o projeto.
   - Confirmar que o índice de `chamados(status)` é criado pela inicialização existente.
3. **Implementar a consulta**
   - Criar a tool MCP `listar_chamados` com filtro opcional por status.
   - Validar o status informado e executar uma consulta parametrizada.
   - Aplicar a ordenação determinística e retornar os campos especificados.
4. **Definir e integrar os dados de demonstração**
   - Na primeira inicialização com a tabela `chamados` vazia, inserir clientes e chamados fictícios determinísticos e seus status iniciais no histórico.
   - Fazer a carga em transação e preservar qualquer base que já contenha chamados.
5. **Adicionar testes da funcionalidade**
   - Cobrir listagem sem filtro, filtro com resultados, filtro sem resultados, base vazia e status inválido.
   - Cobrir a inicialização fictícia na primeira execução e a não duplicação em execuções seguintes.
6. **Executar a validação**
   - Rodar os testes relevantes e verificar a tool pelo servidor MCP, sem alterar o comportamento das outras funcionalidades.
