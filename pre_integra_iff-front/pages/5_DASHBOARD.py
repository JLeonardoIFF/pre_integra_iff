import streamlit as st
import pandas as pd
from auth import require_login
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

#carrega dataframes usados
df_gabarito = pd.read_csv("data/gabaritos_1817232422.csv")
df_matriz =  st.session_state.get("df_matriz")

#conta a quantidade de repeticoes do Dn por coluna

#st.logo("images/abajo.png", size="large")
st.image(image1_path, width=200)
st.write(""" ## Dados - Integra  """)
st.markdown("""<h4 style="color: #93C56D">  aqui voce acompanha graficos e estatisticas uteis para mapear <br> a prova do iff rumo sua aprovação </h4>""", unsafe_allow_html=True)

#sidebar com opçoes
lista_materias = df_gabarito["subject"].dropna().unique().tolist()
lista_materias.sort()
materia_escolha = st.sidebar.selectbox("ESCOLHA UMA MATERIA PARA ANALISAR", lista_materias)

df_relacionado = df_gabarito[df_gabarito["subject"] == materia_escolha]

#tratamento do dado
df = df_relacionado.copy()
df["descritores"] = df["descritores"].fillna("").astype(str)

# 2. separar por ponto-e-vírgula (remover espaços ao redor)
df["descritores_list"] = df["descritores"].str.split(r"\s*;\s*")

# 3. explodir: cada descritor vira uma linha
df_expl = df.explode("descritores_list")

# 4. limpar espaços e remover strings vazias
df_expl["descritores_list"] = df_expl["descritores_list"].str.strip()
df_expl = df_expl[df_expl["descritores_list"] != ""]

# 5. agrupar e contar por subject + descritor
df_counts = (
    df_expl
    .groupby(["subject", "descritores_list"])
    .size()
    .reset_index(name="Count")
    .rename(columns={"descritores_list": "descritor"})
)

import altair as alt

top_n = 30
plot_df = df_counts.sort_values("Count", ascending=False).head(top_n)

chart = (
    alt.Chart(plot_df)
    .mark_bar()
    .encode(
        x=alt.X("descritor:N", sort='-y', title="Descritor"),
        y=alt.Y("Count:Q", title="Ocorrências"),
        tooltip=["descritor", "Count"]
    )
    .properties(width=800, height=400)
)

st.subheader("Grafico de Relevancia X Conteudo")
st.altair_chart(chart, use_container_width=True)

print(materia_escolha)



