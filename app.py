import streamlit as st

# CONFIGURAÇÃO PÁGINA (Sempre o primeiro comando Streamlit)
st.set_page_config(
    page_title="FM Analytics 26",
    page_icon="⚽",
    layout="wide"
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
from database import inserir_partida, buscar_partidas, deletar_partida
from licencas import Licenca, PLANOS, get_mensagem_upgrade, comparar_planos
from auth import buscar_usuario
from lang import STRINGS
from utils import (
    calcular_aproveitamento, comparar_com_benchmark, calcular_score_benchmark,
    diagnostico_geral, validar_dados_partida, BENCHMARK, RESULTADO_VITORIA,
    RESULTADO_EMPATE, RESULTADO_DERROTA, LOCAL_CASA, LOCAL_FORA,
    calcular_percentual_passes, calcular_percentual_finalizacao
)

# =======================
# IDIOMA E INTERNACIONALIZAÇÃO
# =======================
if 'idioma' not in st.session_state:
    st.session_state.idioma = "pt-br"

with st.sidebar:
    st.title("⚙️ Settings / Configurações")
    st.session_state.idioma = st.selectbox(
        "🌐 Language",
        options=["pt-br", "en", "es", "pt-pt"],
        format_func=lambda x: {
            "pt-br": "Português (BR)", 
            "en": "English", 
            "es": "Español", 
            "pt-pt": "Português (PT)"
        }[x]
    )

t = STRINGS[st.session_state.idioma]

# =======================
# SEGURANÇA E LOGIN
# =======================
if 'logado' not in st.session_state or not st.session_state.logado:
    st.warning("🔒 Please login / Faça login")
    if st.button("🔑 Login"):
        st.switch_page("pages/1_Login.py")
    st.stop()

usuario = buscar_usuario(st.session_state.usuario_id)
if not usuario:
    st.error("User Error / Erro ao carregar usuário")
    st.stop()

# Criar licença
data_exp = None
if usuario['data_expiracao']:
    data_exp = datetime.fromisoformat(usuario['data_expiracao'])

licenca = Licenca(usuario['plano'], data_exp)
st.session_state.licenca = licenca

# =======================
# HEADER
# =======================
col_logo, col_licenca, col_upgrade = st.columns([2, 1, 1])

with col_logo:
    st.title(t["header_titulo"])
    st.caption(t["header_caption"])

# =======================
# TABS PRINCIPAIS
# =======================
tab1, tab2, tab3, tab4 = st.tabs([
    t["tab_cadastro"], 
    t["tab_dashboard"], 
    t["tab_historico"], 
    t["tab_ia"]
])

# =======================
# TAB 1: CADASTRO
# =======================
with tab1:
    st.subheader(t["tab_cadastro"])
    
    partidas_existentes = buscar_partidas(st.session_state.usuario_id)
    num_partidas = len(partidas_existentes)
    pode_cadastrar, mensagem_erro = licenca.pode_cadastrar_partida(num_partidas)
    
    if not pode_cadastrar:
        msg = get_mensagem_upgrade("limite_partidas")
        st.error(f"### {msg['titulo']}")
        st.warning(msg['texto'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**{msg['oferta']}**")
        with col2:
            if st.button(f"⭐ {msg['cta']}", type="primary", use_container_width=True):
                st.switch_page("pages/upgrade.py")
        st.stop()
    
    col1, col2 = st.columns(2)
    with col1:
        time_usuario = st.text_input(t["lbl_seu_time"], key="time_usuario")
        local = st.selectbox(t["lbl_local"], [LOCAL_CASA, LOCAL_FORA])
        temporada = st.text_input("Season / Temporada (ex: 2025/26)")
        rodada = st.number_input("Round / Rodada", min_value=1, step=1)
    
    with col2:
        time_adv = st.text_input(t["lbl_adversario"])
        competicao = st.text_input("Competition / Competição")
        data = st.date_input("Date / Data")

    st.divider()
    
    col_user, col_adv = st.columns(2)
    with col_user:
        st.subheader(f"📊 {t['lbl_seu_time']}")
        gols_usuario = st.number_input("Gols", min_value=0, step=1, key="gols_user")
        posse_usuario = st.number_input("Possess. % / Posse %", 0, 100, key="posse_user")
        remates_usuario = st.number_input("Shots / Remates", min_value=0, key="remates_user")
        remates_a_baliza_usuario = st.number_input("On Target / Remates Baliza", min_value=0, key="baliza_user")
        xg_usuario = st.number_input("xG", min_value=0.0, format="%.2f", key="xg_user")
        oportunidades_flagrantes_usuario = st.number_input("Big Chances / Flagrantes", min_value=0, key="opor_user")
        cantos_usuario = st.number_input("Corners / Cantos", min_value=0, key="cantos_user")
        passes_totais_usuario = st.number_input("Total Passes", min_value=0, key="passes_tot_user")
        passes_certos_usuario = st.number_input("Passes Completed", min_value=0, key="passes_cert_user")
        cruzamentos_totais_usuario = st.number_input("Total Crosses", min_value=0, key="cruz_tot_user")
        cruzamentos_certos_usuario = st.number_input("Crosses Completed", min_value=0, key="cruz_cert_user")
    
    with col_adv:
        st.subheader(f"📉 {t['lbl_adversario']}")
        gols_adv = st.number_input("Gols", min_value=0, step=1, key="gols_adv", help="Adversário")
        posse_adv = st.number_input("Possess. %", 0, 100, key="posse_adv")
        remates_adv = st.number_input("Shots", min_value=0, key="remates_adv")
        remates_a_baliza_adv = st.number_input("On Target", min_value=0, key="baliza_adv")
        xg_adv = st.number_input("xG ", min_value=0.0, format="%.2f", key="xg_adv")
        oportunidades_flagrantes_adv = st.number_input("Big Chances ", min_value=0, key="opor_adv")
        cantos_adv = st.number_input("Corners ", min_value=0, key="cantos_adv")
        passes_totais_adv = st.number_input("Total Passes ", min_value=0, key="passes_tot_adv")
        passes_certos_adv = st.number_input("Passes Completed ", min_value=0, key="passes_cert_adv")
        cruzamentos_totais_adv = st.number_input("Total Crosses ", min_value=0, key="cruz_tot_adv")
        cruzamentos_certos_adv = st.number_input("Crosses Completed ", min_value=0, key="cruz_cert_adv")

    # Resultado automático (Mapeado para labels do lang.py se necessário)
    if gols_usuario > gols_adv:
        resultado = RESULTADO_VITORIA
        resultado_emoji = "🎉"
    elif gols_usuario < gols_adv:
        resultado = RESULTADO_DERROTA
        resultado_emoji = "😞"
    else:
        resultado = RESULTADO_EMPATE
        resultado_emoji = "🤝"

    st.info(f"{resultado_emoji} {t['lbl_resultado']}: **{resultado}** ({gols_usuario} x {gols_adv})")

    if st.button(t["btn_salvar"], type="primary", use_container_width=True):
        dados = (
            st.session_state.usuario_id, time_usuario, time_adv, local, competicao, temporada, str(data), rodada,
            posse_usuario, remates_usuario, remates_a_baliza_usuario, xg_usuario,
            oportunidades_flagrantes_usuario, cantos_usuario, passes_totais_usuario,
            passes_certos_usuario, cruzamentos_totais_usuario, cruzamentos_certos_usuario,
            gols_usuario, posse_adv, remates_adv, remates_a_baliza_adv, xg_adv,
            oportunidades_flagrantes_adv, cantos_adv, passes_totais_adv,
            passes_certos_adv, cruzamentos_totais_adv, cruzamentos_certos_adv,
            gols_adv, resultado
        )
        valido, mensagem = validar_dados_partida(dados)
        
        if not valido:
            st.error(mensagem)
        else:
            if inserir_partida(dados):
                st.success(t["msg_sucesso"])
                time.sleep(1)
                st.rerun()

# =======================
# TAB 2: DASHBOARD
# =======================
with tab2:
    st.subheader(t["tab_dashboard"])
    partidas = buscar_partidas(st.session_state.usuario_id)
    
    if not partidas:
        st.info("🎯 Start by adding your first match / Comece adicionando sua primeira partida!")
        st.stop()
    
    df = pd.DataFrame(partidas, columns=[
        "id", "usuario_id", "time_usuario", "time_adv", "local", "competicao", "temporada", "data", "rodada",
        "posse_usuario", "remates_usuario", "remates_a_baliza_usuario", "xg_usuario",
        "oportunidades_flagrantes_usuario", "cantos_usuario", "passes_totais_usuario",
        "passes_certos_usuario", "cruzamentos_totais_usuario", "cruzamentos_certos_usuario",
        "gols_usuario", "posse_adv", "remates_adv", "remates_a_baliza_adv", "xg_adv",
        "oportunidades_flagrantes_adv", "cantos_adv", "passes_totais_adv",
        "passes_certos_adv", "cruzamentos_totais_adv", "cruzamentos_certos_adv",
        "gols_adv", "resultado"
    ])
    df["data"] = pd.to_datetime(df["data"])
    
    # Filtros e métricas seguem o mesmo padrão usando t["chave"]
    # ... (O restante do Dashboard deve usar as variáveis t["metrica_aproveitamento"], etc.)

# =======================
# TAB 4: ASSISTENTE IA (NOVA)
# =======================
with tab4:
    st.subheader(t["tab_ia"])
    st.info("AI Analysis environment ready. Integrate Gemini API here.")
    # Aqui entrará o código do model.generate_content que planejamos

# =======================
# FOOTER
# =======================
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("📧 onzevirtual1895@gmail.com")
with col_f2:
    st.caption(f"Language: {st.session_state.idioma.upper()}")
with col_f3:
    st.caption("V 1.12 - Dev Mode")