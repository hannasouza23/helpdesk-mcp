import streamlit as st


st.set_page_config(page_title="Helpdesk", page_icon="💬")
st.title("Helpdesk — atendimento")
st.markdown(
    "Use o campo abaixo para escrever uma mensagem e acompanhar a conversa. "
    "Este protótipo mantém o histórico apenas durante a sessão atual e ainda "
    "não está conectado ao servidor MCP."
)
st.info(
    "Não inclua dados reais de clientes. As mensagens não são encaminhadas "
    "nem processadas pelas ferramentas de chamados."
)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {
            "role": "assistant",
            "content": (
                "Olá! Como posso ajudar? Descreva sua solicitação para "
                "visualizá-la nesta conversa."
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
    resposta = (
        "Sua mensagem foi adicionada à conversa desta sessão. "
        "A integração com o assistente e com as ferramentas de chamados "
        "ainda não está disponível."
    )
    st.session_state.mensagens.append(
        {"role": "assistant", "content": resposta}
    )
    st.rerun()
