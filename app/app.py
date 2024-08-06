import streamlit as st
import pandas as pd
import asyncio
from utils_async import *
from datetime import datetime
from utils_files import *
import time
import emoji
import re


# Funções Assíncronas
def get_event_loop():
    """Garante que um event loop esteja disponível, criando um se necessário."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError as e:
        if "There is no current event loop in thread" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        raise

async def async_process_comments(df, context):
    """Processa comentários de forma assíncrona."""
    return await process_comments(df, context)

async def run_async_process(df, context, progress_bar):
    loop = get_event_loop()
    task = loop.create_task(process_comments(df, context))
    
    progress = 0
    while not task.done():
        await asyncio.sleep(11)  # Aguarda 5 segundos entre cada atualização
        progress += 10
        progress_bar.progress(min(progress, 100))
    
    return await task


# Função Principal
def main():
    st.set_page_config(page_title="Orbit AI", layout='centered')
    print(f"##### Executando Main...{datetime.now()}")

    inicializacao() 

    st.header('Ambev Crises 📈')
    if st.button('Melhores Práticas'):
        st.session_state.show_info = not st.session_state.get('show_info', False)
    if st.session_state.get('show_info', False):
            with st.expander("Como utilizar o chat"):
                st.write("""
                    1. Faça o upload de um arquivo Excel com os comentários sobre a crise (O arquivo deve conter uma coluna chamada 'Texto').
                    2. Descreva o contexto da análise no campo de texto (Marca e Causa).
                    3. Clique no botão ou pressione `Enter` para processar a análise.
                    4. Aguarde enquanto o processamento é realizado. O resultado será exibido na tela.
                """)
            with st.expander("Como escrever o contexto"):
                st.write("""
                    O contexto é uma descrição curta da crise ou evento que gerou os comentários, e deve conter a marca e causa da crise. 
                    Por exemplo, se os comentários são sobre uma mudança de ingredientes na cerveja Heineken, 
                    o contexto poderia ser: "A mudança nos ingredientes da cerveja Heineken".
                """)
            with st.expander("Comentários removidos"):
                st.write("""
                    O modelo remove os comentários que são linhas vazias e menções a outros usuários, para garantir uma análise precisa sobre o tema.
                """)
            st.info("O modelo analisa no máximo 1000 comentários por vez.")
     
    uploaded_file = st.file_uploader("Faça o upload do arquivo Excel com os comentários sobre a crise", type="xlsx", help="O arquivo deve conter uma coluna chamada 'Texto'.", accept_multiple_files=False)
    df_texto = handle_uploaded_file(uploaded_file)
    
    prompt = st.chat_input(placeholder='Descreva o contexto da análise...', max_chars=250, key='input')    

    if prompt:
        if df_texto is None:
            st.error("Faça o upload do arquivo Excel!")
        else:
            st.session_state.processing = True
            api_key = st.session_state['api_key']
            st.write("Processando...")
            # Mostrar barra de progresso
            progress_bar = st.progress(0)
            
            # Executa o processamento assíncrono e atualiza a barra de progresso
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(run_async_process(df_texto, prompt, progress_bar))
            
            st.session_state.processing = False
            display_results(results)
            st.button('Baixar resultados')

def clean_text(text):
    """Remove emojis e menções de usuários do texto."""
    text = re.sub(r'@\w+', '', text)  # Remove menções de usuários
    text = text.strip()  # Remove espaços em branco extras
    return text


def handle_uploaded_file(uploaded_file, limit=5000):
    """Processa o arquivo carregado e retorna um DataFrame se encontrado. limit é o tamanho maximo de textos"""
    try:
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            tamanho = len(df)
            df = df[df['Texto'].apply(lambda x: isinstance(x, str))]  # Filtra apenas strings
            df['Texto'] = df['Texto'].apply(clean_text)  # Limpa o texto
            df = df.dropna(subset=['Texto'])  # Remove linhas em branco
            df = df[df['Texto'] != '']  # Remove linhas que ficaram vazias após a limpeza
            df = df.head(limit)
            df.reset_index(drop=True, inplace=True)  # Redefine o índice do DataFrame
            if 'Texto' in df.columns:
                st.dataframe(df['Texto'])  # Mostra o dataframe
                tamanho_limpo = len(df)
                st.info(f"{tamanho - tamanho_limpo} comentários foram removidos.")
                return df
            else:
                st.error("A coluna 'Texto' não foi encontrada no arquivo.")
    except Exception as e:
        st.error("Erro: A coluna 'Texto' não foi encontrada no arquivo.")
    return None

def display_results(results):
    """Exibe os resultados processados."""
    if results:
        results_str = ''.join(results)
        st.write(results_str)   


def inicializacao():
    """Inicializa a sessão do Streamlit, se necessário."""
    if 'modelo' not in st.session_state:
        st.session_state.modelo = 'gpt-4o'
    if 'api_key' not in st.session_state:
        st.session_state.api_key = le_chave()
    if 'show_info' not in st.session_state:
        st.session_state.show_info = False
    
    print("##### Sessão inicializada.")

if __name__ == '__main__':
    main()