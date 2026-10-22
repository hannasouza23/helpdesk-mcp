# Requisitos — Atualizar status de chamado

## Objetivo

Definir o contrato da tool MCP `atualizar_status`, que altera o status de um chamado existente e preserva a linha do tempo de status armazenada no SQLite.

## Entrada

A tool recebe:

- `chamado_id`: identificador inteiro do chamado. Deve ser validado como inteiro estrito, sem aceitar valores de outro tipo como substitutos.
- `novo_status`: texto que deve corresponder exatamente a um dos status permitidos: `aberto`, `em_andamento`, `resolvido` ou `fechado`.

## Resultado

Em caso de sucesso, retornar um resultado estruturado com:

- `chamado_id`: identificador do chamado processado;
- `status_anterior`: status persistido antes da operação;
- `status_atual`: status persistido após a operação;
- `alterado`: indica se houve uma transição (`true`) ou se o chamado já estava nesse status (`false`).

O resultado deve refletir os dados persistidos. Uma falha não deve ser apresentada como sucesso.

## Comportamentos

1. Localizar o chamado pelo `chamado_id`.
2. Se o chamado existir e `novo_status` for permitido:
   - Se o novo status for diferente do atual, atualizar `chamados.status` e `chamados.atualizado_em`, e inserir um novo evento em `historico_status_chamado` com o identificador do chamado, o novo status e a data/hora UTC da transição.
   - Se o novo status já for o atual, retornar sucesso com `alterado: false` e não modificar o chamado nem inserir evento.
3. A atualização do chamado e a inserção do evento de transição devem fazer parte da mesma transação SQLite. Confirmar ambas em conjunto.
4. Se a inserção do evento falhar, reverter a transação inteira, inclusive a alteração de status e de `atualizado_em`.
5. Eventos históricos anteriores são imutáveis nesta operação: não podem ser apagados nem substituídos, tanto no sucesso quanto em caso de falha.
6. Usar parâmetros SQL para valores recebidos; não interpolar entradas nas instruções SQL.

## Erros e casos relevantes

| Caso | Resultado esperado | Efeito no banco |
|---|---|---|
| `chamado_id` não identifica um chamado existente | Sinalizar explicitamente erro de chamado não encontrado. Esse erro é distinto de status inválido. | Nenhuma alteração em qualquer tabela. |
| Chamado existe, mas `novo_status` não é um dos quatro valores permitidos | Sinalizar explicitamente erro de status inválido/não permitido. | Nenhuma alteração em qualquer tabela. |
| `chamado_id` tem tipo inválido | Rejeitar a entrada como erro de validação do identificador. | Nenhuma alteração em qualquer tabela. |
| Chamado existe e o status solicitado é igual ao atual | Retornar sucesso com `alterado: false`. | Não atualizar o chamado e não inserir evento. |
| Chamado existe e o status solicitado é diferente do atual | Retornar sucesso com `alterado: true`. | Atualizar o chamado e acrescentar exatamente um evento, preservando todos os anteriores. |
| A inserção do evento falha durante uma transição | Sinalizar a falha; não retornar sucesso. | Reverter também a atualização do chamado; preservar o histórico anterior. |

Para distinguir inexistência de status não permitido, verificar a existência do chamado antes de validar se o texto recebido pertence ao conjunto de status permitidos. Assim, um identificador válido em tipo que não corresponda a um registro produz o erro de chamado não encontrado; para um chamado existente, um status não permitido produz o erro de status inválido.

## Revisão e aprovação

Revisado quanto à distinção entre erros, aos limites de persistência e à consistência transacional com a constituição do projeto. Aprovado como contrato para orientar a implementação. A implementação não faz parte desta etapa.
