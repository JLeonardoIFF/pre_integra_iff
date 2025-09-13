import streamlit as st
import pandas as pd

st.logo("images/simbolo.png", size="large")

st.markdown("""
    <style>
    /* Container do menu de páginas no sidebar */
    [data-testid="stSidebarNav"] {
        background-color: #0F3552;  /* cor de fundo */
        padding: 10px;
        border-radius: 12px;
    }

    /* Texto dos links de página */
    [data-testid="stSidebarNav"] li a {
        color: #0F3552 !important;    /* amarelo */
        font-size: 18px;
        font-weight: bold;
        text-decoration: #0F3552;
    }

    /* Texto ao passar o mouse */
    [data-testid="stSidebarNav"] li a:hover {
        color: #34D399 !important;   /* verde */
    }
    </style>
""", unsafe_allow_html=True)

#pegar o descritor do session state
descritor = st.session_state.get("escolha_d")

@st.cache_data
def get_data():
    # sempre retorna o dataframe (antes retornava só dentro do if)
    return pd.read_csv("data/matriz_referencia.csv")

df_matriz =  st.session_state.get("df_matriz")

conteudo = df_matriz.loc[df_matriz["Descritor"] == descritor, "Equivalência EF"]
habilidade_d = df_matriz.loc[df_matriz["Descritor"] == descritor, "Habilidade Original"]
tema = df_matriz.loc[df_matriz["Descritor"] == descritor, "Tema"]

#logica para tratar se o descritor foi selecionado atraves do checklist ou nao
if descritor is None:
    lista_materias = df_matriz["Materia"].dropna().unique().tolist()
    lista_materias.sort()
    materia_escolha = st.sidebar.selectbox("ESCOLHA - UMA MATERIA", lista_materias)

    st.session_state["escolha_d"] = descritor
    conteudos = df_matriz.loc[df_matriz["Materia"] == materia_escolha, "Equivalência EF"].dropna().unique().tolist()
    descritor_escolha = st.sidebar.selectbox("ESCOLHA - UM CONTEUDO", conteudos)

st.write(f"{descritor}")


