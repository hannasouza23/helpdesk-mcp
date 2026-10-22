# Validação: buscar histórico de cliente

## Testes automatizados

Usar um banco SQLite temporário por teste. Preparar clientes com combinações distintas de chamados e eventos de status e verificar:

1. Um cliente cadastrado com chamados recebe somente os próprios chamados, com todos os campos definidos em `requisitos.md`.
2. Cada chamado inclui os eventos persistidos correspondentes, ordenados por `alterado_em` crescente e, em caso de empate, por `id` crescente.
3. Os chamados são ordenados por `criado_em` decrescente e, em caso de empate, por `id` crescente.
4. Um cliente cadastrado sem chamados recebe exatamente uma lista vazia (`[]`), sem erro.
5. Um identificador numérico sem cliente correspondente produz erro explícito de cliente não encontrado, e não uma lista vazia nem a mensagem de ausência de chamados.
6. Uma entrada não inteira produz erro de validação claro e não é interpretada como ausência de resultados.
7. Um chamado sem eventos persistidos é retornado com `historico_status` vazio, sem eventos inventados.
8. Chamados de outros clientes não aparecem nos resultados.
9. O identificador é enviado como parâmetro SQL; seu conteúdo não altera a instrução executada.

## Verificação via MCP

Executar o servidor localmente pelo transporte `stdio` e invocar `buscar_historico_cliente` com:

- um `cliente_id` cadastrado que tenha chamados;
- um `cliente_id` cadastrado sem chamados;
- um `cliente_id` sem cadastro;
- uma entrada que não seja inteira.

Confirmar que a primeira chamada retorna os chamados e eventos na ordenação especificada, que a segunda retorna `[]`, e que as duas últimas são sinalizadas como erro com mensagens apropriadas. Confirmar também que mensagens de diagnóstico não são enviadas à saída padrão reservada ao protocolo.
