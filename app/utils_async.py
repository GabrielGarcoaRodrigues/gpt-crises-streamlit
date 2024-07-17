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

def dividir_texto_em_blocos(texto, tamanho_bloco=4096):
    palavras = texto.split()
    blocos = []
    bloco_atual = []
    tamanho_atual = 0

    for palavra in palavras:
        tamanho_palavra = len(palavra) + 1  # Adiciona 1 para o espaço
        if tamanho_atual + tamanho_palavra > tamanho_bloco:
            blocos.append(' '.join(bloco_atual))
            bloco_atual = []
            tamanho_atual = 0
        bloco_atual.append(palavra)
        tamanho_atual += tamanho_palavra

    if bloco_atual:
        blocos.append(' '.join(bloco_atual))

    return blocos

async def make_api_call_to_gpt(prompt):
    print(f"##### Calling API...: {datetime.datetime.now()}")
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
    texto_concatenado = '\n'.join(results)
    
    prompt.append({'role': 'system',  'content' : prompt_final})
    prompt.append({'role': 'user', 'content':f"lista de análises: {texto_concatenado}"})
    
    resultado_final = await make_api_call_to_gpt(prompt)
    
    print(f"##### Resultado final...{datetime.datetime.now()}: {resultado_final}")
    
    return resultado_final    

async def process_comments(df, context):
    print(f"##### Async Process Init...{datetime.datetime.now()}")

    if 'Texto' not in df.columns:
        raise ValueError("A coluna 'Texto' não está presente no DataFrame.")

    textos_concatenados = '\n'.join(df['Texto'].tolist())
    blocos_de_texto = dividir_texto_em_blocos(textos_concatenados)

    results = []
    for bloco in blocos_de_texto:
        prompt = [
            {'role': 'system', 'content': description},
            {'role': 'system', 'content': f"O contexto da análise é: {context}"},
            {'role': 'user', 'content': f"comentários: {bloco}"}
        ]
        resultado_intermediario = await make_api_call_to_gpt(prompt)
        results.append(resultado_intermediario)

    resultado_final = await retorna_valor_final(results)
    
    return resultado_final

def main(file_path, context):
    df = pd.read_excel(file_path)
    return asyncio.run(process_comments(df, context))
