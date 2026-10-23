import asyncio

import streamlit as st
from fastmcp.exceptions import ToolError
from openai import OpenAIError

from assistente_ia import decidir_proximo_passo, descrever_alteracao
from mcp_client import executar_tool


def _executar_tool(nome_tool: str, argumentos: dict[str, int | str | None]) -> str:
    return asyncio.run(executar_tool(nome_tool, argumentos))


st.set_page_config(page_title="Helpdesk", page_icon="💬")
st.title("Helpdesk — atendimento")
st.markdown(
    "Faça perguntas em linguagem natural sobre chamados. O histórico da "
    "conversa fica disponível durante a sessão atual."
)
st.info(
    "Por exemplo: “Quais chamados estão abertos?”, “O que aconteceu com os "
    "chamados do cliente 2?” ou “Feche o chamado 3”. Para atualizar um chamado, "
    "você precisará confirmar a alteração antes de gravá-la. Esta demonstração "
    "usa dados fictícios."
)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {
            "role": "assistant",
            "content": (
                "Olá! Posso listar chamados, consultar o histórico de um "
                "cliente ou atualizar o status de um chamado."
            ),
        }
    ]
if "alteracao_pendente" not in st.session_state:
    st.session_state.alteracao_pendente = None

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

alteracao_pendente = st.session_state.alteracao_pendente
if alteracao_pendente is not None:
    st.warning(descrever_alteracao(alteracao_pendente["argumentos"]))
    coluna_confirmar, coluna_cancelar = st.columns(2)
    if coluna_confirmar.button("Confirmar alteração", type="primary"):
        try:
            with st.spinner("Atualizando o chamado..."):
                resposta = _executar_tool(
                    alteracao_pendente["nome_tool"],
                    alteracao_pendente["argumentos"],
                )
        except (OSError, TimeoutError, ToolError, RuntimeError) as erro:
            resposta = f"Não foi possível concluir a operação: {erro}"
        st.session_state.mensagens.append(
            {"role": "assistant", "content": resposta}
        )
        st.session_state.alteracao_pendente = None
        st.rerun()
    if coluna_cancelar.button("Cancelar"):
        st.session_state.mensagens.append(
            {
                "role": "assistant",
                "content": "Alteração cancelada. O chamado não foi modificado.",
            }
        )
        st.session_state.alteracao_pendente = None
        st.rerun()

if texto_usuario := st.chat_input(
    "Faça uma pergunta sobre os chamados",
    disabled=alteracao_pendente is not None,
):
    st.session_state.mensagens.append(
        {"role": "user", "content": texto_usuario}
    )
    try:
        with st.spinner("Entendendo sua pergunta..."):
            decisao = decidir_proximo_passo(st.session_state.mensagens)
        if decisao.nome_tool is None:
            resposta = decisao.resposta
            if resposta is None:
                raise RuntimeError("O modelo retornou uma decisão sem resposta.")
            st.session_state.mensagens.append(
                {"role": "assistant", "content": resposta}
            )
        elif decisao.argumentos is None:
            raise RuntimeError("O modelo retornou uma ferramenta sem argumentos.")
        elif decisao.nome_tool == "atualizar_status":
            st.session_state.alteracao_pendente = {
                "nome_tool": decisao.nome_tool,
                "argumentos": decisao.argumentos,
            }
            st.session_state.mensagens.append(
                {
                    "role": "assistant",
                    "content": "Preparei uma alteração para sua confirmação.",
                }
            )
        else:
            with st.spinner("Consultando o servidor de helpdesk..."):
                resposta = _executar_tool(decisao.nome_tool, decisao.argumentos)
            st.session_state.mensagens.append(
                {"role": "assistant", "content": resposta}
            )
    except (OpenAIError, OSError, TimeoutError, ToolError, ValueError) as erro:
        st.session_state.mensagens.append(
            {
                "role": "assistant",
                "content": f"Não foi possível processar a solicitação: {erro}",
            }
        )
    st.rerun()
