import asyncio
import os
from pathlib import Path
import sys
import tempfile
import unittest
from typing import cast
from unittest.mock import MagicMock, patch

from fastmcp import Client
from fastmcp.client.client import CallToolResult
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError

from src import database


class TestarHistoricoCliente(unittest.TestCase):
    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.diretorio.name) / "teste.sqlite3"
        database.inicializar_banco(self.caminho_banco)
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute("DELETE FROM historico_status_chamado")
            conexao.execute("DELETE FROM chamados")
            conexao.execute(
                """
                INSERT INTO clientes (id, nome, email)
                VALUES (4, 'Cliente sem chamados', 'sem-chamados@example.test')
                """
            )
            conexao.executemany(
                """
                INSERT INTO chamados (
                    id, cliente_id, descricao, status, criado_em, atualizado_em
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        10,
                        1,
                        "Data empatada, id maior",
                        "resolvido",
                        "2025-01-02T09:00:00+00:00",
                        "2025-01-03T09:00:00+00:00",
                    ),
                    (
                        8,
                        1,
                        "Data empatada, id menor",
                        "em_andamento",
                        "2025-01-02T09:00:00+00:00",
                        "2025-01-02T10:00:00+00:00",
                    ),
                    (
                        7,
                        1,
                        "Chamado sem eventos",
                        "aberto",
                        "2025-01-01T09:00:00+00:00",
                        "2025-01-01T09:00:00+00:00",
                    ),
                    (
                        20,
                        2,
                        "Chamado de outro cliente",
                        "aberto",
                        "2025-01-04T09:00:00+00:00",
                        "2025-01-04T09:00:00+00:00",
                    ),
                ),
            )
            conexao.executemany(
                """
                INSERT INTO historico_status_chamado (
                    id, chamado_id, status, alterado_em
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    (30, 10, "resolvido", "2025-01-03T09:00:00+00:00"),
                    (21, 8, "em_andamento", "2025-01-02T09:00:00+00:00"),
                    (20, 8, "aberto", "2025-01-02T09:00:00+00:00"),
                    (31, 20, "aberto", "2025-01-04T09:00:00+00:00"),
                ),
            )

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def test_retorna_chamados_do_cliente_com_ordem_e_eventos_deterministicos(
        self,
    ) -> None:
        resultado = database.buscar_historico_cliente(self.caminho_banco, 1)

        self.assertEqual([chamado["id"] for chamado in resultado], [8, 10, 7])
        self.assertEqual(
            set(resultado[0]),
            {
                "id",
                "cliente_id",
                "descricao",
                "status",
                "criado_em",
                "atualizado_em",
                "historico_status",
            },
        )
        self.assertEqual(
            resultado[0]["historico_status"],
            [
                {
                    "status": "aberto",
                    "alterado_em": "2025-01-02T09:00:00+00:00",
                },
                {
                    "status": "em_andamento",
                    "alterado_em": "2025-01-02T09:00:00+00:00",
                },
            ],
        )
        self.assertEqual(
            resultado[2]["historico_status"],
            [],
        )
        self.assertTrue(all(chamado["cliente_id"] == 1 for chamado in resultado))

    def test_cliente_cadastrado_sem_chamados_retorna_lista_vazia(self) -> None:
        self.assertEqual(
            database.buscar_historico_cliente(self.caminho_banco, 4), []
        )

    def test_cliente_inexistente_gera_erro_especifico(self) -> None:
        with self.assertRaisesRegex(
            LookupError, r"^Cliente não encontrado: 999\.$"
        ):
            database.buscar_historico_cliente(self.caminho_banco, 999)

    def test_identificador_nao_inteiro_e_rejeitado_antes_da_consulta(self) -> None:
        with patch.object(database, "conectar_banco") as conectar:
            for cliente_id in ("1", 1.5, True):
                with self.subTest(cliente_id=cliente_id):
                    with self.assertRaisesRegex(
                        ValueError, "cliente_id deve ser um número inteiro"
                    ):
                        database.buscar_historico_cliente(
                            self.caminho_banco, cast(int, cliente_id)
                        )

        conectar.assert_not_called()

    def test_identificador_e_enviado_como_parametro_sql(self) -> None:
        conexao = MagicMock()
        conexao.__enter__.return_value = conexao
        conexao.execute.return_value.fetchone.return_value = (1,)
        conexao.execute.return_value.fetchall.return_value = []

        with patch.object(database, "conectar_banco", return_value=conexao):
            database.buscar_historico_cliente(self.caminho_banco, 15)

        chamadas = conexao.execute.call_args_list
        self.assertEqual(chamadas[0].args[1], (15,))
        self.assertIn("WHERE id = ?", chamadas[0].args[0])
        self.assertEqual(chamadas[1].args[1], (15,))
        self.assertIn("WHERE c.cliente_id = ?", chamadas[1].args[0])

    def test_tool_mcp_expoe_resultados_e_sinaliza_erros(self) -> None:
        async def chamar_tools() -> tuple[
            list[str], CallToolResult, CallToolResult, str, str
        ]:
            ambiente = os.environ.copy()
            ambiente["HELPDESK_DB_PATH"] = str(self.caminho_banco)
            caminho_src = str(Path(__file__).resolve().parents[1] / "src")
            ambiente["PYTHONPATH"] = os.pathsep.join(
                filter(None, (caminho_src, ambiente.get("PYTHONPATH")))
            )
            transporte = StdioTransport(
                command=sys.executable,
                args=[str(Path(caminho_src) / "server.py")],
                env=ambiente,
                cwd=str(Path(__file__).resolve().parents[1]),
            )
            async with Client(transporte) as cliente:
                ferramentas = await cliente.list_tools()
                com_chamados = await cliente.call_tool(
                    "buscar_historico_cliente", {"cliente_id": 1}
                )
                sem_chamados = await cliente.call_tool(
                    "buscar_historico_cliente", {"cliente_id": 4}
                )
                try:
                    await cliente.call_tool(
                        "buscar_historico_cliente", {"cliente_id": 999}
                    )
                except ToolError as erro:
                    inexistente = str(erro)
                else:
                    raise AssertionError("Cliente inexistente não sinalizou erro.")
                try:
                    await cliente.call_tool(
                        "buscar_historico_cliente", {"cliente_id": "1"}
                    )
                except ToolError as erro:
                    invalido = str(erro)
                else:
                    raise AssertionError("Identificador inválido não sinalizou erro.")
                return (
                    [ferramenta.name for ferramenta in ferramentas],
                    com_chamados,
                    sem_chamados,
                    inexistente,
                    invalido,
                )

        (
            nomes_ferramentas,
            com_chamados,
            sem_chamados,
            inexistente,
            invalido,
        ) = asyncio.run(chamar_tools())

        self.assertEqual(
            nomes_ferramentas,
            ["listar_chamados", "buscar_historico_cliente", "atualizar_status"],
        )
        self.assertFalse(com_chamados.is_error)
        self.assertIsNotNone(com_chamados.structured_content)
        assert com_chamados.structured_content is not None
        self.assertEqual(
            [item["id"] for item in com_chamados.structured_content["result"]],
            [8, 10, 7],
        )
        self.assertFalse(sem_chamados.is_error)
        self.assertEqual(sem_chamados.structured_content, {"result": []})
        self.assertIn(
            "Cliente não encontrado: 999.",
            inexistente,
        )
        self.assertIn("cliente_id", invalido)


if __name__ == "__main__":
    unittest.main()
