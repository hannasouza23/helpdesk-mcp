import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from openai.types.chat import ChatCompletionMessageFunctionToolCall
from openai.types.chat.chat_completion_message_function_tool_call import (
    Function as ChamadaDeFuncao,
)
from streamlit.testing.v1 import AppTest

from app import assistente_ia
from app.assistente_ia import (
    DecisaoAssistente,
    decidir_proximo_passo,
    descrever_alteracao,
)
from src import database


def resposta_modelo(
    conteudo: str | None = None,
    chamada: tuple[str, dict[str, object]] | None = None,
) -> SimpleNamespace:
    chamadas = []
    if chamada is not None:
        nome, argumentos = chamada
        chamadas = [
            ChatCompletionMessageFunctionToolCall(
                id="chamada-teste",
                type="function",
                function=ChamadaDeFuncao(
                    name=nome,
                    arguments=json.dumps(argumentos),
                ),
            )
        ]
    mensagem = SimpleNamespace(content=conteudo, tool_calls=chamadas)
    return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)])


class TestarSelecaoDeToolsPeloModelo(unittest.TestCase):
    def setUp(self) -> None:
        self.ambiente = patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "chave-de-teste",
                "OPENAI_BASE_URL": "https://modelo.example/v1",
                "OPENAI_MODEL": "modelo-teste",
            },
        )
        self.ambiente.start()
        self.addCleanup(self.ambiente.stop)

    @patch("app.assistente_ia.OpenAI")
    def test_modelo_seleciona_tool_de_consulta(
        self, criar_cliente: MagicMock
    ) -> None:
        cliente = criar_cliente.return_value
        cliente.chat.completions.create.return_value = resposta_modelo(
            chamada=("listar_chamados", {"status": "aberto"})
        )

        decisao = decidir_proximo_passo(
            [{"role": "user", "content": "Quais chamados estão abertos?"}]
        )

        self.assertEqual(
            decisao,
            DecisaoAssistente(
                "listar_chamados", {"status": "aberto"}, None
            ),
        )
        parametros = cliente.chat.completions.create.call_args.kwargs
        self.assertEqual(parametros["tool_choice"], "auto")
        self.assertFalse(parametros["parallel_tool_calls"])
        self.assertEqual(
            {tool["function"]["name"] for tool in parametros["tools"]},
            {
                "listar_chamados",
                "buscar_historico_cliente",
                "atualizar_status",
            },
        )

    @patch("app.assistente_ia.OpenAI")
    def test_modelo_pode_responder_sem_chamar_tool(
        self, criar_cliente: MagicMock
    ) -> None:
        cliente = criar_cliente.return_value
        cliente.chat.completions.create.return_value = resposta_modelo(
            conteudo="Qual é o identificador do cliente?"
        )

        decisao = decidir_proximo_passo(
            [{"role": "user", "content": "Quero consultar um histórico"}]
        )

        self.assertEqual(
            decisao,
            DecisaoAssistente(
                nome_tool=None,
                argumentos=None,
                resposta="Qual é o identificador do cliente?",
            ),
        )

    @patch("app.assistente_ia.OpenAI")
    def test_alteracao_retorna_plano_sem_executar_tool(
        self, criar_cliente: MagicMock
    ) -> None:
        cliente = criar_cliente.return_value
        cliente.chat.completions.create.return_value = resposta_modelo(
            chamada=(
                "atualizar_status",
                {"chamado_id": 3, "novo_status": "fechado"},
            )
        )

        decisao = decidir_proximo_passo(
            [{"role": "user", "content": "Feche o chamado 3"}]
        )

        self.assertEqual(
            decisao.nome_tool,
            "atualizar_status",
        )
        self.assertEqual(
            descrever_alteracao(decisao.argumentos or {}),
            "Confirmar alteração do chamado #3 para o status **Fechado**? "
            "O banco só será atualizado se você confirmar.",
        )

    @patch("app.assistente_ia.OpenAI")
    def test_rejeita_ferramenta_e_argumentos_invalidos(
        self, criar_cliente: MagicMock
    ) -> None:
        cliente = criar_cliente.return_value
        mensagens = [{"role": "user", "content": "Atualize o chamado"}]
        for nome, argumentos in (
            ("ferramenta_inexistente", {}),
            ("atualizar_status", {"chamado_id": True, "novo_status": "fechado"}),
            ("atualizar_status", {"chamado_id": 3, "novo_status": "pendente"}),
            ("buscar_historico_cliente", {"cliente_id": 2, "extra": "valor"}),
        ):
            with self.subTest(nome=nome, argumentos=argumentos):
                cliente.chat.completions.create.return_value = resposta_modelo(
                    chamada=(nome, argumentos)
                )
                with self.assertRaises(ValueError):
                    decidir_proximo_passo(mensagens)

    @patch.object(assistente_ia, "OpenAI")
    def test_schema_de_listagem_envia_status_nulo_quando_sem_filtro(
        self, criar_cliente: MagicMock
    ) -> None:
        cliente = criar_cliente.return_value
        cliente.chat.completions.create.return_value = resposta_modelo(
            chamada=("listar_chamados", {"status": None})
        )

        decisao = decidir_proximo_passo(
            [{"role": "user", "content": "Liste todos"}]
        )

        self.assertEqual(
            decisao,
            DecisaoAssistente("listar_chamados", {"status": None}, None),
        )

    def test_exige_configuracao_do_modelo(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
                decidir_proximo_passo(
                    [{"role": "user", "content": "Liste os chamados"}]
                )


class TestarConfirmacaoNaInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.diretorio = tempfile.TemporaryDirectory()
        self.caminho_banco = Path(self.diretorio.name) / "helpdesk.sqlite3"
        database.inicializar_banco(self.caminho_banco)

    def tearDown(self) -> None:
        self.diretorio.cleanup()

    def _status_chamado(self) -> str:
        with database.conectar_banco(self.caminho_banco) as conexao:
            linha = conexao.execute(
                "SELECT status FROM chamados WHERE id = 3"
            ).fetchone()
        assert linha is not None
        return linha["status"]

    def _abrir_confirmacao(self) -> AppTest:
        caminho_app = Path(__file__).resolve().parents[1] / "app" / "app.py"
        app = AppTest.from_file(str(caminho_app)).run()
        app.session_state["alteracao_pendente"] = {
            "nome_tool": "atualizar_status",
            "argumentos": {"chamado_id": 3, "novo_status": "fechado"},
        }
        return app.run()

    def test_banco_so_muda_apos_clique_explicito_de_confirmacao(self) -> None:
        with patch.dict(
            os.environ, {"HELPDESK_DB_PATH": str(self.caminho_banco)}
        ):
            app = self._abrir_confirmacao()
            self.assertEqual(self._status_chamado(), "resolvido")
            self.assertIn("Confirmar alteração", [botao.label for botao in app.button])

            app.button[0].click().run()

        self.assertEqual(self._status_chamado(), "fechado")
        self.assertIsNone(app.session_state["alteracao_pendente"])
        self.assertIn(
            "atualizado com sucesso",
            app.session_state["mensagens"][-1]["content"],
        )

    def test_cancelar_nao_altera_o_banco(self) -> None:
        with patch.dict(
            os.environ, {"HELPDESK_DB_PATH": str(self.caminho_banco)}
        ):
            app = self._abrir_confirmacao()
            app.button[1].click().run()

        self.assertEqual(self._status_chamado(), "resolvido")
        self.assertIsNone(app.session_state["alteracao_pendente"])
        self.assertIn("cancelada", app.session_state["mensagens"][-1]["content"])


if __name__ == "__main__":
    unittest.main()
