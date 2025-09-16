import streamlit as st

def is_authenticated():
    return st.session_state.get("user") is not None

def show_login_prompt(message="Faça login para acessar esta página."):
    st.warning(message)
    # opcional: link para a página de login (Se você tiver uma Page chamada "Login")
    st.write("Vá para a página **Login** no menu e entre com sua conta.")
    # opcional: mostrar um botão que redireciona via query params (ver alternativa abaixo)
    if st.button("Ir para Login"):
        st.switch_page("1_LOGIN.py")

def require_login():
    if not is_authenticated():
        show_login_prompt()
        st.stop()   # para a execução da página (não mostra nada além do aviso)
