import asyncio
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from helpdesk_mcp import database


class TestarListagemChamados(unittest.TestCase):
    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.diretorio.name) / "teste.sqlite3"
        database.inicializar_banco(self.caminho_banco)
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute("DELETE FROM historico_status_chamado")
            conexao.execute("DELETE FROM chamados")
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
                        "Chamado mais antigo",
                        "aberto",
                        "2025-01-01T09:00:00+00:00",
                        "2025-01-01T09:00:00+00:00",
                    ),
                    (
                        12,
                        2,
                        "Empate de data, id maior",
                        "aberto",
                        "2025-01-02T09:00:00+00:00",
                        "2025-01-02T09:00:00+00:00",
                    ),
                    (
                        11,
                        2,
                        "Empate de data, id menor",
                        "em_andamento",
                        "2025-01-02T09:00:00+00:00",
                        "2025-01-02T09:00:00+00:00",
                    ),
                    (
                        13,
                        3,
                        "Chamado resolvido",
                        "resolvido",
                        "2025-01-03T09:00:00+00:00",
                        "2025-01-03T09:00:00+00:00",
                    ),
                    (
                        14,
                        1,
                        "Chamado fechado",
                        "fechado",
                        "2025-01-04T09:00:00+00:00",
                        "2025-01-04T09:00:00+00:00",
                    ),
                ),
            )

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def test_lista_todos_ordenados_com_desempate_por_id(self) -> None:
        resultado = database.listar_chamados(self.caminho_banco)

        self.assertEqual([chamado["id"] for chamado in resultado], [14, 13, 11, 12, 10])
        self.assertEqual(
            set(resultado[0]),
            {"id", "cliente_id", "descricao", "status", "criado_em", "atualizado_em"},
        )

    def test_filtra_por_cada_status_aceito(self) -> None:
        for status in database.STATUS_VALIDOS:
            with self.subTest(status=status):
                resultado = database.listar_chamados(self.caminho_banco, status)
                self.assertTrue(isinstance(resultado, list))
                self.assertTrue(all(chamado["status"] == status for chamado in resultado))

    def test_status_valido_sem_resultados_retorna_mensagem(self) -> None:
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute("DELETE FROM chamados WHERE status = 'fechado'")

        resultado = database.listar_chamados(self.caminho_banco, "fechado")

        self.assertEqual(resultado, "Nenhum chamado encontrado.")

    def test_base_sem_chamados_retorna_mensagem(self) -> None:
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute("DELETE FROM chamados")

        resultado = database.listar_chamados(self.caminho_banco)

        self.assertEqual(resultado, "Nenhum chamado encontrado.")

    def test_status_invalido_gera_erro_antes_de_acessar_o_banco(self) -> None:
        with patch.object(database, "conectar_banco") as conectar:
            with self.assertRaisesRegex(ValueError, "Status inválido"):
                database.listar_chamados(self.caminho_banco, "ABERTO")

        conectar.assert_not_called()

    def test_filtro_status_usa_parametro_sql(self) -> None:
        conexao = MagicMock()
        conexao.__enter__.return_value = conexao
        conexao.execute.return_value.fetchall.return_value = []

        with patch.object(database, "conectar_banco", return_value=conexao):
            resultado = database.listar_chamados(self.caminho_banco, "aberto")

        self.assertEqual(resultado, "Nenhum chamado encontrado.")
        instrucao, parametros = conexao.execute.call_args.args
        self.assertIn("WHERE status = ?", instrucao)
        self.assertEqual(parametros, ("aberto",))

    def test_tool_mcp_expoe_e_filtra_a_listagem(self) -> None:
        async def chamar_tool() -> tuple[list[str], object]:
            ambiente = os.environ.copy()
            ambiente["HELPDESK_DB_PATH"] = str(self.caminho_banco)
            transporte = StdioTransport(
                command=sys.executable,
                args=["-m", "helpdesk_mcp.server"],
                env=ambiente,
                cwd=str(Path(__file__).resolve().parents[1]),
            )
            async with Client(transporte) as cliente:
                ferramentas = await cliente.list_tools()
                resultado = await cliente.call_tool(
                    "listar_chamados", {"status": "aberto"}
                )
                return [ferramenta.name for ferramenta in ferramentas], resultado

        nomes_ferramentas, resultado = asyncio.run(chamar_tool())

        self.assertEqual(nomes_ferramentas, ["listar_chamados"])
        self.assertFalse(resultado.is_error)
        self.assertEqual(
            resultado.structured_content["result"][0]["status"], "aberto"
        )


class TestarInicializacaoBanco(unittest.TestCase):
    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.diretorio.name) / "subdiretorio" / "demo.sqlite3"

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def test_cria_esquema_indices_dados_demo_e_historico(self) -> None:
        database.inicializar_banco(self.caminho_banco)

        with database.conectar_banco(self.caminho_banco) as conexao:
            self.assertEqual(
                conexao.execute("SELECT COUNT(*) FROM chamados").fetchone()[0], 4
            )
            self.assertEqual(
                conexao.execute("SELECT COUNT(*) FROM clientes").fetchone()[0], 3
            )
            self.assertEqual(
                conexao.execute(
                    "SELECT COUNT(*) FROM historico_status_chamado"
                ).fetchone()[0],
                4,
            )
            emails = [
                linha[0]
                for linha in conexao.execute("SELECT email FROM clientes ORDER BY id")
            ]
            self.assertEqual(len(emails), len(set(emails)))
            indices = {
                linha[1]
                for linha in conexao.execute("PRAGMA index_list(chamados)")
            }
            self.assertIn("idx_chamados_status", indices)
            self.assertIn("idx_chamados_cliente_criado", indices)
            indices_historico = {
                linha[1]
                for linha in conexao.execute(
                    "PRAGMA index_list(historico_status_chamado)"
                )
            }
            self.assertIn("idx_historico_chamado_alterado", indices_historico)

    def test_inicializacao_repetida_nao_duplica_dados(self) -> None:
        database.inicializar_banco(self.caminho_banco)
        antes = database.listar_chamados(self.caminho_banco)

        database.inicializar_banco(self.caminho_banco)
        depois = database.listar_chamados(self.caminho_banco)

        self.assertEqual(depois, antes)
        with database.conectar_banco(self.caminho_banco) as conexao:
            self.assertEqual(
                conexao.execute(
                    "SELECT COUNT(*) FROM historico_status_chamado"
                ).fetchone()[0],
                4,
            )

    def test_preserva_chamados_existentes_sem_adicionar_demo(self) -> None:
        database.inicializar_banco(self.caminho_banco)
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute("DELETE FROM historico_status_chamado")
            conexao.execute("DELETE FROM chamados")
            conexao.execute("DELETE FROM clientes")
            conexao.execute(
                """
                INSERT INTO clientes (id, nome, email)
                VALUES (20, 'Cliente existente', 'existente@example.test')
                """
            )
            conexao.execute(
                """
                INSERT INTO chamados (
                    id, cliente_id, descricao, status, criado_em, atualizado_em
                ) VALUES (
                    20, 20, 'Não substituir', 'aberto',
                    '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00'
                )
                """
            )

        database.inicializar_banco(self.caminho_banco)

        resultado = database.listar_chamados(self.caminho_banco)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["descricao"], "Não substituir")
        with database.conectar_banco(self.caminho_banco) as conexao:
            self.assertEqual(
                conexao.execute("SELECT COUNT(*) FROM clientes").fetchone()[0], 1
            )

    def test_falha_na_carga_reverte_esquema_e_dados(self) -> None:
        with patch.object(
            database,
            "_inserir_dados_de_demonstracao",
            side_effect=RuntimeError("falha simulada"),
        ):
            with self.assertRaisesRegex(RuntimeError, "falha simulada"):
                database.inicializar_banco(self.caminho_banco)

        self.assertTrue(self.caminho_banco.exists())
        with sqlite3.connect(self.caminho_banco) as conexao:
            tabelas = conexao.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        self.assertEqual(tabelas, [])


if __name__ == "__main__":
    unittest.main()
