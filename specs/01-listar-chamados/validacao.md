# Validação: listar chamados

## Testes automatizados

Usar um banco SQLite temporário por teste para não depender de dados locais nem alterar a base padrão. Preparar chamados com status distintos e verificar:

1. Chamada sem `status` retorna todos os registros.
2. Cada status aceito (`aberto`, `em_andamento`, `resolvido`, `fechado`) retorna apenas os chamados correspondentes.
3. Os campos retornados correspondem aos registros persistidos e os resultados respeitam a ordenação por `criado_em` decrescente, com desempate por `id`.
4. Um status aceito sem correspondências e uma base sem chamados retornam exatamente “Nenhum chamado encontrado.”
5. Um status não aceito produz erro explícito e não é interpretado como ausência de filtro.
6. O filtro é enviado como parâmetro SQL e não muda a instrução SQL executada.

## Validação da inicialização fictícia

1. Inicializar com um caminho de banco inexistente e confirmar a criação do diretório, do esquema e dos índices.
2. Confirmar que a carga inicial cria clientes e chamados fictícios determinísticos e registra o status inicial de cada chamado no histórico.
3. Inicializar novamente e confirmar que não há duplicação nem sobrescrita dos chamados.
4. Inicializar com uma base que já contenha chamados e confirmar que os dados existentes permanecem intactos e que os exemplos não são inseridos.
5. Verificar que uma falha durante a carga não deixa registros parciais, por meio do rollback da transação.

## Verificação via MCP

Executar o servidor localmente pelo transporte `stdio` e invocar `listar_chamados` sem filtro e com cada status aceito. Confirmar que as respostas correspondem aos casos automatizados, inclusive a mensagem de lista vazia, e que mensagens de diagnóstico não são enviadas à saída padrão reservada ao protocolo.
