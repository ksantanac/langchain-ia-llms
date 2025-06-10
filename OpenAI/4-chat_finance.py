import yfinance as yf
import openai
import json

client = openai.Client()

def cotacao(ticker, periodo="1mo"):
    # Obtém o objeto Ticker do Yahoo Finance (adiciona .SA para ações brasileiras)
    ticker_obj = yf.Ticker(f"{ticker}.SA")
    
    # Obtém o histórico de preços de fechamento
    hist = ticker_obj.history(period=periodo)["Close"]
    
    # Formata as datas e arredonda os valores
    hist.index = hist.index.strftime("%Y-%m-%d")
    hist = round(hist, 2)
    
    # Limita a 30 resultados para não sobrecarregar o modelo
    if len(hist) > 30:
        slice_size = int(len(hist) / 30) 
        hist = hist.iloc[::-slice_size][::-1]
    
    return hist.to_json()

tools = [
    {
        "type": "function",
        "function": {
            "name": "cotacao",
            "description": "Retorna a cotação de uma ação da B3 (Brasil) em formato JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "O ticker da ação na B3 (exemplo: PETR4, VALE3)."
                    },
                    "periodo": {
                        "type": "string",
                        "description": "O período para o qual se deseja obter a cotação. Padrão é '1mo'.",
                        "enum": ["1d", "5d", "1mo", "6mo", "1y", "5y", "10y", "ytd", "max"]
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]

funcao_disponivel = {"cotacao": cotacao}

mensagens = [{"role": "user", "content": "Qual é a cotaçaõ da Bradesco no ultimo ano?"}]

resposta = client.chat.completions.create(
    messages=mensagens,
    model="gpt-3.5-turbo-0125",
    tools=tools,
    tool_choice="auto",
)

tool_calls = resposta.choices[0].message.tool_calls
# print(tool_calls)

if tool_calls:
    mensagens.append(resposta.choices[0].message)
    for tool_call in tool_calls:

        # 1. Primeiro, extraímos os dados da chamada de forma organizada
        function_name = tool_call.function.name

        # 2. Convertemos os argumentos para um dicionário Python
        function_args = json.loads(tool_call.function.arguments)

        # 3. Buscamos a função correspondente no nosso dicionário
        function_to_call = funcao_disponivel[function_name]

        # 4. Executamos a função com os argumentos
        function_return = function_to_call(**function_args)

        mensagens.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_return,
            }
        )

        segunda_resposta = client.chat.completions.create(
            messages=mensagens,
            model="gpt-3.5-turbo-0125",
        )

        mensagens.append(segunda_resposta.choices[0].message)
        print(segunda_resposta.choices[0].message.content)