# Planejamento — Atualizar status de chamado

Os grupos abaixo devem ser executados na ordem indicada. Cada grupo é pequeno e tem um resultado verificável.

## 1. Implementar a operação no banco

- Criar a operação de atualização recebendo o caminho do banco, `chamado_id` e `novo_status`.
- Distinguir chamado inexistente de status não permitido, sem alterar dados nos dois casos.
- Fazer a atualização do chamado e a inclusão do evento numa única transação.
- Não gravar alteração nem evento quando o status já for o atual.
- Garantir rollback da atualização se a inclusão do evento falhar e preservar eventos anteriores.

**Concluído quando:** a operação de banco satisfaz o contrato e tem testes unitários dos casos de sucesso, erro e rollback.

## 2. Expor a tool MCP

- Registrar a tool `atualizar_status` no servidor, com entradas estritas para identificador e novo status.
- Devolver o resultado estruturado definido nos requisitos.
- Propagar erros de chamado não encontrado, status inválido e falha de persistência de forma explícita e distinta.

**Concluído quando:** a tool está acessível pelo servidor MCP e os erros não são convertidos em resultados de sucesso.

## 3. Validar integração e regressões

- Testar a tool contra um banco SQLite isolado, confirmando estado atual e eventos persistidos.
- Testar a falha de inclusão do evento e confirmar a reversão integral da transição.
- Executar testes existentes de listagem e consulta de histórico.

**Concluído quando:** os cenários de validação estão aprovados e as operações existentes continuam funcionando.

## Revisão e aprovação

Revisado para manter a ordem contrato de dados → tool MCP → validação, com entregas verificáveis em cada grupo. Aprovado para orientar a futura implementação. Nenhuma tarefa de implementação foi executada nesta etapa.
