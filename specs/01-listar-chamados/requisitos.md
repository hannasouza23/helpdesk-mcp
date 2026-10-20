# Requisitos: listar chamados

## Objetivo

Disponibilizar a tool MCP `listar_chamados` para consultar os chamados registrados, permitindo restringir o resultado por status.

## Entrada

- `status` (opcional): status pelo qual filtrar os chamados.
- Quando omitido ou nulo, não aplicar filtro e listar todos os chamados.
- Quando informado, aceitar somente `aberto`, `em_andamento`, `resolvido` ou `fechado`. Esses valores correspondem aos estados definidos para a coluna `chamados.status` em `specs/pilha-tecnologia.md`.
- Um status fora dessa lista deve ser informado como entrada inválida; não deve ser tratado como uma consulta sem filtro.

## Saída

- Para cada chamado encontrado, retornar uma lista com `id`, `cliente_id`, `descricao`, `status`, `criado_em` e `atualizado_em`.
- Retornar os horários no formato ISO 8601 em UTC, conforme a pilha de tecnologia.
- Ordenar os resultados do mais recente para o mais antigo por `criado_em`; em caso de empate, usar `id` para manter a ordem determinística.
- Se nenhum chamado corresponder à consulta, retornar a mensagem **“Nenhum chamado encontrado.”**, inclusive quando a base estiver vazia. Não retornar uma lista de chamados com conteúdo inventado nem sinalizar esse caso como erro.

## Status sugeridos

| Status aceito | Significado |
| --- | --- |
| `aberto` | Chamado registrado e ainda não iniciado. |
| `em_andamento` | Chamado em atendimento. |
| `resolvido` | Solução aplicada, aguardando eventual encerramento. |
| `fechado` | Atendimento encerrado. |

Os quatro valores acima são os únicos aceitos para o filtro e coincidem com os valores permitidos no banco. A comparação deve usar os valores exatos, sem aceitar variações de maiúsculas, acentos ou espaços.

## Casos relevantes

1. Sem `status`: listar todos os chamados.
2. Com um status válido e resultados: listar somente chamados com esse status.
3. Com um status válido sem resultados: retornar “Nenhum chamado encontrado.”
4. Com base vazia: retornar “Nenhum chamado encontrado.”
5. Com status inválido: rejeitar a entrada com erro claro, sem executar a consulta como se o filtro tivesse sido omitido.
6. A consulta deve usar parâmetros SQL, sem interpolar o valor recebido na instrução.

## Inicialização de dados fictícios

Para que a listagem tenha exemplos disponíveis na primeira execução, a inicialização do servidor deve criar o esquema e os índices SQLite de forma idempotente e carregar um conjunto pequeno e determinístico de clientes e chamados fictícios quando `chamados` estiver vazia. Os clientes de demonstração devem usar e-mails fictícios únicos; cada chamado inicial deve ter um evento correspondente em `historico_status_chamado`.

A criação do esquema e a carga devem ocorrer em uma transação. Se já houver chamados, não inserir novamente os exemplos nem substituir dados existentes. Essa proposta segue as regras de inicialização de `specs/pilha-tecnologia.md`.
