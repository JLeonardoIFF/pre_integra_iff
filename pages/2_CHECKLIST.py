import streamlit as st
import pandas as pd
import random
import re

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

df_matriz =  st.session_state.get("df_matriz")

# --- Helpers ---
def sanitize_key(s: str) -> str:
    """Converte string para uma chave segura: só letras, números e underscores."""
    return re.sub(r'\W+', '_', str(s)).strip('_')

def tema_key(materia: str, tema: str) -> str:
    return sanitize_key(f"{materia}__{tema}")

# inicializa estado persistente
st.session_state.setdefault("progresso_geral", 0)
st.session_state.setdefault("tema_progress_map", {})  # mapa tema -> percent
st.session_state.setdefault("seed_temas_shuffle", 0)  # opcional para determinismo

# Sidebar seleção
if df_matriz.empty:
    st.error("O arquivo data/matriz_referencia.csv está vazio ou não encontrado.")
    st.stop()

lista_materias = df_matriz["Materia"].dropna().unique().tolist()
lista_materias.sort()
materia_escolha = st.sidebar.selectbox("Matéria", lista_materias)

# Filtra apenas a matéria escolhida
checklist_materia = df_matriz[df_matriz["Materia"] == materia_escolha]

# Título e progresso topo
st.title("Checklist - IntegraPréIFF")
st.markdown(f"### Aqui você acompanha sua evolução nos conteúdos da matéria: <br> <center>**{materia_escolha}**</center>", unsafe_allow_html=True)
st.divider()

top_progress_placeholder = st.empty()
top_progress_placeholder.progress(st.session_state.progresso_geral, text=f"{st.session_state.progresso_geral}% concluído")

# Lista estável de temas (ordem determinística)
temas_quantidade = checklist_materia["Tema"].dropna().unique().tolist()
temas_quantidade.sort()

# reset mapa local temporário para recalcular
tema_progress_map_local = {}

for tema in temas_quantidade:
    tk = tema_key(materia_escolha, tema)

    # pega descritores e conteudos do tema (listas usando ordenação determinística)
    descritores = checklist_materia.loc[checklist_materia["Tema"] == tema, "Descritor"].dropna().unique().tolist()
    conteudos = checklist_materia.loc[checklist_materia["Tema"] == tema, "Equivalência EF"].dropna().unique().tolist()
    # garante ordenação estável
    # (se preferir outra ordem, aplique sorting customizado)
    # descritores.sort()

    count_descritor = len(descritores)
    if count_descritor == 0:
        continue

    # expander por tema
    with st.expander(f"{tema}", expanded=False):
        # Placeholder para barra do tema
        tema_top_placeholder = st.empty()
        # para cada descritor do tema
        for d_idx, descr in enumerate(descritores):
            # container para cada descritor (mantém estrutura)
            with st.container():
                col1, col2, col3 = st.columns([2, 4, 2], vertical_alignment="top")

                # ---------- Coluna 1: descritor + botão Estudar ----------
                with col1:
                    st.markdown("**Descritor**")
                    st.write(descr)

                    # botão Estudar com chave única
                    btn_key = f"btn_estudar__{tk}__{d_idx}"
                    if st.button("Estudar", key=btn_key):
                        try:
                            if "escolha_d" not in st.session_state:
                                 st.session_state["escolha_d"] = descr
                            st.switch_page("3_estudar")
                        except Exception:
                            try:
                                st.switch_page("pages/3_ESTUDAR.py")
                            except Exception as e:
                                st.error(f"Não foi possível mudar de página: {e}")

                # ---------- Coluna 2: Conteúdos + Checkboxes ----------
                with col2:
                    st.markdown("**Conteúdo**")
                    if d_idx < len(conteudos):
                        st.markdown(f"<b>{conteudos[d_idx]}</b>", unsafe_allow_html=True)
                    else:
                        st.write("-")

                    # chaves determinísticas por check
                    k1 = f"check_teoria__{tk}__{d_idx}"
                    k2 = f"check_resumo__{tk}__{d_idx}"
                    k3 = f"check_questao__{tk}__{d_idx}"
                    k4 = f"check_revisao__{tk}__{d_idx}"

                    # garante que chave existe em session_state
                    for k in (k1, k2, k3, k4):
                        st.session_state.setdefault(k, False)

                    # mostra checkboxes (estado persistido via key)
                    st.checkbox("Teoria", key=k1)
                    st.checkbox("Resumo", key=k2)
                    st.checkbox("Questões", key=k3)
                    st.checkbox("Revisões", key=k4)

                # ---------- Coluna 3: Status + nível ----------
                with col3:
                    # nível (persistido por descritor)
                    nivel_key = f"nivel__{tk}__{d_idx}"
                    st.session_state.setdefault(nivel_key, "N/A")
                    nivel_escolhido = st.selectbox(
                        "Nível de Domínio",
                        ("N/A", "Ruim", "Médio", "Bom", "Dominado"),
                        key=nivel_key
                    )

                    # calcula progresso do descritor a partir dos checks e do nível
                    checked = sum(1 for k in (k1, k2, k3, k4) if st.session_state.get(k, False))
                    base_percent = int((checked / 4) * 80)  # 80% vem dos checks
                    nivel_bonus_map = {"N/A": 0, "Ruim": 5, "Médio": 10, "Bom": 15, "Dominado": 20}
                    bonus = nivel_bonus_map.get(nivel_escolhido, 0)
                    descritor_progress = min(100, base_percent + bonus)

                    # salva progresso do descritor no session_state (persistência)
                    st.session_state[f"progresso__{tk}__{d_idx}"] = descritor_progress

                    st.markdown("**Progresso (descritor)**")
                    st.progress(descritor_progress, text=f"{descritor_progress}% concluído")

        # depois de iterar todos os descritores do tema, calcula média do tema
        descritor_progs = [
            st.session_state.get(f"progresso__{tk}__{i}", 0) for i in range(count_descritor)
        ]
        tema_percent = int(sum(descritor_progs) / len(descritor_progs)) if descritor_progs else 0
        # armazena mapa local e no session_state
        tema_progress_map_local[tema] = tema_percent
        st.session_state["tema_progress_map"][tk] = tema_percent

        # atualiza barra do topo do expander
        tema_top_placeholder.progress(tema_percent, text=f"{tema_percent}% do tema concluído")

# --- calcular e atualizar progresso geral (média dos temas apresentados) ---
if tema_progress_map_local:
    geral = int(sum(tema_progress_map_local.values()) / len(tema_progress_map_local))
else:
    geral = 0

st.session_state.progresso_geral = geral
top_progress_placeholder.progress(geral, text=f"{geral}% concluído")


				
