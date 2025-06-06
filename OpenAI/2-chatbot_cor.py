import openai

from colorama import Fore, Style, init

client = openai.Client()

init(autoreset=True)

def geracao_texto(mensagens):

    respostas = client.chat.completions.create(
        messages=mensagens,
        model="gpt-3.5-turbo-0125",
        max_tokens=1000,
        temperature=0,
        stream=True
    )

    print(f"{Fore.CYAN}Bot :", end="")

    texto_completo = ""
    for resposta_stream in respostas:
        texto = resposta_stream.choices[0].delta.content
        if texto:
            print(texto, end='')
            texto_completo += texto
    print()
    mensagens.append({"role": "assistant", "content": texto_completo})
    return mensagens

if __name__ == "__main__":
    print(f"{Fore.YELLOW}Olá! Eu sou um chatbot 🤖. Como posso ajudar você hoje?")

    mensagens = []
    while True:
        in_user = input(f"{Fore.GREEN}User: {Style.RESET_ALL}")
        mensagens.append({"role": "user", "content": in_user})
        mensagens = geracao_texto(mensagens)
