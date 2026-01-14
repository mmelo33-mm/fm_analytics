import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import criar_tabela, inserir_partida, buscar_partidas, deletar_partida
from utils import (
    calcular_aproveitamento, comparar_com_benchmark, calcular_score_benchmark,
    diagnostico_geral, validar_dados_partida, BENCHMARK, RESULTADO_VITORIA,
    RESULTADO_EMPATE, RESULTADO_DERROTA, LOCAL_CASA, LOCAL_FORA,
    calcular_percentual_passes, calcular_percentual_finalizacao
)
from licencas import Licenca, PLANOS, get_mensagem_upgrade, comparar_planos



















import streamlit as st
from auth import criar_tabela_usuarios, buscar_usuario
from licencas import Licenca

# Criar tabelas
criar_tabela_usuarios()

# Verificar login
if 'logado' not in st.session_state or not st.session_state.logado:
    st.warning("🔒 Faça login para acessar")
    if st.button("🔑 Ir para Login"):
        st.switch_page("pages/1_Login.py")
    st.stop()

# Buscar dados do usuário
usuario = buscar_usuario(st.session_state.usuario_id)
if not usuario:
    st.error("Erro ao carregar usuário")
    st.stop()

# Criar licença
from datetime import datetime
data_exp = None
if usuario['data_expiracao']:
    data_exp = datetime.fromisoformat(usuario['data_expiracao'])

licenca = Licenca(usuario['plano'], data_exp)
st.session_state.licenca = licenca






# =======================
# CONFIGURAÇÃO PÁGINA
# =======================
st.set_page_config(
    page_title="FM Analytics",
    page_icon="⚽",
    layout="wide"
)

# =======================
# INICIALIZAÇÃO
# =======================
criar_tabela()

# Inicializar licença do usuário (por enquanto FREE, depois virá do banco)
if 'licenca' not in st.session_state:
    # EXEMPLO: Usuário FREE
    st.session_state.licenca = Licenca("FREE")
    
    # EXEMPLO: Usuário PRO (para testar)
    # data_exp = datetime.now() + timedelta(days=30)
    # st.session_state.licenca = Licenca("PRO", data_exp)

licenca = st.session_state.licenca

# =======================
# HEADER
# =======================
col_logo, col_licenca, col_upgrade = st.columns([2, 1, 1])

with col_logo:
    st.title("⚽ FM Analytics")
    st.caption("Análise profissional para Football Manager")

with col_licenca:
    info = licenca.get_info()
    st.metric(
        label=f"{info['badge']} {info['nome']}",
        value=f"{info['limite_partidas']} partidas" if info['limite_partidas'] < 999 else "Ilimitado",
        delta=f"{info['dias_restantes']} dias" if info['plano'] != "FREE" else None
    )

# with col_upgrade:
#     if licenca.plano == "FREE":
#         if st.button("⭐ FAZER UPGRADE", type="primary", use_container_width=True):
#             st.switch_page("pages/upgrade.py")  # Página de upgrade (criar depois)
#     elif licenca.dias_restantes() < 7:
#         st.warning(f"⚠️ {licenca.dias_restantes()} dias restantes")
#         if st.button("🔄 Renovar", type="primary", use_container_width=True):
#             st.switch_page("pages/pagamento.py")

# =======================
# TABS PRINCIPAIS
# =======================
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Cadastrar Partida",
    "📊 Dashboard", 
    "📋 Histórico",
    "⭐ Preços"
])

# =======================
# TAB 1: CADASTRO
# =======================
with tab1:
    st.subheader("📝 Cadastro da Partida")
    
    # Verificar limite de partidas
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
        
        # Mostrar quantas partidas tem cadastradas
        st.divider()
        st.subheader("💡 Dica: Libere espaço deletando partidas antigas")
        st.info(f"Você tem **{num_partidas}/{licenca.configuracao['limite_partidas']}** partidas cadastradas. Delete algumas na aba '📋 Histórico' para liberar espaço.")
        
        st.stop()
    
    # Mostrar contador
    partidas_restantes = licenca.configuracao['limite_partidas'] - num_partidas
    
    if licenca.plano == "FREE":
        if partidas_restantes <= 2:
            st.warning(f"⚠️ Apenas **{partidas_restantes}** partida(s) restante(s)! Faça upgrade para continuar.")
        else:
            st.info(f"📊 Partidas: **{num_partidas}/{licenca.configuracao['limite_partidas']}** | Restantes: **{partidas_restantes}**")
    
    # Formulário de cadastro
    col1, col2 = st.columns(2)
    
    with col1:
        time_usuario = st.text_input("Seu time", key="time_usuario")
        local = st.selectbox("Local do jogo", [LOCAL_CASA, LOCAL_FORA])
        temporada = st.text_input("Temporada (ex: 2025/26)")
        rodada = st.number_input("Rodada", min_value=1, step=1)
    
    with col2:
        time_adv = st.text_input("Time adversário")
        competicao = st.text_input("Competição")
        data = st.date_input("Data da partida")

    st.divider()
    
    # Estatísticas
    col_user, col_adv = st.columns(2)
    
    with col_user:
        st.subheader("📊 Seu Time")
        gols_usuario = st.number_input("Gols", min_value=0, step=1, key="gols_user")
        posse_usuario = st.number_input("Posse de bola (%)", 0, 100, key="posse_user")
        remates_usuario = st.number_input("Remates", min_value=0, key="remates_user")
        remates_a_baliza_usuario = st.number_input("Remates a baliza", min_value=0, key="baliza_user")
        xg_usuario = st.number_input("xG", min_value=0.0, format="%.2f", key="xg_user")
        oportunidades_flagrantes_usuario = st.number_input("Oportunidades flagrantes", min_value=0, key="opor_user")
        cantos_usuario = st.number_input("Cantos", min_value=0, key="cantos_user")
        passes_totais_usuario = st.number_input("Passes totais", min_value=0, key="passes_tot_user")
        passes_certos_usuario = st.number_input("Passes certos", min_value=0, key="passes_cert_user")
        cruzamentos_totais_usuario = st.number_input("Cruzamentos totais", min_value=0, key="cruz_tot_user")
        cruzamentos_certos_usuario = st.number_input("Cruzamentos certos", min_value=0, key="cruz_cert_user")
    
    with col_adv:
        st.subheader("📉 Adversário")
        gols_adv = st.number_input("Gols", min_value=0, step=1, key="gols_adv")
        posse_adv = st.number_input("Posse de bola (%)", 0, 100, key="posse_adv")
        remates_adv = st.number_input("Remates", min_value=0, key="remates_adv")
        remates_a_baliza_adv = st.number_input("Remates a baliza", min_value=0, key="baliza_adv")
        xg_adv = st.number_input("xG", min_value=0.0, format="%.2f", key="xg_adv")
        oportunidades_flagrantes_adv = st.number_input("Oportunidades flagrantes", min_value=0, key="opor_adv")
        cantos_adv = st.number_input("Cantos", min_value=0, key="cantos_adv")
        passes_totais_adv = st.number_input("Passes totais", min_value=0, key="passes_tot_adv")
        passes_certos_adv = st.number_input("Passes certos", min_value=0, key="passes_cert_adv")
        cruzamentos_totais_adv = st.number_input("Cruzamentos totais", min_value=0, key="cruz_tot_adv")
        cruzamentos_certos_adv = st.number_input("Cruzamentos certos", min_value=0, key="cruz_cert_adv")

    # Resultado automático
    if gols_usuario > gols_adv:
        resultado = RESULTADO_VITORIA
        resultado_emoji = "🎉"
    elif gols_usuario < gols_adv:
        resultado = RESULTADO_DERROTA
        resultado_emoji = "😞"
    else:
        resultado = RESULTADO_EMPATE
        resultado_emoji = "🤝"

    st.info(f"{resultado_emoji} Resultado: **{resultado}** ({gols_usuario} x {gols_adv})")

    # Botão de salvar
    if st.button("💾 Salvar partida", type="primary", use_container_width=True):
        dados = (
            st.session_state.usuario_id,
            time_usuario, time_adv, local, competicao, temporada, str(data), rodada,
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
            if mensagem:
                st.warning(mensagem)
            
            if inserir_partida(dados):
                st.success("✅ Partida salva com sucesso!")
                st.balloons()
                
                # Se for última partida gratuita, mostrar oferta
                if licenca.plano == "FREE" and (num_partidas + 1) >= licenca.configuracao['limite_partidas']:
                    st.warning("🎉 Você cadastrou todas as suas partidas gratuitas!")
                    st.info("⭐ **Oferta especial:** Upgrade agora e ganhe 30% OFF no primeiro mês!")
                    if st.button("Ver Planos Premium", type="primary"):
                        st.switch_page("pages/upgrade.py")
            else:
                st.error("❌ Erro ao salvar partida. Tente novamente.")




# =======================
# TAB 2: DASHBOARD
# =======================

with tab2:
    st.subheader("📊 Dashboard Geral")
    
    partidas = buscar_partidas(st.session_state.usuario_id)
    
    if not partidas:
        st.info("🎯 Nenhuma partida cadastrada ainda. Comece adicionando sua primeira partida!")
        st.stop()
    
    # Criar DataFrame
    colunas = [
        "id", "usuario_id", "time_usuario", "time_adv", "local", "competicao", "temporada", "data", "rodada",
        "posse_usuario", "remates_usuario", "remates_a_baliza_usuario", "xg_usuario",
        "oportunidades_flagrantes_usuario", "cantos_usuario", "passes_totais_usuario",
        "passes_certos_usuario", "cruzamentos_totais_usuario", "cruzamentos_certos_usuario",
        "gols_usuario", "posse_adv", "remates_adv", "remates_a_baliza_adv", "xg_adv",
        "oportunidades_flagrantes_adv", "cantos_adv", "passes_totais_adv",
        "passes_certos_adv", "cruzamentos_totais_adv", "cruzamentos_certos_adv",
        "gols_adv", "resultado"
    ]
    
    df = pd.DataFrame(partidas, columns=colunas)
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data")
    
    # Filtros
    st.subheader("🔍 Filtros")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        temporadas = ["Todas"] + sorted(df["temporada"].unique().tolist())
        temp_selecionada = st.selectbox("Temporada", temporadas)
    
    with col_f2:
        competicoes = ["Todas"] + sorted(df["competicao"].unique().tolist())
        comp_selecionada = st.selectbox("Competição", competicoes)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if temp_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["temporada"] == temp_selecionada]
    if comp_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["competicao"] == comp_selecionada]
    
    if len(df_filtrado) == 0:
        st.warning("⚠️ Nenhuma partida encontrada com os filtros selecionados.")
        st.stop()
    
    st.divider()
    
    # Resultados gerais
    st.subheader("🏆 Resultados")
    
    resumo = df_filtrado["resultado"].value_counts()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 Partidas", len(df_filtrado))
    col2.metric("✅ Vitórias", resumo.get(RESULTADO_VITORIA, 0))
    col3.metric("🤝 Empates", resumo.get(RESULTADO_EMPATE, 0))
    col4.metric("❌ Derrotas", resumo.get(RESULTADO_DERROTA, 0))
    
    # Aproveitamento geral
    aproveitamento_geral = calcular_aproveitamento(df_filtrado)
    st.metric("📊 Aproveitamento Geral", f"{aproveitamento_geral:.1f}%")
    
    # Gráfico de resultados
    fig_resultados = px.pie(
        values=resumo.values,
        names=resumo.index,
        title="Distribuição de Resultados",
        color=resumo.index,
        color_discrete_map={
            RESULTADO_VITORIA: "#00cc66",
            RESULTADO_EMPATE: "#ffcc00",
            RESULTADO_DERROTA: "#ff4444"
        }
    )
    st.plotly_chart(fig_resultados, use_container_width=True)
    
    st.divider()
    
    # Casa x Fora
    st.subheader("🏠 Desempenho: Casa x Fora")
    
    df_casa = df_filtrado[df_filtrado["local"] == LOCAL_CASA]
    df_fora = df_filtrado[df_filtrado["local"] == LOCAL_FORA]
    
    aprov_casa = calcular_aproveitamento(df_casa)
    aprov_fora = calcular_aproveitamento(df_fora)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏠 Em Casa")
        st.metric("Aproveitamento", f"{aprov_casa:.1f}%")
        st.metric("Vitórias", (df_casa["resultado"] == RESULTADO_VITORIA).sum())
        st.metric("Empates", (df_casa["resultado"] == RESULTADO_EMPATE).sum())
        st.metric("Derrotas", (df_casa["resultado"] == RESULTADO_DERROTA).sum())
    
    with col2:
        st.markdown("### ✈️ Fora")
        st.metric("Aproveitamento", f"{aprov_fora:.1f}%")
        st.metric("Vitórias", (df_fora["resultado"] == RESULTADO_VITORIA).sum())
        st.metric("Empates", (df_fora["resultado"] == RESULTADO_EMPATE).sum())
        st.metric("Derrotas", (df_fora["resultado"] == RESULTADO_DERROTA).sum())
    
    st.divider()
    
    # Médias ofensivas
    st.subheader("⚡ Médias")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Gols/jogo", f"{df_filtrado['gols_usuario'].mean():.2f}")
    col2.metric("xG/jogo", f"{df_filtrado['xg_usuario'].mean():.2f}")
    col3.metric("Remates/jogo", f"{df_filtrado['remates_usuario'].mean():.1f}")
    col4.metric("Remates alvo/jogo", f"{df_filtrado['remates_a_baliza_usuario'].mean():.1f}")
    col5.metric("Oportunidades flagrantes/jogo", f"{df_filtrado['oportunidades_flagrantes_usuario'].mean():.2f}")  
    
    # Percentuais
    perc_passes = calcular_percentual_passes(
        df_filtrado['passes_certos_usuario'].sum(),
        df_filtrado['passes_totais_usuario'].sum()
    )
    perc_finalizacao = calcular_percentual_finalizacao(
        df_filtrado['remates_a_baliza_usuario'].sum(),
        df_filtrado['remates_usuario'].sum()
    )
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Posse média", f"{df_filtrado['posse_usuario'].mean():.1f}%")
    col2.metric("Acerto de passes", f"{perc_passes:.1f}%")
    col3.metric("Remates no alvo", f"{perc_finalizacao:.1f}%")
    
    st.divider()
    
    # Comparação com Europa
    # Comparação com Europa
    st.subheader("🌍 Comparação com Padrão Europeu")
    
    metricas = {
        "xg_usuario": ("xG por jogo", df_filtrado["xg_usuario"].mean(), "maior"),
        "gols_usuario": ("Gols por jogo", df_filtrado["gols_usuario"].mean(), "maior"),
        "remates_usuario": ("Remates por jogo", df_filtrado["remates_usuario"].mean(), "maior"),
        "remates_a_baliza_usuario": ("Remates no alvo", df_filtrado["remates_a_baliza_usuario"].mean(), "maior"),
        "posse_usuario": ("Posse média (%)", df_filtrado["posse_usuario"].mean(), "maior"),
        "passes_certos_usuario": ("Passes certos", df_filtrado["passes_certos_usuario"].mean(), "maior"),
        "aproveitamento": ("Aproveitamento (%)", aproveitamento_geral, "maior"),
    }
    
    for chave, (label, meu_valor, regra) in metricas.items():
        benchmark_info = BENCHMARK[chave]
        emoji, status, cor, intervalo = comparar_com_benchmark(meu_valor, benchmark_info, regra)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"{emoji} **{label}**: {meu_valor:.2f} | Referência: {intervalo}")
        with col2:
            st.markdown(f":{cor}[{status}]")

    # Diagnóstico
    score = calcular_score_benchmark(df_filtrado, aproveitamento_geral)
    tipo_msg, msg = diagnostico_geral(score)
    
    st.divider()
    
    if tipo_msg == "success":
        st.success(f"🎯 {msg}")
    elif tipo_msg == "warning":
        st.warning(f"⚠️ {msg}")
    else:
        st.error(f"📉 {msg}")
    
    # Últimos 5 jogos
    st.divider()
    st.subheader("🔥 Últimos 5 Jogos (Seu time x Adversários)")
    
    ultimos_5 = df_filtrado.tail(5)
    aprov_ultimos_5 = calcular_aproveitamento(ultimos_5)
    
    col1, col2, col3, col4, col10, col5, col6, col7, col8, col9= st.columns(10)
    col1.metric("Aproveitamento", f"{aprov_ultimos_5:.1f}%")
    col2.metric("xG médio", f"{ultimos_5['xg_usuario'].mean():.2f}")
    col3.metric("Gols/jogo", f"{ultimos_5['gols_usuario'].mean():.2f}")
    col4.metric("Remates/jogo", f"{ultimos_5['remates_usuario'].mean():.1f}")
    col10.metric("Oportunidades flagrantes/jogo", f"{ultimos_5['oportunidades_flagrantes_usuario'].mean():.1f}")
    col5.metric("Posse média", f"{ultimos_5['posse_usuario'].mean():.1f}%")
    col6.metric("Cruzamentos totais/jogo", f"{ultimos_5['cruzamentos_totais_usuario'].mean():.1f}")
    col7.metric("Cruzamentos certos/jogo", f"{ultimos_5['cruzamentos_certos_usuario'].mean():.1f}")
    col8.metric("Cantos/jogo", f"{ultimos_5['cantos_usuario'].mean():.1f}")
    col9.metric("Aproveitamento de passes", f"{calcular_percentual_passes(ultimos_5['passes_certos_usuario'].sum(), ultimos_5['passes_totais_usuario'].sum()):.1f}%")

    ultimos_5 = df_filtrado.tail(5)
    aprov_ultimos_5 = calcular_aproveitamento(ultimos_5)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1, col2, col3, col4, col10, col5, col6, col7, col8, col9= st.columns(10)
    
    col2.metric("xG médio", f"{ultimos_5['xg_adv'].mean():.2f}")
    col3.metric("Gols/jogo", f"{ultimos_5['gols_adv'].mean():.2f}")
    col4.metric("Remates/jogo", f"{ultimos_5['remates_adv'].mean():.1f}")
    col10.metric("Oportunidades flagrantes/jogo", f"{ultimos_5['oportunidades_flagrantes_adv'].mean():.1f}")
    col5.metric("Posse média", f"{ultimos_5['posse_adv'].mean():.1f}%")
    col6.metric("Cruzamentos totais/jogo", f"{ultimos_5['cruzamentos_totais_adv'].mean():.1f}")
    col7.metric("Cruzamentos certos/jogo", f"{ultimos_5['cruzamentos_certos_adv'].mean():.1f}")
    col8.metric("Cantos/jogo", f"{ultimos_5['cantos_adv'].mean():.1f}")
    col9.metric("Aproveitamento de passes", f"{calcular_percentual_passes(ultimos_5['passes_certos_adv'].sum(), ultimos_5['passes_totais_adv'].sum()):.1f}%")


    st.divider()
    st.subheader("🔥 Últimos 5 Jogos (Casa x Fora)")
    # =======================
    # Últimos 5 EM CASA
    # =======================
    ultimos_5_casa = (
    df_filtrado[df_filtrado["local"] == LOCAL_CASA]
    .sort_values("data")
    .tail(5)
    )

    aprov_5_casa = calcular_aproveitamento(ultimos_5_casa)

    # =======================
    # Últimos 5 FORA
    # =======================
    ultimos_5_fora = (
    df_filtrado[df_filtrado["local"] == LOCAL_FORA]
    .sort_values("data")
    .tail(5)
    )

    aprov_5_fora = calcular_aproveitamento(ultimos_5_fora)

    col1, col2 = st.columns(2)

    # =======================
    # CARD CASA
    # =======================
with col1:
    st.markdown("### 🏠 Últimos 5 em Casa")
    
    if len(ultimos_5_casa) == 0:
        st.info("Nenhum jogo em casa.")
    else:
        st.metric("Aproveitamento", f"{aprov_5_casa:.1f}%")
        st.metric("xG médio", f"{ultimos_5_casa['xg_usuario'].mean():.2f}")
        st.metric("Gols/jogo", f"{ultimos_5_casa['gols_usuario'].mean():.2f}")
        st.metric("Remates/jogo", f"{ultimos_5_casa['remates_usuario'].mean():.1f}")
        st.metric("Oportunidades flagrantes/jogo", f"{ultimos_5_casa['oportunidades_flagrantes_usuario'].mean():.1f}")
        st.metric("Cruzamentos totais/jogo", f"{ultimos_5_casa['cruzamentos_totais_usuario'].mean():.1f}")
        st.metric("Cruzamentos certos/jogo", f"{ultimos_5_casa['cruzamentos_certos_usuario'].mean():.1f}")
        st.metric("Cantos/jogo", f"{ultimos_5_casa['cantos_usuario'].mean():.1f}")
        st.metric("Posse média", f"{ultimos_5_casa['posse_usuario'].mean():.1f}%")

    # =======================
    # CARD FORA
    # =======================
    with col2:
        st.markdown("### ✈️ Últimos 5 Fora")
    
        if len(ultimos_5_fora) == 0:
            st.info("Nenhum jogo fora.")
        else:
            st.metric("Aproveitamento", f"{aprov_5_fora:.1f}%")
        st.metric("xG médio", f"{ultimos_5_fora['xg_usuario'].mean():.2f}")
        st.metric("Gols/jogo", f"{ultimos_5_fora['gols_usuario'].mean():.2f}")
        st.metric("Remates/jogo", f"{ultimos_5_fora['remates_usuario'].mean():.1f}")
        st.metric("Oportunidades flagrantes/jogo", f"{ultimos_5_fora['oportunidades_flagrantes_usuario'].mean():.1f}")
        st.metric("Cruzamentos totais/jogo", f"{ultimos_5_fora['cruzamentos_totais_usuario'].mean():.1f}")
        st.metric("Cruzamentos certos/jogo", f"{ultimos_5_fora['cruzamentos_certos_usuario'].mean():.1f}")
        st.metric("Cantos/jogo", f"{ultimos_5_fora['cantos_usuario'].mean():.1f}")
        st.metric("Posse média", f"{ultimos_5_fora['posse_usuario'].mean():.1f}%")





    # Resultados - Casa
    v_casa = (ultimos_5_casa["resultado"] == RESULTADO_VITORIA).sum()
    e_casa = (ultimos_5_casa["resultado"] == RESULTADO_EMPATE).sum()
    d_casa = (ultimos_5_casa["resultado"] == RESULTADO_DERROTA).sum()

    # Resultados - Fora
    v_fora = (ultimos_5_fora["resultado"] == RESULTADO_VITORIA).sum()
    e_fora = (ultimos_5_fora["resultado"] == RESULTADO_EMPATE).sum()
    d_fora = (ultimos_5_fora["resultado"] == RESULTADO_DERROTA).sum()


    st.divider()
    st.subheader("🔥 Últimos 5 Jogos (Casa x Fora)")
    col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### Últimos 5 Casa")
    st.metric("Vitórias", v_casa)
    st.metric("Empates", e_casa)
    st.metric("Derrotas", d_casa)

with col2:
    st.markdown("###  Últimos 5 Fora")
    st.metric("Vitórias", v_fora)
    st.metric("Empates", e_fora)
    st.metric("Derrotas", d_fora)
with col3:
    st.markdown("### Gráfico de Resultados")
    fig_casa_fora = go.Figure(data=[
        go.Bar(name='Casa', x=['Vitórias', 'Empates', 'Derrotas'], y=[v_casa, e_casa, d_casa], marker_color='indianred'),
        go.Bar(name='Fora', x=['Vitórias', 'Empates', 'Derrotas'], y=[v_fora, e_fora, d_fora], marker_color='lightsalmon')
    ])
    fig_casa_fora.update_layout(barmode='group', title_text='Resultados: Casa vs Fora')
    st.plotly_chart(fig_casa_fora, use_container_width=True)

# =======================
# TAB 3: HISTÓRICO
# =======================
# =======================
# TAB 3: HISTÓRICO
# =======================
with tab3:
    st.subheader("📋 Histórico Completo de Partidas")
    
    if not partidas:
        st.info("Nenhuma partida cadastrada.")
        st.stop()
    
    # Exibir tabela
    df_display = df.copy()
    df_display["data"] = df_display["data"].dt.strftime("%d/%m/%Y")
    
    st.dataframe(
        df_display[[
            "data", "time_usuario", "gols_usuario", "gols_adv", "time_adv",
            "resultado", "local", "competicao", "temporada", "xg_usuario", "xg_adv"
        ]],
        use_container_width=True,
        hide_index=True
    )
    
    # Opção de deletar
    st.divider()
    st.subheader("🗑️ Gerenciar Partidas")
    
    partida_deletar = st.selectbox(
        "Selecione uma partida para deletar",
        options=df["id"].tolist(),
        format_func=lambda x: f"{df[df['id']==x]['data'].iloc[0].strftime('%d/%m/%Y')} - {df[df['id']==x]['time_usuario'].iloc[0]} {df[df['id']==x]['gols_usuario'].iloc[0]}x{df[df['id']==x]['gols_adv'].iloc[0]} {df[df['id']==x]['time_adv'].iloc[0]}"
    )
    
    if st.button("🗑️ Deletar partida selecionada", type="secondary"):
        if deletar_partida(partida_deletar):
            st.success("✅ Partida deletada com sucesso!")
            st.rerun()
        else:
            st.error("❌ Erro ao deletar partida.")

# =======================
# TAB 4: PLANOS & UPGRADE
# =======================
# with tab4:
#     st.subheader("⭐ Planos e Upgrade")
    
#     # Mostrar plano atual
#     info = licenca.get_info()
    
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.success(f"""
#         ### {info['badge']} Plano Atual: {info['nome']}
        
#         {'✅ Ativo' if info['ativa'] else '❌ Expirado'}
#         {f"📅 Expira em {info['dias_restantes']} dias" if info['plano'] != 'FREE' else ''}
#         """)
    
#     st.divider()
    
#     # Comparação de planos
#     st.subheader("📊 Compare os Planos")
    
#     cols = st.columns(4)
    
#     for idx, (plano_id, plano) in enumerate(PLANOS.items()):
#         with cols[idx]:
#             # Card do plano
#             cor_badge = {"FREE": "🆓", "STARTER": "🌟", "PRO": "⚡", "TEAM": "🏆"}
            
#             st.markdown(f"""
#             ### {cor_badge[plano_id]} {plano['nome']}
            
#             **{'GRÁTIS' if plano['preco_mensal'] == 0 else f"R$ {plano['preco_mensal']:.2f}/mês"}**
            
#             {f"*ou R$ {plano['preco_anual']:.2f}/ano*" if plano['preco_anual'] > 0 else ''}
#             """)
            
#             st.markdown("---")
            
#             # Recursos
#             st.markdown(f"""
#             **Recursos:**
            
#             {'✅' if plano['limite_partidas'] > 999 else '📊'} {plano['limite_partidas'] if plano['limite_partidas'] < 999 else 'Ilimitadas'} partidas
            
#             {'✅' if plano['exportar_pdf'] else '❌'} Exportar PDF
            
#             {'✅' if plano.get('exportar_excel', False) else '❌'} Exportar Excel
            
#             {'✅' if plano.get('backup_nuvem', False) else '❌'} Backup nuvem
            
#             {'✅' if plano.get('multiplos_times', False) else '❌'} Múltiplos times
            
#             **Suporte:** {plano['suporte']}
#             """)
            
#             # Botão de ação
#             if plano_id == licenca.plano:
#                 st.success("✅ Plano Atual")
#             elif plano_id == "FREE":
#                 st.info("Grátis para sempre")
#             else:
#                 if st.button(f"Escolher {plano['nome']}", key=f"btn_{plano_id}", use_container_width=True):
#                     st.info(f"Redirecionando para pagamento do plano {plano['nome']}...")
#                     # Aqui você implementaria a integração com pagamento
    
#     st.divider()
    
#     # Ofertas especiais
#     st.subheader("🎁 Ofertas Especiais")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.info("""
#         ### 🎉 Oferta de Lançamento
        
#         **30% OFF no primeiro mês** em qualquer plano pago!
        
#         Use o cupom: **LANCAMENTO30**
#         """)
    
#     with col2:
#         st.success("""
#         ### 💎 Plano Anual
        
#         **Economize 17%** pagando anualmente!
        
#         Pague 10 meses, ganhe 12!
#         """)
    
#     st.divider()
    
#     # FAQ
#     with st.expander("❓ Perguntas Frequentes"):
#         st.markdown("""
#         **Posso cancelar a qualquer momento?**
#         Sim! Sem fidelidade ou multas.
        
#         **Como funciona o período de teste?**
#         7 dias grátis para testar o plano PRO.
        
#         **Posso mudar de plano depois?**
#         Sim! Upgrade ou downgrade a qualquer momento.
        
#         **Aceitam quais formas de pagamento?**
#         Cartão de crédito, PIX e boleto.
        
#         **Os dados ficam salvos ao cancelar?**
#         Sim, por 30 dias. Depois são excluídos.
#         """)
    
#     # Testemunhos
#     st.divider()
#     st.subheader("💬 O que dizem nossos usuários")
    
#     col1, col2, col3 = st.columns(3)

#     with col1:
#         st.info("""
#         *"Mudou completamente minha forma de jogar FM. Agora entendo onde estou errando!"*
        
#         — João, SP
#         """)
    
#     with col2:
#         st.info("""
#         *"Vale muito a pena! Os relatórios em PDF economizam horas de análise."*
        
#         — Maria, RJ
#         """)
    
#     with col3:
#         st.info("""
#         *"Indispensável para quem leva FM a sério. Plano PRO é o melhor investimento!"*
        
#         — Pedro, MG
#         """)

# =======================
# FOOTER
# =======================
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("📧 Suporte: onzevirtual1895@gmail.com")

with col2:
    st.caption("🔒 Seus dados estão seguros")

with col3:
    st.caption(f"v1.0 | {licenca.get_badge()} {licenca.plano}")