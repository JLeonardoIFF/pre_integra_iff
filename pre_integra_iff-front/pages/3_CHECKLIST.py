# --------------------------------------------------
# Arquivo: checklist.py  (versão atualizada)
# --------------------------------------------------
import streamlit as st
import pandas as pd
import re
from auth import require_login
from supabase_db import upsert_user_progress_cache, load_progress_all, upsert_progress_item, sanitize_key
from pathlib import Path

require_login()

st.logo("images/simbolo.png", size="large")

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        background-color: #0F3552;
        padding: 10px;
        border-radius: 12px;
    }

    [data-testid="stSidebarNav"] li a {
        color: #0F3552 !important;
        font-size: 18px;
        font-weight: bold;
        text-decoration: #0F3552;
    }

    [data-testid="stSidebarNav"] li a:hover {
        color: #34D399 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# Aplica pending_updates (se houver) ANTES de criar widgets
# -------------------------
if "pending_updates" in st.session_state and isinstance(st.session_state.get("pending_updates"), dict):
    pending = st.session_state.pop("pending_updates", {})
    for k, v in pending.items():
        try:
            st.session_state[k] = v
        except Exception:
            st.warning(f"Não foi possível aplicar pending update para {k}")

# Carregar df_matriz (se não estiver em session_state)
if "df_matriz" not in st.session_state:
    @st.cache_data
    def get_data():
        return pd.read_csv("data/matriz_referencia.csv")
    
    st.session_state["df_matriz"] = get_data()

df_matriz = st.session_state.get("df_matriz")

# Se usuário está logado mas progresso ainda não foi carregado, carregar aqui
if "progress_loaded" not in st.session_state and st.session_state.get("user_id"):
    try:
        geral, tema_map, items = load_progress_all(st.session_state["user_id"])
        # aplica diretamente no session_state para garantir que widgets reflitam o estado
        for it in items:
            tk = it.get("tema_key")
            d_idx = int(it.get("descr_idx", 0))
            st.session_state[f"progresso__{tk}__{d_idx}"] = int(it.get("progress", 0))
            st.session_state[f"check_teoria__{tk}__{d_idx}"] = bool(it.get("check_teoria", False))
            st.session_state[f"check_resumo__{tk}__{d_idx}"] = bool(it.get("check_resumo", False))
            st.session_state[f"check_questao__{tk}__{d_idx}"] = bool(it.get("check_questao", False))
            st.session_state[f"check_revisao__{tk}__{d_idx}"] = bool(it.get("check_revisao", False))
            st.session_state[f"nivel__{tk}__{d_idx}"] = it.get("nivel", "N/A") or "N/A"
        st.session_state["tema_progress_map"] = dict(tema_map or {})
        st.session_state["progresso_geral"] = int(geral or 0)
        st.session_state["progress_loaded"] = True
    except Exception as e:
        st.warning(f"Não foi possível carregar progresso inicial: {e}")

# --- Helpers ---

def tema_key(materia: str, tema: str) -> str:
    return sanitize_key(f"{materia}__{tema}")

# inicializa estado persistente
st.session_state.setdefault("progresso_geral", 0)
st.session_state.setdefault("tema_progress_map", {})

lista_materias = df_matriz["Materia"].dropna().unique().tolist()
lista_materias.sort()
materia_escolha = st.sidebar.selectbox("Matéria", lista_materias)

checklist_materia = df_matriz[df_matriz["Materia"] == materia_escolha]

st.title("Checklist - IntegraPréIFF")
st.markdown(f"### Aqui você acompanha sua evolução nos conteúdos da matéria: <br> <center>**{materia_escolha}**</center>", unsafe_allow_html=True)
st.divider()

top_progress_placeholder = st.empty()
top_progress_placeholder.progress(st.session_state["progresso_geral"], text=f"{st.session_state['progresso_geral']}% concluído")

temas_quantidade = checklist_materia["Tema"].dropna().unique().tolist()
temas_quantidade.sort()

tema_progress_map_local = {}


def compute_and_update_progress(materia, tk, count_descritor):
    descritor_progs = []
    for i in range(count_descritor):
        k1 = f"check_teoria__{tk}__{i}"
        k2 = f"check_resumo__{tk}__{i}"
        k3 = f"check_questao__{tk}__{i}"
        k4 = f"check_revisao__{tk}__{i}"
        nivel_key = f"nivel__{tk}__{i}"

        # garante chaves em session_state com valores já carregados (se houver)
        st.session_state.setdefault(k1, False)
        st.session_state.setdefault(k2, False)
        st.session_state.setdefault(k3, False)
        st.session_state.setdefault(k4, False)
        st.session_state.setdefault(nivel_key, "N/A")

        checked = sum(1 for k in (k1, k2, k3, k4) if st.session_state.get(k, False))
        base_percent = int((checked / 4) * 80)
        nivel_bonus_map = {"N/A": 0, "Ruim": 5, "Médio": 10, "Bom": 15, "Dominado": 20}
        nivel_escolhido = st.session_state.get(nivel_key, "N/A")
        bonus = nivel_bonus_map.get(nivel_escolhido, 0)
        descritor_progress = min(100, base_percent + bonus)
        st.session_state[f"progresso__{tk}__{i}"] = descritor_progress
        descritor_progs.append(descritor_progress)

    tema_percent = int(sum(descritor_progs) / len(descritor_progs)) if descritor_progs else 0
    st.session_state.setdefault("tema_progress_map", {})
    st.session_state["tema_progress_map"][tk] = tema_percent

    tema_map_local = st.session_state.get("tema_progress_map", {})
    geral = int(sum(tema_map_local.values()) / len(tema_map_local)) if tema_map_local else 0
    st.session_state["progresso_geral"] = geral

    return descritor_progs, tema_percent, geral

for tema in temas_quantidade:
    tk = tema_key(materia_escolha, tema)

    descritores = checklist_materia.loc[checklist_materia["Tema"] == tema, "Descritor"].dropna().unique().tolist()
    conteudos = checklist_materia.loc[checklist_materia["Tema"] == tema, "Equivalência EF"].dropna().unique().tolist()
    habilidades = checklist_materia.loc[checklist_materia["Tema"] == tema, "Habilidade Original"].dropna().unique().tolist()

    count_descritor = len(descritores)
    if count_descritor == 0:
        continue

    with st.expander(f"{tema}", expanded=False):
        tema_top_placeholder = st.empty()

        # recalc inicial a partir do session_state (que foi carregado no login ou no início)
        compute_and_update_progress(materia_escolha, tk, count_descritor)
        tema_top_placeholder.progress(st.session_state["tema_progress_map"].get(tk, 0), text=f"{st.session_state['tema_progress_map'].get(tk, 0)}% do tema concluído")

        for d_idx, descr in enumerate(descritores):
            with st.container():
                col1, col2, col3 = st.columns([2, 4, 2], vertical_alignment="top")

                def make_handler(materia, tk, d_idx, count_descritor, tema_top_placeholder, top_progress_placeholder):
                    def _handler():
                        compute_and_update_progress(materia, tk, count_descritor)
                        try:
                            tema_top_placeholder.progress(st.session_state["tema_progress_map"].get(tk, 0), text=f"{st.session_state['tema_progress_map'].get(tk, 0)}% do tema concluído")
                            top_progress_placeholder.progress(st.session_state["progresso_geral"], text=f"{st.session_state['progresso_geral']}% concluído")
                        except Exception:
                            pass
                    return _handler

                handler = make_handler(materia_escolha, tk, d_idx, count_descritor, tema_top_placeholder, top_progress_placeholder)

                # Coluna 1
                with col1:
                    st.markdown("**Descritor**")
                    st.write(descr)

                    btn_key = f"btn_estudar__{tk}__{d_idx}"
                    if st.button("Estudar", key=btn_key):
                        try:
                            st.session_state["escolha_d"] = descr
                            st.session_state["materia_escolha"] = materia_escolha
                            st.session_state["conteudo"] = conteudos[d_idx]
                            st.session_state["habilidade"] = habilidades[d_idx]
                            st.switch_page("pages/4_ESTUDAR.py")
                        except Exception:
                            try:
                                st.switch_page("pages/4_ESTUDAR.py")
                            except Exception as e:
                                st.error(f"Não foi possível mudar de página: {e}")

                # Coluna 2
                with col2:
                    st.markdown("**Conteúdo**")
                    if d_idx < len(conteudos):
                        st.markdown(f"<b>{conteudos[d_idx]}</b>", unsafe_allow_html=True)
                    else:
                        st.write("-")

                    key_teoria = f"check_teoria__{tk}__{d_idx}"
                    key_resumo = f"check_resumo__{tk}__{d_idx}"
                    key_questao = f"check_questao__{tk}__{d_idx}"
                    key_revisao = f"check_revisao__{tk}__{d_idx}"

                    k1 = st.session_state[f"check_teoria__{tk}__{d_idx}"]
                    k2 = st.session_state[f"check_resumo__{tk}__{d_idx}"]
                    k3 = st.session_state[f"check_questao__{tk}__{d_idx}"]
                    k4 = st.session_state[f"check_revisao__{tk}__{d_idx}"]

                    # checkboxes (já vinculados a session_state via key)
                    st.checkbox("Teoria", key=key_teoria, on_change=handler, value=k1)
                    st.checkbox("Resumo", key=key_resumo, on_change=handler, value=k2)
                    st.checkbox("Questões", key=key_questao, on_change=handler, value=k3)
                    st.checkbox("Revisões", key=key_revisao, on_change=handler, value=k4)

                # Coluna 3
                with col3:
                    nivel_key = f"nivel__{tk}__{d_idx}"
                    st.session_state.setdefault(nivel_key, "N/A")
                    nivel_escolhido = st.selectbox(
                        "Nível de Domínio",
                        ("N/A", "Ruim", "Médio", "Bom", "Dominado"),
                        key=nivel_key,
                        on_change=handler
                    )

                    compute_and_update_progress(materia_escolha, tk, count_descritor)
                    descritor_progress = st.session_state.get(f"progresso__{tk}__{d_idx}", 0)

                    st.markdown("**Progresso (descritor)**")
                    st.progress(descritor_progress, text=f"{descritor_progress}% concluído")

                    # ---------- Botão SALVAR (usa pending_updates + rerun) ----------
                    save_key = f"btn_salvar__{tk}__{d_idx}"
                    if st.button("Salvar", key=save_key):
                        checked_vals = {
                            "check_teoria": bool(st.session_state.get(f"check_teoria__{tk}__{d_idx}")),
                            "check_resumo": bool(st.session_state.get(f"check_resumo__{tk}__{d_idx}")),
                            "check_questao": bool(st.session_state.get(f"check_questao__{tk}__{d_idx}")),
                            "check_revisao": bool(st.session_state.get(f"check_revisao__{tk}__{d_idx}")),
                        }
                        nivel_atual = st.session_state.get(nivel_key, "N/A")

                        # prepara pending_updates que serão aplicados no PRÓXIMO rerun
                        updates = {
                            f"check_teoria__{tk}__{d_idx}": checked_vals["check_teoria"],
                            f"check_resumo__{tk}__{d_idx}": checked_vals["check_resumo"],
                            f"check_questao__{tk}__{d_idx}": checked_vals["check_questao"],
                            f"check_revisao__{tk}__{d_idx}": checked_vals["check_revisao"],
                            f"nivel__{tk}__{d_idx}": nivel_atual
                        }

                        base_checked = sum(1 for k in (f"check_teoria__{tk}__{d_idx}", f"check_resumo__{tk}__{d_idx}", f"check_questao__{tk}__{d_idx}", f"check_revisao__{tk}__{d_idx}") if updates.get(k, False))
                        base_percent = int((base_checked / 4) * 80)
                        nivel_bonus_map = {"N/A": 0, "Ruim": 5, "Médio": 10, "Bom": 15, "Dominado": 20}
                        bonus = nivel_bonus_map.get(nivel_atual, 0)
                        descritor_progress = min(100, base_percent + bonus)
                        updates[f"progresso__{tk}__{d_idx}"] = descritor_progress

                        st.session_state["pending_updates"] = updates

                        # Persiste no DB
                        user_id = st.session_state.get("user_id")
                        if not user_id:
                            st.error("Usuário não autenticado. Faça login antes de salvar.")
                        else:
                            try:
                                try:
                                    upsert_progress_item(user_id, materia_escolha, tk, d_idx, descr, descritor_progress, checks=checked_vals, nivel=nivel_atual)
                                except Exception as e_pi:
                                    st.warning(f"Falha ao gravar progress_item (continua salvando cache): {e_pi}")

                                descritor_progs_for_theme = []
                                for i in range(count_descritor):
                                    if i == d_idx:
                                        descritor_progs_for_theme.append(int(descritor_progress))
                                    else:
                                        descritor_progs_for_theme.append(int(st.session_state.get(f"progresso__{tk}__{i}", 0)))
                                tema_percent_to_save = int(sum(descritor_progs_for_theme) / len(descritor_progs_for_theme)) if descritor_progs_for_theme else 0

                                tema_map_to_save = dict(st.session_state.get("tema_progress_map", {}))
                                tema_map_to_save[tk] = tema_percent_to_save

                                geral_to_save = int(sum(tema_map_to_save.values()) / len(tema_map_to_save)) if tema_map_to_save else 0

                                composite_key = f"{tk}:::{d_idx}"
                                new_entry = {
                                    composite_key: {
                                        "check_teoria": checked_vals["check_teoria"],
                                        "check_resumo": checked_vals["check_resumo"],
                                        "check_questao": checked_vals["check_questao"],
                                        "check_revisao": checked_vals["check_revisao"],
                                        "nivel": nivel_atual,
                                        "progress": int(descritor_progress)
                                    }
                                }

                                upsert_user_progress_cache(user_id, geral_to_save, tema_map_to_save, checks_map=new_entry)

                            except Exception as e:
                                st.error(f"Erro ao salvar no banco: {e}")

                        st.session_state["progress_loaded"] = True
                        # força rerun para aplicar pending_updates antes de criar widgets
                        try:
                            st.rerun()
                        except Exception:
                            try:
                                st.rerun()
                            except Exception:
                                pass

        # depois de iterar descritores do tema
        descritor_progs = [
            st.session_state.get(f"progresso__{tk}__{i}", 0) for i in range(count_descritor)
        ]
        tema_percent = int(sum(descritor_progs) / len(descritor_progs)) if descritor_progs else 0
        tema_progress_map_local[tema] = tema_percent
        st.session_state["tema_progress_map"][tk] = tema_percent
        tema_top_placeholder.progress(tema_percent, text=f"{tema_percent}% do tema concluído")

# atualizar geral
if tema_progress_map_local:
    geral = int(sum(tema_progress_map_local.values()) / len(tema_progress_map_local))
else:
    geral = 0

st.session_state["progresso_geral"] = geral
top_progress_placeholder.progress(geral, text=f"{geral}% concluído")
