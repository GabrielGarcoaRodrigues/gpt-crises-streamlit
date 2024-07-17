import pandas as pd
import asyncio
import aiohttp
import json
import datetime
from utils_files import *


headers = {
    'Authorization': f'Bearer {st.secrets["API_KEY"]}',
    'Content-Type': 'application/json'
}

description = """
Você é um analista de crises de marcas e trabalha para a marca Ambev. 
O usuário irá inserir uma lista de comentários de redes sociais.
Seu trabalho é ler TODOS os comentários e fazer as análises solicitadas a partir do contexto dado.
"""

prompt_final = '''
Analise TODOS os comentários do contexto e faça as seguintes tarefas:
1. Faça a quantificação total dos sentimentos, mostrando somente o resultado final da soma de todos os comentários analisados juntamente com o percentual em relação ao total;
2. Crie 5 categorias em formato de uma frase curta a partir de todas as categrias criadas, mostrando também a quantidade de comentários relacionados a cada categoria  além de uma pequena lista com algumas palavras chave relacionadas a categoria. Além disso Para cada categoria criada, gere um comentário curto que esteja no mesmo modelo dos comentários analisados e que sintetize a maior parte dos comentários relacionados a categoria. Gere uma breve descrição de cada categoria baseado nos comentários; 
3. Faça um breve resumos dos comentários que não estão relacionados a nenhuma das categorias.
4. Faça uma breve análise dos comentários positivos, neutros e negativos;
5. Faça uma análise única juntando quantitaiva e qualitativa dos comentários.
'''

#def dividir_dataframe_em_blocos(df, tamanho_bloco=120):
#    if 'Texto' not in df.columns:
#        raise ValueError("A coluna 'Texto' não está presente no DataFrame.")
#
#    num_blocos = (len(df) + tamanho_bloco - 1) // tamanho_bloco
#    lista_de_textos_bloco = [df['Texto'][i*tamanho_bloco:(i+1)*tamanho_bloco].tolist() for i in range(num_blocos)]
#    
#    return lista_de_textos_bloco
def dividir_texto_em_blocos(texto, max_tokens=2048):
    palavras = texto.split()
    blocos = []
    bloco_atual = []
    tamanho_atual = 0
    
    for palavra in palavras:
        tamanho_palavra = len(palavra)
        if tamanho_atual + tamanho_palavra + 1 > max_tokens:  # +1 para o espaço
            blocos.append(" ".join(bloco_atual))
            bloco_atual = [palavra]
            tamanho_atual = tamanho_palavra
        else:
            bloco_atual.append(palavra)
            tamanho_atual += tamanho_palavra + 1  # +1 para o espaço

    if bloco_atual:
        blocos.append(" ".join(bloco_atual))

    return blocos
    
def concatena_textos_blocos(blocos_de_textos):    
    lista_de_strings = []
    for bloco in blocos_de_textos:
        # Concatenar os textos do bloco com quebra de linha entre eles
        texto_concatenado = '\n'.join(bloco)
        lista_de_strings.append(texto_concatenado)
    
    return lista_de_strings

async def make_api_call_to_gpt(prompt):
    print(f"##### Calling API...: {datetime.datetime.now()}")
    # print(prompt)
    async with aiohttp.ClientSession() as session:                
        payload = {
            "model": "gpt-4o",
            "messages": prompt,
            "temperature": 0,
            "max_tokens": 4096,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

        async with session.post('https://api.openai.com/v1/chat/completions',
                                headers=headers, data=json.dumps(payload)) as response:
            if response.status == 200:
                resp_json = await response.json()
                return resp_json['choices'][0]['message']['content']
            else:
                return f"Error: {response.status}"


async def retorna_valor_final(results):
    print(f"##### Making Final Analysis....{datetime.datetime.now()}")
    prompt = [] 
    texto_concatenado = ''
    
    prompt.append({'role': 'system',  'content' : prompt_final})
    
    for i in results:
        texto_concatenado = texto_concatenado + " \n "+i
    
    prompt.append({'role': 'user', 'content':f"lista de análises: {texto_concatenado}"})
    
    resultado_final = await make_api_call_to_gpt(prompt)
    
    print(f"##### Resultado final...{datetime.datetime.now()}: {resultado_final}")
    
    return resultado_final    

'''
async def process_comments(df, context):
    
    print(f"##### Async Process Init...{datetime.datetime.now()}")
    
    blocos_de_textos = dividir_dataframe_em_blocos(df)
    concatenados = concatena_textos_blocos(blocos_de_textos)

    prompts = []
    dicionario_de_prompts = []
    for i in concatenados:
        prompts = []
        prompts.append({'role': 'system',  'content' : description})    
        prompts.append({'role': 'system',  'content' : f"O contexto da análise é:{context}"})    
        prompts.append({'role': 'user',  'content' : f"comentários: {i}"})
        dicionario_de_prompts.append(prompts)
    
    print("*************DICIONARIO")
    print(dicionario_de_prompts[0])
    results = []
    tasks = [make_api_call_to_gpt(prompt) for prompt in dicionario_de_prompts]
    #results = await asyncio.gather(*tasks)
    
    print("Gerando resultado final...")
    resultado_final = await retorna_valor_final(results)
    
    return resultado_final
'''
async def process_comments(df, context):
    print(f"##### Async Process Init...{datetime.datetime.now()}")
    
    blocos_de_textos = dividir_texto_em_blocos(df)
    concatenados = concatena_textos_blocos(blocos_de_textos)

    dicionario_de_prompts = []
    for i in concatenados:
        blocos = dividir_texto_em_blocos(i)  # Dividir cada texto grande em blocos menores
        for bloco in blocos:
            prompt = []
            prompt.append({'role': 'system',  'content' : description})    
            prompt.append({'role': 'system',  'content' : f"O contexto da análise é:{context}"})    
            prompt.append({'role': 'user',  'content' : f"comentários: {bloco}"})
            dicionario_de_prompts.append(prompt)
    
    print("*************DICIONARIO")
    print(dicionario_de_prompts[0])
    results = []
    tasks = [make_api_call_to_gpt(prompt) for prompt in dicionario_de_prompts]
    results = await asyncio.gather(*tasks)
    
    print("Gerando resultado final...")
    resultado_final = await retorna_valor_final(results)
    
    return resultado_final

if __name__ == "__main__":
    asyncio.run(process_comments())
