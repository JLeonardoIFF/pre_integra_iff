import streamlit as st
import pandas as pd
from auth import require_login
from pathlib import Path

st.set_page_config(page_title="Pré Integra IFF", layout="wide")

require_login()

@st.cache_data
def get_data():
    # sempre retorna o dataframe (antes retornava só dentro do if)
    base_dir = Path(__file__).resolve().parent
    project_root = base_dir.parent
    csv_path = project_root / "data" / "matrizreferencia.csv"
    return pd.read_csv(csv_path)

df_matriz = get_data()
st.session_state["df_matriz"] = df_matriz

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
        color: #0F3552 !important;
        font-size: 18px;
        font-weight: bold;
        text-decoration: #0F3552;
    }

    /* Texto ao passar o mouse */
    [data-testid="stSidebarNav"] li a:hover {
        color: #34D399 !important;  
    }
    </style>
""", unsafe_allow_html=True)

#opçoes do sidebar
lista_escolha = ["Padrão", "Edital", "Banco_Provas", "Matriz"]
materia_escolha = st.sidebar.selectbox("ESCOLHA - INFORMAÇÕES GERAIS", lista_escolha)

base_dir = Path(__file__).resolve().parent
project_root = base_dir.parent

image_path = project_root / "images" / "simbolo.png"
image1_path = project_root / "images" / "simbolo(1).png"
if materia_escolha == "Padrão":

    #st.sidebar.image("images/simbolo.png", width=650)
    st.logo(str(image_path), size="large")
    #st.logo("images/abajo.png", size="large")
    st.image(str(image2_path), width=200)
    st.write(""" # Pre IFF - Integra """)
    st.markdown(""" <h3 style="color: #93C56D; margin-bottom: 0px;"> Site de preparação pre-IFF </h3>""", unsafe_allow_html=True)
    st.markdown("""<h5 style="margin-bottom: 0px;"> <u> (exclusivo para Eloá, Lorena e Laura) </u> </h5>""", unsafe_allow_html=True)

    st.divider()

    col1, col2, col3 = st.columns([0.3, 0.4, 0.3], vertical_alignment="top")

    with col2:
        with st.container(width=400):
            st.markdown(
                """
                <div style="
                    text-align: center;
                    width: 100%;
                    padding: 10px;
                    font-size: 60px">

                    AQUI VOCE ENCONTRA... 
                </div>
                """,
                unsafe_allow_html=True
            )  

    col11, col22, col33 = st.columns(3, vertical_alignment="top")

    with col11:
        with st.container(border=True, width=300):
            editalimg = project_root / "images" / "editalimg.png"
            st.image(str(editalimg), width=200)

            st.divider()

            st.markdown("""<p> este é o documento com todas informaçoes referentes a: <br> Processo seletivo, Vagas, Inscrições, <br> Isenção,
                            Cotas, Condições, Provas, Classificação, Resultados<br>
                            Recursos, Matrículas, Eliminação, Disposições finais,
                            Anexos<br> """, unsafe_allow_html=True)
    with col22:
        with st.container(border=True, width=300):
            image3_path = project_root / "images" / "matrizimg.png"
            st.image(str(image3_path), width=200)

            st.divider()

            st.markdown("""<p> este é o documento com todas informaçoes referentes a: <br> """, unsafe_allow_html=True)
    with col33:
        with st.container(border=True, width=300):
            image4_path = project_root / "images" / "bancoprovas.png"
            st.image(str(image4_path), width=200)
            
            st.divider()

            st.markdown("""<p> este é o banco que armazena <br> as seguintes provas do IFF anteriores <br> 2025.1, 2024.1, 2023.1, """, unsafe_allow_html=True)
elif materia_escolha == "Edital":
    st.image(image1_path, width=300)

    st.write(""" # Edital IFF """)
    st.markdown("### Aqui esta o conteudo em PDF do edital do IFF 2026", unsafe_allow_html=True)

    coluna1, coluna2 = st.columns(2, vertical_alignment="top", gap="medium")

    with coluna1:
        base_dir = Path(__file__).resolve().parent
        project_root = base_dir.parent
        caminho_pdf = project_root / "data" / "edital20261.pdf"
        st.pdf(caminho_pdf, height=400)

    with coluna2:
        base_dir = Path(__file__).resolve().parent
        project_root = base_dir.parent
        caminho_pdf = project_root / "data" / "edital20261.pdf"

        # Abre o PDF em modo binário
        with open(caminho_pdf, "rb") as f:
            pdf_bytes = f.read()

        # Botão para download
        st.download_button(
            label="📥 Baixar Edital em PDF",
            data=pdf_bytes,
            file_name="edital20261.pdf",     
            mime="application/pdf"      
        )


elif materia_escolha == "Matriz":
    st.image(image1_path, width=300)

    st.write(""" # Matriz IFF """)
    st.markdown("""<h3 style ="color: #93C56D;"> Aqui esta o dataFrame da Matriz do IFF 2026 </h2>""", unsafe_allow_html=True)
    st.write("")

    df_matriz
