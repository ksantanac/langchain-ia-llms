import streamlit as st
import openai
import time

# Inicialização
if "client" not in st.session_state:
    st.session_state.client = openai.Client()
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("💬 Análise de Dados com GPT-4o e CSV")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("📁 Faça upload do seu arquivo CSV", type=["csv"])

if uploaded_file and st.session_state.assistant_id is None:
    with st.spinner("🔄 Enviando arquivo e criando assistente..."):
        client = st.session_state.client

        file = client.files.create(
            file=uploaded_file,
            purpose="assistants"
        )

        assistant = client.beta.assistants.create(
            name="Analista de Dados",
            instructions=(
                "Você é um analista de dados experiente. "
                "Ao responder perguntas, sempre explique passo a passo como chegou à resposta. "
                "Se usar cálculos ou análise de dados com código, mostre o código Python usado, "
                "os resultados intermediários e a interpretação final. Seja didático."
            ),
            tools=[{"type": "code_interpreter"}],
            tool_resources={"code_interpreter": {"file_ids": [file.id]}},
            model="gpt-4o",
        )

        thread = client.beta.threads.create()

        st.session_state.assistant_id = assistant.id
        st.session_state.file_id = file.id
        st.session_state.thread_id = thread.id

        st.success("✅ Arquivo enviado e assistente pronto para conversar!")

# Mostrar histórico do chat
if st.session_state.assistant_id:
    st.markdown("### 💬 Histórico de Conversa")

    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"**🧑‍💻 Você:** {chat['content']}")
        else:
            st.markdown(f"**🤖 Assistente:** {chat['content']}")

    st.markdown("---")

    # Inicializa o campo de pergunta, se ainda não existir
if "pergunta_input" not in st.session_state:
    
    st.session_state.pergunta_input = ""

# Mostrar campo de chat apenas após upload do arquivo e criação do assistente
if st.session_state.assistant_id:
    pergunta = st.chat_input("Faça uma pergunta relacionada ao arquivo carregado...")

    if pergunta is not None and pergunta.strip():
        with st.spinner("⏳ Processando..."):
            client = st.session_state.client
            thread_id = st.session_state.thread_id
            assistant_id = st.session_state.assistant_id

            st.session_state.chat_history.append({
                "role": "user",
                "content": pergunta
            })

            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=pergunta
            )

            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions=(
                    "Responda como um analista de dados experiente. "
                    "Mostre o código utilizado (em Python), explique o que ele faz, "
                    "e descreva os passos realizados para chegar à resposta. "
                    "Se possível, mostre os dados ou resultados intermediários. "
                    "Nunca dê apenas a resposta direta."
                )
            )

            while run.status in ["queued", "in_progress", "cancelling"]:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

            if run.status == "completed":
                mensagens = client.beta.threads.messages.list(
                    thread_id=thread_id
                )

                resposta = mensagens.data[0].content[0].text.value

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": resposta
                })

                st.rerun()
            else:
                st.error(f"Ocorreu um erro: {run.status}")