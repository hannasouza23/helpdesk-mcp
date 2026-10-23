import asyncio
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.mcp_client import _formatar_data, executar_tool, interpretar_comando
from src import database


class TestarInterpretacaoComandos(unittest.TestCase):
    def test_interpreta_comandos_das_tres_tools(self) -> None:
        self.assertEqual(
            interpretar_comando("listar abertos"),
            ("listar_chamados", {"status": "aberto"}),
        )
        self.assertEqual(
            interpretar_comando("histórico do cliente 2"),
            ("buscar_historico_cliente", {"cliente_id": 2}),
        )
        self.assertEqual(
            interpretar_comando("alterar chamado 3 para fechado"),
            (
                "atualizar_status",
                {"chamado_id": 3, "novo_status": "fechado"},
            ),
        )

    def test_aceita_variacoes_de_acentos_e_status(self) -> None:
        self.assertEqual(
            interpretar_comando("LISTAR EM ANDAMENTO"),
            ("listar_chamados", {"status": "em_andamento"}),
        )
        self.assertEqual(
            interpretar_comando("atualizar chamado 3 para em_andamento"),
            (
                "atualizar_status",
                {"chamado_id": 3, "novo_status": "em_andamento"},
            ),
        )

    def test_listar_sem_filtro_lista_todos(self) -> None:
        self.assertEqual(
            interpretar_comando("listar"),
            ("listar_chamados", {"status": None}),
        )

    def test_comando_desconhecido_exibe_orientacao(self) -> None:
        with self.assertRaisesRegex(ValueError, "Comandos disponíveis"):
            interpretar_comando("oi, preciso de ajuda")

    def test_status_invalido_exibe_status_aceitos(self) -> None:
        with self.assertRaisesRegex(ValueError, "Status inválido"):
            interpretar_comando("alterar chamado 3 para pendente")


class TestarClienteMcpApp(unittest.TestCase):
    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.diretorio.name) / "helpdesk.sqlite3"
        database.inicializar_banco(self.caminho_banco)

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def test_comandos_invocam_tools_e_exibem_resultados(self) -> None:
        with patch.dict(
            os.environ, {"HELPDESK_DB_PATH": str(self.caminho_banco)}
        ):
            resposta_lista = asyncio.run(
                executar_tool(
                    *interpretar_comando("listar abertos")
                )
            )
            resposta_historico = asyncio.run(
                executar_tool(
                    *interpretar_comando("histórico do cliente 2")
                )
            )
            resposta_atualizacao = asyncio.run(
                executar_tool(
                    *interpretar_comando(
                        "alterar chamado 3 para fechado"
                    )
                )
            )

        self.assertIn("**Chamados encontrados: 1**", resposta_lista)
        self.assertIn("**Chamado #1 — Aberto**", resposta_lista)
        self.assertIn("10/01/2025 às 06:00 UTC-3", resposta_lista)
        self.assertIn("**Histórico do cliente #2**", resposta_historico)
        self.assertIn("**Movimentações:**", resposta_historico)
        self.assertIn("11/01/2025 às 07:30 UTC-3", resposta_historico)
        self.assertIn("**Chamado #3 atualizado com sucesso.**", resposta_atualizacao)
        self.assertIn("Novo status: **Fechado**", resposta_atualizacao)

    def test_lista_vazia_e_atualizacao_sem_mudanca_tem_mensagens_claras(self) -> None:
        with database.conectar_banco(self.caminho_banco) as conexao:
            conexao.execute(
                """
                INSERT INTO clientes (id, nome, email)
                VALUES (4, 'Cliente sem chamados', 'sem-chamados@example.test')
                """
            )

        with patch.dict(
            os.environ, {"HELPDESK_DB_PATH": str(self.caminho_banco)}
        ):
            resposta_historico = asyncio.run(
                executar_tool(
                    "buscar_historico_cliente", {"cliente_id": 4}
                )
            )
            resposta_sem_mudanca = asyncio.run(
                executar_tool(
                    "atualizar_status",
                    {"chamado_id": 3, "novo_status": "resolvido"},
                )
            )

        self.assertEqual(
            resposta_historico, "Esse cliente ainda não possui chamados."
        )
        self.assertIn("já está com status **Resolvido**", resposta_sem_mudanca)

    def test_horario_converte_para_utc_menos_tres_e_ajusta_data(self) -> None:
        self.assertEqual(
            _formatar_data("2025-01-10T02:00:00+00:00"),
            "09/01/2025 às 23:00 UTC-3",
        )
        self.assertEqual(
            _formatar_data("2025-01-10T09:00:00+00:00"),
            "10/01/2025 às 06:00 UTC-3",
        )
        self.assertEqual(
            _formatar_data("2025-01-10T09:00:00"),
            "10/01/2025 às 06:00 UTC-3",
        )
