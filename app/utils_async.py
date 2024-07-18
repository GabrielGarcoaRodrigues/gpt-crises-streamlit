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
Seu trabalho é ler TODOS os comentários e fornecer os outputs que serão enviados a seguir.
"""

prompt_final = '''
Analise TODOS os comentários do contexto e faça as seguintes tarefas:
1. Classifique os sentimentos de todos os comentários, mostrando no resultado final o percentual e número absoluto de cada sentimento em relação ao total;
2. Leia os comentários, e a partir da leitura de todos eles, crie 5 categorias em formato de uma frase curta para cada categoria, mostrando também a quantidade de comentários relacionados a cada categoria  além de uma pequena lista com algumas palavras chave relacionadas a categoria. Além disso Para cada categoria criada, gere um comentário curto que esteja no mesmo modelo dos comentários analisados e que sintetize a maior parte dos comentários relacionados a categoria. Gere uma breve descrição de cada categoria baseado nos comentários; 
3. Faça um breve resumos dos comentários que não estão relacionados a nenhuma das categorias.
4. Faça uma breve análise dos comentários positivos, neutros e negativos;
5. Faça uma análise única juntando quantitaiva e qualitativa dos comentários.
'''

def dividir_dataframe_em_blocos(df, tamanho_bloco=300):   
    if 'Texto' not in df.columns:
       raise ValueError("A coluna 'Texto' não está presente no DataFrame.")
    st.write(len(df))
    num_blocos = (len(df) + tamanho_bloco - 1) // tamanho_bloco
    lista_de_textos_bloco = [df['Texto'][i*tamanho_bloco:(i+1)*tamanho_bloco].tolist() for i in range(num_blocos)]
    
    return lista_de_textos_bloco
    
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
    results = await asyncio.gather(*tasks)
    
    print("Gerando resultado final...")
    resultado_final = await retorna_valor_final(results)
    
    return resultado_final



if __name__ == "__main__":
    asyncio.run(process_comments())
