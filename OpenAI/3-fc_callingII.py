import json
import openai
from dotenv import load_dotenv, find_dotenv

client = openai.Client()

# Função para calcular o IMC e fornecer recomendação
def calcular_imc(peso, altura):
    imc = peso / (altura ** 2)
    if imc < 18.5:
        estado = "abaixo do peso"
        recomendacao = "É importante que você consulte um médico para ajustar sua alimentação."
    elif 18.5 <= imc < 24.9:
        estado = "peso normal"
        recomendacao = "Continue mantendo hábitos saudáveis!"
    elif 25 <= imc < 29.9:
        estado = "sobrepeso"
        recomendacao = "Você pode considerar uma reavaliação de sua dieta e exercícios físicos."
    else:
        estado = "obesidade"
        recomendacao = "É altamente recomendável consultar um médico para orientações sobre perda de peso."
    
    return json.dumps({
        "imc": imc,
        "estado": estado,
        "recomendacao": recomendacao
    })

tools = [
    {
        "type": "function",
        "function": {
            "name": "calcular_imc",
            "description": "Calcula o IMC de uma pessoa e fornece uma recomendação de saúde",
            "parameters": {
                "type": "object",
                "properties": {
                    "peso": {"type": "number", 
                             "description": "Peso da pessoa em kg"},
                    "altura": {"type": "number", 
                               "description": "Altura da pessoa em metros"}
                },
                "required": ["peso", "altura"],
            },
        },
    }
]

funcoes_disponiveis = {
    "calcular_imc": calcular_imc,
}

mensagens = [
    {"role": "user", "content":
        "Qual é o IMC de uma pessoa que pesa 90 kg e tem 1.50 m de altura?"}
]

resposta = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=mensagens,
    tools=tools,
    tool_choice="auto",
)

mensagem_resp = resposta.choices[0].message
tool_calls = mensagem_resp.tool_calls

if tool_calls:
    mensagens.append(mensagem_resp)
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = funcoes_disponiveis[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(
            peso=function_args.get("peso"),
            altura=function_args.get("altura"),
        )
        mensagens.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
        )
    segunda_resposta = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=mensagens,
    )

mensagem_resp = segunda_resposta.choices[0].message
print(mensagem_resp.content)
