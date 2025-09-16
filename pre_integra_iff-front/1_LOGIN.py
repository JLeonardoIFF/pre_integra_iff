# --------------------------------------------------
# Arquivo: login.py  (versão atualizada)
# --------------------------------------------------
import streamlit as st
from supabase_db import get_db, load_progress_all

st.set_page_config(page_title="Pré Integra IFF", layout="wide")

supabase = get_db()


def after_login_load():
    # obtenha user_id de forma robusta
    user_id = st.session_state.get("user_id")
    if not user_id:
        user_obj = st.session_state.get("user")
        if isinstance(user_obj, dict):
            user_id = user_obj.get("id")
        elif isinstance(user_obj, int):
            user_id = user_obj
        else:
            user_id = getattr(user_obj, "id", None) or getattr(user_obj, "user_id", None)

    if not user_id:
        st.error("after_login_load: user_id não encontrado em session_state.")
        return

    # load_progress_all retorna (geral, tema_map, items)
    geral, tema_map, items = load_progress_all(user_id)

    # popula session_state para cada descritor salvo
    for it in items:
        if not isinstance(it, dict):
            st.warning(f"Item inesperado em load_progress_all: {it}")
            continue

        tk = it.get("tema_key")
        d_idx = int(it.get("descr_idx", 0))

        # sempre escrever explicitamente para garantir que os widgets criados
        # depois reflitam os valores do DB (não usar setdefault aqui)
        st.session_state[f"progresso__{tk}__{d_idx}"] = int(it.get("progress", 0))

        st.session_state[f"check_teoria__{tk}__{d_idx}"] = bool(it.get("check_teoria", False))
        st.session_state[f"check_resumo__{tk}__{d_idx}"] = bool(it.get("check_resumo", False))
        st.session_state[f"check_questao__{tk}__{d_idx}"] = bool(it.get("check_questao", False))
        st.session_state[f"check_revisao__{tk}__{d_idx}"] = bool(it.get("check_revisao", False))

        # nivel persistido
        st.session_state[f"nivel__{tk}__{d_idx}"] = it.get("nivel", "N/A") or "N/A"

    # atualiza mapa e geral (sobrescreve se necessário)
    st.session_state["tema_progress_map"] = dict(tema_map or {})
    st.session_state["progresso_geral"] = int(geral or 0)
    st.session_state["progress_loaded"] = True


if "user" not in st.session_state:
    st.subheader("Entrar (demo)")
    email = st.text_input("email")
    password = st.text_input("Senha", type="password")
    if st.button("Login"):
        try:
            sign = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user_resp = supabase.auth.get_user()

            user = None
            if user_resp:
                data = getattr(user_resp, "data", None)
                if data:
                    if isinstance(data, dict):
                        user = data.get("user") or data
                    else:
                        user = getattr(data, "user", data)
                else:
                    user = getattr(user_resp, "user", None) or (user_resp if isinstance(user_resp, dict) else None)

            user_id = None
            user_email = ""
            if user:
                if isinstance(user, dict):
                    user_id = user.get("id")
                    user_email = user.get("email", "")
                else:
                    user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
                    user_email = getattr(user, "email", "") or getattr(user, "user_email", "")

            if user and user_id:
                st.session_state["user"] = user
                st.session_state["user_id"] = user_id
                st.session_state["user_email"] = user_email

                after_login_load()

                st.success("Logado como " + (user_email))
            else:
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
                st.error("Falha ao obter usuário ou user_id. Verifique credenciais.")
        except Exception as e:
            st.error("Erro login: " + str(e))
else:
    user = st.session_state.get("user")
    user_email = st.session_state.get("user_email", "")
    user_id = st.session_state.get("user_id") or (user.get("id") if isinstance(user, dict) else getattr(user, "id", None))
    st.write(f"Usuário: **{user_email or user_id or '(sem email)'}**")




