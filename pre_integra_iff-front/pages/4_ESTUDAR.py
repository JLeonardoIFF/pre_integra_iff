import streamlit as st
import pandas as pd
from auth import require_login
import pymupdf
from pathlib import Path

require_login()

base_dir = Path(__file__).resolve().parent
project_root = base_dir.parent

image_path = project_root / "images" / "simbolo.png"
image1_path = project_root / "images" / "simbolo(1).png"

st.logo(image_path, size="large")

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
df_matriz =  st.session_state.get("df_matriz")

# Obter descritor e matéria escolhida do session_state
descritor = st.session_state.get("escolha_d")
materia_escolha = st.session_state.get("materia_escolha")
habilidade = st.session_state.get("habilidade")

print(materia_escolha)

# Função para obter descritor (simplificada)
def get_descritor(descritor, descritores):
    # Verifica se o descritor existe na lista de descritores
    if descritor in descritores.values:
        print(descritor)
        return descritor
    return None

# Obter descritores para a matéria escolhida
descritores = df_matriz.loc[df_matriz["Materia"] == materia_escolha, "Descritor"]

# Obter o descritor relacionado
descritor_relacionado = get_descritor(descritor, descritores)

# Lógica para exibir conteúdo
if descritor_relacionado is None:
    # Caso nenhum descritor tenha sido selecionado
    lista_materias = df_matriz["Materia"].dropna().unique().tolist()
    lista_materias.sort()
    materia_escolha = st.sidebar.selectbox("ESCOLHA - UMA MATERIA", lista_materias)

    # Atualizar session_state com a matéria escolhida
    st.session_state["materia_escolha"] = materia_escolha

    # Obter conteúdos para a matéria escolhida
    conteudos = df_matriz.loc[df_matriz["Materia"] == materia_escolha, "Equivalência EF"].dropna().unique().tolist()
    conteudo_escolha = st.sidebar.selectbox("ESCOLHA - UM CONTEÚDO", conteudos)

    habilidade_d = df_matriz.loc[df_matriz["Descritor"] == descritor, "Habilidade Original"] if not df_matriz.loc[df_matriz["Descritor"] == descritor_relacionado, "Habilidade Original"].empty else "Habilidade não encontrada"
    tema = df_matriz.loc[df_matriz["Descritor"] == descritor, "Tema"] if not df_matriz.loc[df_matriz["Descritor"] == descritor_relacionado, "Tema"].empty else "Tema não encontrado"

    # Exibir imagem e conteúdo escolhido
    st.image(image1_path, width=200)
    st.markdown(f""" <h3 style="margin-bottom: 0px;"> estudar sobre: </h3>""", unsafe_allow_html=True)
    st.markdown(f""" <h1 style="color: #93C56D; margin-bottom: 0px;"> {conteudo_escolha} </h1>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(f""" <p style="margin-bottom: 0px;"> Habilidade da matriz relacionada: <br> {habilidade} </p>""", unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown(f""" <h3 style="color: #93C56D; margin-bottom: 0px;"> Ferramentas de Estudo </h3>""", unsafe_allow_html=True)
            notebook_url = "https://notebooklm.google.com/"  # abre no navegador / app se disponível
            if st.button("Abrir NotebookLM"):
                st.markdown(f"[Abrir NotebookLM]({notebook_url})")
else:
    # Caso o descritor tenha sido selecionado via checklist
    lista_materias = df_matriz["Materia"].dropna().unique().tolist()
    lista_materias.sort()

    conteudo = st.session_state.get("conteudo")
    #conteudo = df_matriz.loc[df_matriz["Descritor"] == descritor_relacionado, "Equivalência EF"].dropna().unique().tolist()
    habilidade_d = df_matriz.loc[df_matriz["Descritor"] == descritor_relacionado, "Habilidade Original"] if not df_matriz.loc[df_matriz["Descritor"] == descritor_relacionado, "Habilidade Original"].empty else "Habilidade não encontrada"
    tema = df_matriz.loc[df_matriz["Descritor"] == descritor_relacionado, "Tema"] if not df_matriz.loc[df_matriz["Descritor"] == descritor_relacionado, "Tema"].empty else "Tema não encontrado"

    # Exibir imagem e conteúdo relacionado ao descritor
    st.image(image1_path, width=200)
    st.markdown(f""" <h3 style="margin-bottom: 0px;"> estudar sobre: </h3>""", unsafe_allow_html=True)
    st.markdown(f""" <h1 style="color: #93C56D; margin-bottom: 0px;"> {conteudo} </h1>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(f""" <p style="margin-bottom: 0px;"> Habilidade da matriz relacionada: <br> {habilidade} </p>""", unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown(f""" <h3 style="color: #93C56D; margin-bottom: 0px;"> Ferramentas de Estudo </h3>""", unsafe_allow_html=True)
            notebook_url = "https://notebooklm.google.com/"  # abre no navegador / app se disponível
            st.markdown(
                f"""
                <p> para estudo com fontes com auxilio de IA: </p>
                <a href="{notebook_url}">
                    <button style="background-color: #93C56D; color: white; padding: 8px; border: none; border-radius: 8px;">
                        Abrir NotebookLM
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )
            notion_url = "https://www.notion.so/"
            st.markdown(
                f"""
                <p> Notion uma opção para organização de estudos
                <a href="{notion_url}">
                    <button style="background-color: #93C56D; color: white; padding: 8px; border: none; border-radius: 8px;">
                        Abrir Notion
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )
