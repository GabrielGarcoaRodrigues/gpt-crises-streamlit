import re
from pathlib import Path
import pickle
import streamlit as st

from unidecode import unidecode

PASTA_CONFIGERACOES = Path(__file__).parent / 'configuracoes'
PASTA_CONFIGERACOES.mkdir(exist_ok=True)

def salva_chave(chave):
    with open(PASTA_CONFIGERACOES / 'chave', 'wb') as f:
        pickle.dump(chave, f)

def le_chave():
    chave = st.secrets["API_KEY"]
    return chave
    # if (PASTA_CONFIGERACOES / 'chave').exists():
    #     with open(PASTA_CONFIGERACOES / 'chave', 'rb') as f:
    #         return pickle.load(f)
    # return chave
    # else:
    #     return ''
