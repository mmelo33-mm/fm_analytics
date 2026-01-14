import streamlit as st
from auth import criar_tabela_usuarios, cadastrar_usuario, fazer_login

st.set_page_config(page_title="Login - FM Analytics", page_icon="🔐")

criar_tabela_usuarios()

if 'logado' in st.session_state and st.session_state.logado:
    st.success(f"✅ Logado como {st.session_state.email}")
    if st.button("🚪 Sair"):
        st.session_state.logado = False
        st.rerun()
    if st.button("🏠 Ir para Dashboard"):
        st.switch_page("app.py")
    st.stop()

st.title("⚽ FM Analytics")

tab1, tab2 = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

with tab1:
    with st.form("login"):
        email = st.text_input("👤 Usuário")
        senha = st.text_input("🔒 Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            sucesso, resultado = fazer_login(email, senha)
            if sucesso:
                st.session_state.logado = True
                st.session_state.usuario_id = resultado['id']
                st.session_state.email = resultado['email']
                st.session_state.plano = resultado['plano']
                st.success("✅ Login realizado!")
                st.rerun()
            else:
                st.error(f"❌ {resultado}")

with tab2:
    with st.form("registro"):
        nome = st.text_input("👤 Nome")
        email_novo = st.text_input("👤 Usuário")
        senha_nova = st.text_input("🔒 Senha (min 6 caracteres)", type="password")
        aceita = st.checkbox("Confirmo que vou criar login")
        submit = st.form_submit_button("Criar Conta Grátis")
        
        if submit:
            if len(senha_nova) < 6:
                st.error("❌ Senha muito curta")
            elif not aceita:
                st.error("❌ Marque a confirmação para criar a conta")
            else:
                sucesso, resultado = cadastrar_usuario(email_novo, senha_nova, nome)
                if sucesso:
                    st.success("🎉 Conta criada! Faça login.")
                else:
                    st.error(f"❌ {resultado}")