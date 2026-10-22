# Validação — Atualizar status de chamado

Validar a futura implementação com testes automatizados usando um banco SQLite temporário e isolado. Preparar chamados e eventos iniciais conhecidos para comparar o estado antes e depois de cada operação.

## Casos de validação

1. **Transição válida:** para um chamado existente, solicitar um status diferente e verificar o resultado (`status_anterior`, `status_atual` e `alterado: true`), o novo `chamados.status`, a atualização de `atualizado_em` e a inclusão de exatamente um evento com o novo status.
2. **Histórico preservado:** comparar os eventos anteriores antes e depois da transição; todos devem continuar presentes e inalterados, com apenas o novo evento acrescentado.
3. **Status inalterado:** solicitar o status que o chamado já possui e verificar `alterado: false`, sem mudanças no registro do chamado, inclusive em `atualizado_em`, e sem evento adicional.
4. **Chamado inexistente:** usar um identificador inteiro sem registro e verificar erro explícito de chamado não encontrado. Comparar as tabelas relevantes antes e depois e confirmar que nenhum dado foi alterado.
5. **Status inválido para chamado existente:** usar um identificador existente e um texto fora do conjunto permitido; verificar erro explícito de status inválido, distinto do erro de chamado não encontrado, e ausência de alterações no chamado e no histórico.
6. **Identificador com tipo inválido:** verificar rejeição da entrada e ausência de alterações no banco.
7. **Falha ao inserir evento:** provocar uma falha controlada na inserção do evento durante uma transição. Confirmar que a operação sinaliza a falha, que o status e `atualizado_em` do chamado permanecem como antes e que os eventos históricos anteriores seguem intactos.
8. **Integração MCP:** invocar `atualizar_status` pelo servidor MCP e confirmar que os resultados e erros expostos correspondem ao contrato da operação de banco.
9. **Regressão:** executar os testes existentes de `listar_chamados` e `buscar_historico_cliente`; confirmar que continuam passando.

## Critério de aprovação

A funcionalidade atende à especificação quando todos os casos acima passam, a transição e o evento são atômicos, a repetição do status atual não produz evento e nenhum cenário apaga ou substitui histórico anterior.

## Revisão e aprovação

Revisado para cobrir entradas, os dois erros distintos, todos os efeitos de persistência, a falha transacional e a integração MCP, além de regressões. Aprovado como procedimento de validação da futura implementação. Nenhum teste de implementação foi executado nesta etapa.
