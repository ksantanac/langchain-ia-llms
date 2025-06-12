import yfinance as yf
import openai
import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

# Inicializa cliente OpenAI
client = openai.Client()

# Função para obter a cotação
def cotacao(ticker, periodo="1mo"):
    try:
        ticker_obj = yf.Ticker(f"{ticker}.SA")
        hist = ticker_obj.history(period=periodo)["Close"]

        if hist.empty:
            return json.dumps({"erro": f"O ticker '{ticker}' não retornou dados."})

        hist.index = hist.index.map(lambda x: x.strftime("%Y-%m-%d"))
        hist = round(hist, 2)

        if len(hist) > 30:
            slice_size = int(len(hist) / 30) 
            hist = hist.iloc[::-slice_size][::-1]

        return json.dumps({
            "ticker": ticker,
            "periodo": periodo,
            "dados": hist.to_dict()
        })

    except Exception as e:
        return json.dumps({"erro": str(e)})

# Ferramentas
tools = [{
    "type": "function",
    "function": {
        "name": "cotacao",
        "description": "Retorna a cotação de uma ação da B3 (Brasil) em formato JSON.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker da ação na B3 (ex: PETR4, VALE3)."
                },
                "periodo": {
                    "type": "string",
                    "description": "Período da cotação",
                    "enum": ["1d", "5d", "1mo", "6mo", "1y", "5y", "10y", "ytd", "max"]
                }
            },
            "required": ["ticker"]
        }
    }
}]
funcao_disponivel = {"cotacao": cotacao}

# Função que interage com o modelo
def gerar_texto(mensagens):
    resposta = client.chat.completions.create(
        messages=mensagens,
        model="gpt-3.5-turbo-0125",
        tools=tools,
        tool_choice="auto"
    )
    tool_calls = resposta.choices[0].message.tool_calls

    if tool_calls:
        mensagens.append(resposta.choices[0].message.to_dict())

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            function_to_call = funcao_disponivel[function_name]
            function_return = function_to_call(**function_args)

            mensagens.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_return,
            })

        segunda_resposta = client.chat.completions.create(
            messages=mensagens,
            model="gpt-3.5-turbo-0125",
        )
        mensagens.append(segunda_resposta.choices[0].message.to_dict())
    else:
        mensagens.append(resposta.choices[0].message.to_dict())

    return mensagens

# Função de gráfico com matplotlib
def exibir_grafico_json(json_str):
    try:
        data_dict = json.loads(json_str)
        if "erro" in data_dict:
            st.error(data_dict["erro"])
            return

        dados = pd.Series(data_dict["dados"])
        ticker = data_dict.get("ticker", "")
        periodo = data_dict.get("periodo", "")

        if dados.empty:
            st.warning("Sem dados para exibir.")
            return

        fig, ax = plt.subplots(figsize=(8, 4))
        dados.plot(ax=ax)
        ax.set_title(f"Histórico de {ticker.upper()} - Período: {periodo}", fontsize=14)
        ax.set_ylabel("Preço (R$)")
        ax.set_xlabel("Data")
        ax.grid(True)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Erro ao exibir gráfico: {e}")

# === Streamlit ===
st.set_page_config(page_title="Chatbot Financeiro", page_icon="📊")

st.title("🤖 Chatbot de Cotações da B3 📈")


# Estado de mensagens
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Botão para limpar chat
if st.button("🧹 Limpar Conversa"):
    st.session_state.mensagens = []
    st.rerun()

# Exibir histórico do chat
for msg in st.session_state.mensagens:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").markdown(msg["content"])
    elif msg["role"] == "tool":
        with st.chat_message("assistant"):
            data = json.loads(msg["content"])
            if "erro" in data:
                st.error(data["erro"])
            else:
                exibir_grafico_json(msg["content"])

# Entrada do usuário
user_input = st.chat_input("Pergunte algo como: Cotação da PETR4 nos últimos 6 meses")
if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.mensagens.append({"role": "user", "content": user_input})

    with st.spinner("Consultando..."):
        st.session_state.mensagens = gerar_texto(st.session_state.mensagens)

    ultima_msg = st.session_state.mensagens[-1]
    if ultima_msg["role"] == "assistant":
        st.chat_message("assistant").markdown(ultima_msg["content"])

# Exportar histórico como CSV
if st.session_state.mensagens:
    if st.download_button("💾 Exportar conversa como CSV", data=pd.DataFrame(st.session_state.mensagens).to_csv(index=False), file_name="conversa_chatbot.csv", mime="text/csv"):
        st.success("Download iniciado com sucesso!")

