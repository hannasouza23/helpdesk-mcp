import asyncio
import os
from pathlib import Path
import sqlite3
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


class TestarAtualizacaoStatus(unittest.TestCase):
    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.diretorio.name) / "teste.sqlite3"
        database.inicializar_banco(self.caminho_banco)
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute("DELETE FROM historico_status_chamado")
            conexao.execute("DELETE FROM chamados")
            conexao.execute(
                """
                INSERT INTO chamados (
                    id, cliente_id, descricao, status, criado_em, atualizado_em
                ) VALUES (
                    40, 1, 'Chamado de teste', 'aberto',
                    '2025-02-01T09:00:00+00:00', '2025-02-01T09:00:00+00:00'
                )
                """
            )
            conexao.executemany(
                """
                INSERT INTO historico_status_chamado (
                    chamado_id, status, alterado_em
                ) VALUES (40, ?, ?)
                """,
                (
                    ("aberto", "2025-02-01T09:00:00+00:00"),
                    ("em_andamento", "2025-02-01T10:00:00+00:00"),
                ),
            )

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def _estado_chamado(
        self,
    ) -> tuple[tuple[str, str], list[tuple[int, int, str, str]]]:
        with database.conectar_banco(self.caminho_banco) as conexao:
            chamado = cast(
                tuple[str, str],
                tuple(
                    conexao.execute(
                        """
                        SELECT status, atualizado_em
                        FROM chamados WHERE id = 40
                        """
                    ).fetchone()
                ),
            )
            eventos = [
                cast(tuple[int, int, str, str], tuple(linha))
                for linha in conexao.execute(
                    """
                    SELECT id, chamado_id, status, alterado_em
                    FROM historico_status_chamado
                    WHERE chamado_id = 40
                    ORDER BY id
                    """
                )
            ]
        return chamado, eventos

    def test_transicao_atualiza_chamado_e_acrescenta_um_evento(self) -> None:
        estado_anterior, eventos_anteriores = self._estado_chamado()

        resultado = database.atualizar_status_chamado(
            self.caminho_banco, 40, "resolvido"
        )

        chamado, eventos = self._estado_chamado()
        self.assertEqual(
            resultado,
            {
                "chamado_id": 40,
                "status_anterior": "aberto",
                "status_atual": "resolvido",
                "alterado": True,
            },
        )
        self.assertEqual(chamado[0], "resolvido")
        self.assertNotEqual(chamado[1], estado_anterior[1])
        self.assertEqual(eventos[:-1], eventos_anteriores)
        self.assertEqual(len(eventos), len(eventos_anteriores) + 1)
        self.assertEqual(eventos[-1][1:3], (40, "resolvido"))
        self.assertEqual(eventos[-1][3], chamado[1])
        self.assertTrue(eventos[-1][3].endswith("+00:00"))

    def test_status_igual_nao_altera_chamado_nem_historico(self) -> None:
        antes = self._estado_chamado()

        resultado = database.atualizar_status_chamado(
            self.caminho_banco, 40, "aberto"
        )

        self.assertEqual(
            resultado,
            {
                "chamado_id": 40,
                "status_anterior": "aberto",
                "status_atual": "aberto",
                "alterado": False,
            },
        )
        self.assertEqual(self._estado_chamado(), antes)

    def test_chamado_inexistente_tem_erro_distinto_e_nao_altera_dados(self) -> None:
        antes = self._estado_chamado()

        with self.assertRaisesRegex(
            LookupError, r"^Chamado não encontrado: 999\.$"
        ):
            database.atualizar_status_chamado(
                self.caminho_banco, 999, "status_invalido"
            )

        self.assertEqual(self._estado_chamado(), antes)

    def test_status_invalido_em_chamado_existente_nao_altera_dados(self) -> None:
        antes = self._estado_chamado()

        with self.assertRaisesRegex(ValueError, "Status inválido"):
            database.atualizar_status_chamado(
                self.caminho_banco, 40, "EM_ANDAMENTO"
            )

        self.assertEqual(self._estado_chamado(), antes)

    def test_identificador_de_tipo_invalido_e_rejeitado_antes_do_banco(self) -> None:
        with patch.object(database, "conectar_banco") as conectar:
            for chamado_id in ("40", 40.5, True):
                with self.subTest(chamado_id=chamado_id):
                    with self.assertRaisesRegex(
                        ValueError, "chamado_id deve ser um número inteiro"
                    ):
                        database.atualizar_status_chamado(
                            self.caminho_banco,
                            cast(int, chamado_id),
                            "resolvido",
                        )

        conectar.assert_not_called()

    def test_falha_ao_inserir_evento_reverte_transicao(self) -> None:
        antes = self._estado_chamado()
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute(
                """
                CREATE TRIGGER falhar_novo_evento
                BEFORE INSERT ON historico_status_chamado
                WHEN NEW.chamado_id = 40 AND NEW.status = 'resolvido'
                BEGIN
                    SELECT RAISE(ABORT, 'falha controlada ao inserir evento');
                END
                """
            )

        with self.assertRaisesRegex(sqlite3.IntegrityError, "falha controlada"):
            database.atualizar_status_chamado(
                self.caminho_banco, 40, "resolvido"
            )

        self.assertEqual(self._estado_chamado(), antes)

    def test_consulta_do_identificador_usa_parametro_sql(self) -> None:
        conexao = MagicMock()
        conexao.__enter__.return_value = conexao
        conexao.execute.return_value.fetchone.side_effect = [
            {"status": "aberto"},
            {"status": "aberto"},
        ]

        with patch.object(database, "conectar_banco", return_value=conexao):
            resultado = database.atualizar_status_chamado(
                self.caminho_banco, 40, "aberto"
            )

        self.assertFalse(resultado["alterado"])
        consultas = [
            chamada
            for chamada in conexao.execute.call_args_list
            if "SELECT status FROM chamados WHERE id = ?" in chamada.args[0]
        ]
        self.assertTrue(consultas)
        self.assertTrue(all(chamada.args[1] == (40,) for chamada in consultas))

    def test_tool_mcp_expone_resultados_e_erros_da_operacao(self) -> None:
        async def chamar_tool() -> tuple[list[str], CallToolResult, str, str, str]:
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
                sucesso = await cliente.call_tool(
                    "atualizar_status",
                    {"chamado_id": 40, "novo_status": "resolvido"},
                )
                try:
                    await cliente.call_tool(
                        "atualizar_status",
                        {"chamado_id": 999, "novo_status": "desconhecido"},
                    )
                except ToolError as erro:
                    inexistente = str(erro)
                else:
                    raise AssertionError("Chamado inexistente não sinalizou erro.")
                try:
                    await cliente.call_tool(
                        "atualizar_status",
                        {"chamado_id": 40, "novo_status": "desconhecido"},
                    )
                except ToolError as erro:
                    status_invalido = str(erro)
                else:
                    raise AssertionError("Status inválido não sinalizou erro.")
                try:
                    await cliente.call_tool(
                        "atualizar_status",
                        {"chamado_id": "40", "novo_status": "resolvido"},
                    )
                except ToolError as erro:
                    identificador_invalido = str(erro)
                else:
                    raise AssertionError("Identificador inválido não sinalizou erro.")
                return (
                    [ferramenta.name for ferramenta in ferramentas],
                    sucesso,
                    inexistente,
                    status_invalido,
                    identificador_invalido,
                )

        (
            nomes,
            sucesso,
            inexistente,
            status_invalido,
            identificador_invalido,
        ) = asyncio.run(chamar_tool())

        self.assertEqual(
            nomes, ["listar_chamados", "buscar_historico_cliente", "atualizar_status"]
        )
        self.assertFalse(sucesso.is_error)
        self.assertEqual(
            sucesso.structured_content,
            {
                "chamado_id": 40,
                "status_anterior": "aberto",
                "status_atual": "resolvido",
                "alterado": True,
            },
        )
        self.assertIn("Chamado não encontrado: 999.", inexistente)
        self.assertIn("Status inválido", status_invalido)
        self.assertIn("chamado_id", identificador_invalido)


if __name__ == "__main__":
    unittest.main()
