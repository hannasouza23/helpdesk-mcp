import asyncio

import streamlit as st
from fastmcp.exceptions import ToolError

from mcp_client import executar_tool, interpretar_comando


st.set_page_config(page_title="Helpdesk", page_icon="💬")
st.title("Helpdesk — atendimento")
st.markdown(
    "Consulte e atualize chamados com comandos simples. O histórico da "
    "conversa fica disponível durante a sessão atual."
)
st.info(
    "Exemplos: `listar abertos`, `histórico do cliente 2` e "
    "`alterar chamado 3 para fechado`. Status aceitos: aberto, em andamento, "
    "resolvido e fechado. Esta demonstração usa dados fictícios."
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

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

if texto_usuario := st.chat_input("Digite sua mensagem"):
    st.session_state.mensagens.append(
        {"role": "user", "content": texto_usuario}
    )
    try:
        nome_tool, argumentos = interpretar_comando(texto_usuario)
    except ValueError as erro:
        resposta = str(erro)
    else:
        try:
            with st.spinner("Consultando o servidor de helpdesk..."):
                resposta = asyncio.run(executar_tool(nome_tool, argumentos))
        except (OSError, TimeoutError, ToolError) as erro:
            resposta = f"Não foi possível concluir a operação: {erro}"
    st.session_state.mensagens.append(
        {"role": "assistant", "content": resposta}
    )
    st.rerun()
