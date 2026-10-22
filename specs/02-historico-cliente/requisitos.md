# Requisitos: buscar histórico de cliente

## Objetivo

Disponibilizar a tool MCP `buscar_historico_cliente` para consultar os chamados de um cliente e a linha do tempo de status de cada chamado.

## Entrada

- `cliente_id` (obrigatório): identificador numérico inteiro correspondente a `clientes.id`.
- A busca deve usar o identificador recebido, sem tentar localizar o cliente por nome ou e-mail.
- Uma entrada que não seja um número inteiro deve ser rejeitada com erro claro; não deve ser convertida silenciosamente nem tratada como cliente sem chamados.

## Saída

- Para cada chamado do cliente, retornar `id`, `cliente_id`, `descricao`, `status`, `criado_em`, `atualizado_em` e `historico_status`.
- `historico_status` é uma lista dos eventos persistidos para o chamado. Cada evento contém `status` e `alterado_em`.
- Os horários devem manter o formato ISO 8601 em UTC adotado pelo projeto.
- Ordenar os chamados do mais recente para o mais antigo por `criado_em`; em caso de empate, ordenar por `id` crescente.
- Ordenar os eventos de cada chamado do mais antigo para o mais recente por `alterado_em`; em caso de empate, usar o `id` do evento em ordem crescente.
- Não sintetizar eventos que não estejam persistidos no banco.

## Casos relevantes

1. `cliente_id` de cliente cadastrado com chamados: retornar somente os chamados desse cliente e seus eventos persistidos.
2. `cliente_id` de cliente cadastrado sem chamados: retornar uma lista vazia (`[]`), sem sinalizar erro.
3. `cliente_id` que não corresponde a nenhum cliente: retornar erro explícito de cliente não encontrado, distinto de uma lista vazia. A tool deve sinalizar a falha como erro, com a mensagem `Cliente não encontrado: {cliente_id}.`
4. Entrada não inteira: rejeitar com erro de validação claro; não executar uma consulta de histórico como se não houvesse resultados.
5. Cliente com chamado sem eventos persistidos: incluir o chamado com `historico_status` vazio, sem inventar uma linha do tempo.
6. Chamados de outros clientes não devem aparecer, ainda que tenham datas ou eventos iguais.
7. Todas as consultas devem usar parâmetros SQL; não interpolar valores recebidos nas instruções.

## Esquema da resposta

Quando houver chamados, a resposta é uma lista de objetos neste formato:

```json
[
  {
    "id": 12,
    "cliente_id": 3,
    "descricao": "Exemplo de chamado",
    "status": "em_andamento",
    "criado_em": "2025-01-11T10:30:00+00:00",
    "atualizado_em": "2025-01-12T10:30:00+00:00",
    "historico_status": [
      {
        "status": "aberto",
        "alterado_em": "2025-01-11T10:30:00+00:00"
      },
      {
        "status": "em_andamento",
        "alterado_em": "2025-01-12T10:30:00+00:00"
      }
    ]
  }
]
```

Para um cliente cadastrado sem chamados, a resposta é `[]`. Um identificador sem cliente correspondente produz o erro definido acima, e não `[]`.
