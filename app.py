import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import requests
from datetime import datetime, timedelta
from database import inserir_partida, buscar_partidas, deletar_partida
from utils import (
    calcular_aproveitamento, comparar_com_benchmark, calcular_score_benchmark,
    diagnostico_geral, validar_dados_partida, BENCHMARK, RESULTADO_VITORIA,
    RESULTADO_EMPATE, RESULTADO_DERROTA, LOCAL_CASA, LOCAL_FORA,
    calcular_percentual_passes, calcular_percentual_finalizacao
)
from licencas import Licenca, PLANOS, get_mensagem_upgrade, comparar_planos
from auth import buscar_usuario
from lang import STRINGS, IDIOMAS, t

# =======================
# CONFIGURAÇÃO PÁGINA
# =======================
st.set_page_config(
    page_title="FM Analytics 26",
    page_icon="⚽",
    layout="wide"
)

# =======================
# IDIOMA — inicializar antes de tudo
# =======================
if "idioma" not in st.session_state:
    st.session_state.idioma = "pt-br"

# =======================
# VERIFICAR LOGIN
# =======================
if 'logado' not in st.session_state or not st.session_state.logado:
    st.warning(t("login_aviso", st.session_state.idioma))
    if st.button(t("btn_ir_login", st.session_state.idioma)):
        st.switch_page("pages/1_Login.py")
    st.stop()

# Buscar dados do usuário
usuario = buscar_usuario(st.session_state.usuario_id)
if not usuario:
    st.error(t("erro_usuario", st.session_state.idioma))
    st.stop()

# Criar licença
data_exp = None
if usuario['data_expiracao']:
    data_exp = datetime.fromisoformat(usuario['data_expiracao'])

licenca = Licenca(usuario['plano'], data_exp)
st.session_state.licenca = licenca

if 'licenca' not in st.session_state:
    st.session_state.licenca = Licenca("FREE")

licenca = st.session_state.licenca
lang = st.session_state.idioma

# =======================
# HEADER
# =======================
col_logo, col_licenca, col_upgrade, col_idioma = st.columns([2, 1, 1, 1])

with col_logo:
    st.title(t("header_titulo", lang))
    st.caption(t("header_caption", lang))

with col_idioma:
    idioma_labels = list(IDIOMAS.keys())
    idioma_valores = list(IDIOMAS.values())
    idx_atual = idioma_valores.index(lang) if lang in idioma_valores else 0
    idioma_label = st.selectbox(
        t("lbl_idioma", lang),
        options=idioma_labels,
        index=idx_atual,
        label_visibility="collapsed",
        key="seletor_idioma"
    )
    novo_idioma = IDIOMAS[idioma_label]
    if novo_idioma != st.session_state.idioma:
        st.session_state.idioma = novo_idioma
        st.rerun()

# =======================
# TABS PRINCIPAIS
# =======================
tab1, tab2, tab3, tab4 = st.tabs([
    t("tab_cadastro", lang),
    t("tab_dashboard", lang),
    t("tab_historico", lang),
    t("tab_ia", lang),
])

# =======================
# TAB 1: CADASTRO
# =======================
with tab1:
    st.subheader(t("cadastro_titulo", lang))

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
        st.divider()
        st.subheader(t("limite_dica", lang))
        limite_txt = t("limite_info", lang).format(
            atual=num_partidas,
            max=licenca.configuracao['limite_partidas']
        )
        st.info(limite_txt)
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        time_usuario = st.text_input(t("lbl_seu_time", lang), key="time_usuario")
        local = st.selectbox(t("lbl_local", lang), [LOCAL_CASA, LOCAL_FORA])
        temporada = st.text_input(t("lbl_temporada", lang))
        rodada = st.number_input(t("lbl_rodada", lang), min_value=1, step=1)

    with col2:
        time_adv = st.text_input(t("lbl_adversario", lang))
        competicao = st.text_input(t("lbl_competicao", lang))
        data = st.date_input(t("lbl_data", lang))

    st.divider()

    col_user, col_adv = st.columns(2)

    with col_user:
        st.subheader(t("lbl_seu_time_stats", lang))
        gols_usuario = st.number_input(t("lbl_gols", lang), min_value=0, step=1, key="gols_user")
        posse_usuario = st.number_input(t("lbl_posse", lang), 0, 100, key="posse_user")
        remates_usuario = st.number_input(t("lbl_remates", lang), min_value=0, key="remates_user")
        remates_a_baliza_usuario = st.number_input(t("lbl_remates_baliza", lang), min_value=0, key="baliza_user")
        xg_usuario = st.number_input(t("lbl_xg", lang), min_value=0.0, format="%.2f", key="xg_user")
        oportunidades_flagrantes_usuario = st.number_input(t("lbl_oportunidades", lang), min_value=0, key="opor_user")
        cantos_usuario = st.number_input(t("lbl_cantos", lang), min_value=0, key="cantos_user")
        passes_totais_usuario = st.number_input(t("lbl_passes_totais", lang), min_value=0, key="passes_tot_user")
        passes_certos_usuario = st.number_input(t("lbl_passes_certos", lang), min_value=0, key="passes_cert_user")
        cruzamentos_totais_usuario = st.number_input(t("lbl_cruzamentos_totais", lang), min_value=0, key="cruz_tot_user")
        cruzamentos_certos_usuario = st.number_input(t("lbl_cruzamentos_certos", lang), min_value=0, key="cruz_cert_user")

    with col_adv:
        st.subheader(t("lbl_adv_stats", lang))
        gols_adv = st.number_input(t("lbl_gols", lang), min_value=0, step=1, key="gols_adv")
        posse_adv = st.number_input(t("lbl_posse", lang), 0, 100, key="posse_adv")
        remates_adv = st.number_input(t("lbl_remates", lang), min_value=0, key="remates_adv")
        remates_a_baliza_adv = st.number_input(t("lbl_remates_baliza", lang), min_value=0, key="baliza_adv")
        xg_adv = st.number_input(t("lbl_xg", lang), min_value=0.0, format="%.2f", key="xg_adv")
        oportunidades_flagrantes_adv = st.number_input(t("lbl_oportunidades", lang), min_value=0, key="opor_adv")
        cantos_adv = st.number_input(t("lbl_cantos", lang), min_value=0, key="cantos_adv")
        passes_totais_adv = st.number_input(t("lbl_passes_totais", lang), min_value=0, key="passes_tot_adv")
        passes_certos_adv = st.number_input(t("lbl_passes_certos", lang), min_value=0, key="passes_cert_adv")
        cruzamentos_totais_adv = st.number_input(t("lbl_cruzamentos_totais", lang), min_value=0, key="cruz_tot_adv")
        cruzamentos_certos_adv = st.number_input(t("lbl_cruzamentos_certos", lang), min_value=0, key="cruz_cert_adv")

    if gols_usuario > gols_adv:
        resultado = RESULTADO_VITORIA
        resultado_emoji = "🎉"
    elif gols_usuario < gols_adv:
        resultado = RESULTADO_DERROTA
        resultado_emoji = "😞"
    else:
        resultado = RESULTADO_EMPATE
        resultado_emoji = "🤝"

    info_txt = t("resultado_info", lang).format(
        emoji=resultado_emoji, resultado=resultado,
        gols_u=gols_usuario, gols_a=gols_adv
    )
    st.info(info_txt)

    if st.button(t("btn_salvar", lang), type="primary", use_container_width=True):
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
                progress_text = t("msg_salvando", lang)
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.02)
                my_bar.progress(percent_complete + 1, text=progress_text)
                time.sleep(1)
                my_bar.empty()
                st.success(t("msg_sucesso", lang))


# =======================
# TAB 2: DASHBOARD
# =======================
with tab2:
    st.subheader(t("dashboard_titulo", lang))

    partidas = buscar_partidas(st.session_state.usuario_id)

    if not partidas:
        st.info(t("nenhuma_partida", lang))
        st.stop()

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
    st.subheader(t("filtros_titulo", lang))
    col_f1, col_f2 = st.columns(2)

    todas = t("filtro_todas", lang)

    with col_f1:
        temporadas = [todas] + sorted(df["temporada"].unique().tolist())
        temp_selecionada = st.selectbox(t("lbl_filtro_temporada", lang), temporadas)

    with col_f2:
        competicoes = [todas] + sorted(df["competicao"].unique().tolist())
        comp_selecionada = st.selectbox(t("lbl_filtro_competicao", lang), competicoes)

    df_filtrado = df.copy()
    if temp_selecionada != todas:
        df_filtrado = df_filtrado[df_filtrado["temporada"] == temp_selecionada]
    if comp_selecionada != todas:
        df_filtrado = df_filtrado[df_filtrado["competicao"] == comp_selecionada]

    if len(df_filtrado) == 0:
        st.warning(t("nenhum_filtro", lang))
        st.stop()

    st.divider()

    # Resultados gerais
    st.subheader(t("resultados_titulo", lang))

    resumo = df_filtrado["resultado"].value_counts()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("total_partidas", lang), len(df_filtrado))
    col2.metric(t("vitorias", lang), resumo.get(RESULTADO_VITORIA, 0))
    col3.metric(t("empates", lang), resumo.get(RESULTADO_EMPATE, 0))
    col4.metric(t("derrotas", lang), resumo.get(RESULTADO_DERROTA, 0))

    aproveitamento_geral = calcular_aproveitamento(df_filtrado)
    st.metric(t("metrica_aproveitamento", lang), f"{aproveitamento_geral:.1f}%")

    fig_resultados = px.pie(
        values=resumo.values,
        names=resumo.index,
        title=t("dist_resultados", lang),
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
    st.subheader(t("casa_fora_titulo", lang))

    df_casa = df_filtrado[df_filtrado["local"] == LOCAL_CASA]
    df_fora = df_filtrado[df_filtrado["local"] == LOCAL_FORA]

    aprov_casa = calcular_aproveitamento(df_casa)
    aprov_fora = calcular_aproveitamento(df_fora)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {t('em_casa', lang)}")
        st.metric(t("aproveitamento", lang), f"{aprov_casa:.1f}%")
        st.metric(t("vitorias", lang), (df_casa["resultado"] == RESULTADO_VITORIA).sum())
        st.metric(t("empates", lang), (df_casa["resultado"] == RESULTADO_EMPATE).sum())
        st.metric(t("derrotas", lang), (df_casa["resultado"] == RESULTADO_DERROTA).sum())

    with col2:
        st.markdown(f"### {t('fora', lang)}")
        st.metric(t("aproveitamento", lang), f"{aprov_fora:.1f}%")
        st.metric(t("vitorias", lang), (df_fora["resultado"] == RESULTADO_VITORIA).sum())
        st.metric(t("empates", lang), (df_fora["resultado"] == RESULTADO_EMPATE).sum())
        st.metric(t("derrotas", lang), (df_fora["resultado"] == RESULTADO_DERROTA).sum())

    st.divider()

    # Médias
    st.subheader(t("medias_titulo", lang))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(t("gols_jogo", lang), f"{df_filtrado['gols_usuario'].mean():.2f}")
    col2.metric(t("xg_jogo", lang), f"{df_filtrado['xg_usuario'].mean():.2f}")
    col3.metric(t("remates_jogo", lang), f"{df_filtrado['remates_usuario'].mean():.1f}")
    col4.metric(t("remates_alvo_jogo", lang), f"{df_filtrado['remates_a_baliza_usuario'].mean():.1f}")
    col5.metric(t("opor_flagrantes_jogo", lang), f"{df_filtrado['oportunidades_flagrantes_usuario'].mean():.2f}")

    perc_passes = calcular_percentual_passes(
        df_filtrado['passes_certos_usuario'].sum(),
        df_filtrado['passes_totais_usuario'].sum()
    )
    perc_finalizacao = calcular_percentual_finalizacao(
        df_filtrado['remates_a_baliza_usuario'].sum(),
        df_filtrado['remates_usuario'].sum()
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(t("posse_media", lang), f"{df_filtrado['posse_usuario'].mean():.1f}%")
    col2.metric(t("acerto_passes", lang), f"{perc_passes:.1f}%")
    col3.metric(t("remates_alvo_perc", lang), f"{perc_finalizacao:.1f}%")

    st.divider()

    # Comparação com Europa
    st.subheader(t("padrao_europeu", lang))

    metricas = {
        "xg_usuario": (t("xg_por_jogo", lang), df_filtrado["xg_usuario"].mean(), "maior"),
        "gols_usuario": (t("gols_por_jogo", lang), df_filtrado["gols_usuario"].mean(), "maior"),
        "remates_usuario": (t("remates_por_jogo", lang), df_filtrado["remates_usuario"].mean(), "maior"),
        "remates_a_baliza_usuario": (t("remates_alvo_label", lang), df_filtrado["remates_a_baliza_usuario"].mean(), "maior"),
        "posse_usuario": (t("posse_media_label", lang), df_filtrado["posse_usuario"].mean(), "maior"),
        "passes_certos_usuario": (t("passes_certos_label", lang), df_filtrado["passes_certos_usuario"].mean(), "maior"),
        "aproveitamento": (t("aproveitamento_label", lang), aproveitamento_geral, "maior"),
    }

    for chave, (label, meu_valor, regra) in metricas.items():
        benchmark_info = BENCHMARK[chave]
        emoji, status, cor, intervalo = comparar_com_benchmark(meu_valor, benchmark_info, regra)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"{emoji} **{label}**: {meu_valor:.2f} | {t('referencia', lang)}: {intervalo}")
        with col2:
            st.markdown(f":{cor}[{status}]")

    score = calcular_score_benchmark(df_filtrado, aproveitamento_geral)
    tipo_msg, msg = diagnostico_geral(score)

    st.divider()

    if tipo_msg == "success":
        st.success(f"🎯 {msg}")
    elif tipo_msg == "warning":
        st.warning(f"⚠️ {msg}")
    else:
        st.error(f"📉 {msg}")

    # Últimos 5 jogos — seu time x adversários
    st.divider()
    st.subheader(t("ultimos_5", lang))

    ultimos_5 = df_filtrado.tail(5)
    aprov_ultimos_5 = calcular_aproveitamento(ultimos_5)

    col1, col2, col3, col4, col10, col5, col6, col7, col8, col9 = st.columns(10)
    col1.metric(t("aproveitamento", lang), f"{aprov_ultimos_5:.1f}%")
    col2.metric(t("xg_medio", lang), f"{ultimos_5['xg_usuario'].mean():.2f}")
    col3.metric(t("gols_jogo", lang), f"{ultimos_5['gols_usuario'].mean():.2f}")
    col4.metric(t("remates_jogo", lang), f"{ultimos_5['remates_usuario'].mean():.1f}")
    col10.metric(t("opor_flagrantes_jogo", lang), f"{ultimos_5['oportunidades_flagrantes_usuario'].mean():.1f}")
    col5.metric(t("posse_media", lang), f"{ultimos_5['posse_usuario'].mean():.1f}%")
    col6.metric(t("cruzamentos_totais_jogo", lang), f"{ultimos_5['cruzamentos_totais_usuario'].mean():.1f}")
    col7.metric(t("cruzamentos_certos_jogo", lang), f"{ultimos_5['cruzamentos_certos_usuario'].mean():.1f}")
    col8.metric(t("cantos_jogo", lang), f"{ultimos_5['cantos_usuario'].mean():.1f}")
    col9.metric(t("aprov_passes", lang), f"{calcular_percentual_passes(ultimos_5['passes_certos_usuario'].sum(), ultimos_5['passes_totais_usuario'].sum()):.1f}%")

    col1, col2, col3, col4, col10, col5, col6, col7, col8, col9 = st.columns(10)
    col2.metric(t("xg_medio", lang), f"{ultimos_5['xg_adv'].mean():.2f}")
    col3.metric(t("gols_jogo", lang), f"{ultimos_5['gols_adv'].mean():.2f}")
    col4.metric(t("remates_jogo", lang), f"{ultimos_5['remates_adv'].mean():.1f}")
    col10.metric(t("opor_flagrantes_jogo", lang), f"{ultimos_5['oportunidades_flagrantes_adv'].mean():.1f}")
    col5.metric(t("posse_media", lang), f"{ultimos_5['posse_adv'].mean():.1f}%")
    col6.metric(t("cruzamentos_totais_jogo", lang), f"{ultimos_5['cruzamentos_totais_adv'].mean():.1f}")
    col7.metric(t("cruzamentos_certos_jogo", lang), f"{ultimos_5['cruzamentos_certos_adv'].mean():.1f}")
    col8.metric(t("cantos_jogo", lang), f"{ultimos_5['cantos_adv'].mean():.1f}")
    col9.metric(t("aprov_passes", lang), f"{calcular_percentual_passes(ultimos_5['passes_certos_adv'].sum(), ultimos_5['passes_totais_adv'].sum()):.1f}%")

    st.divider()
    st.subheader(t("ultimos_5_casa_fora", lang))

    ultimos_5_casa = (
        df_filtrado[df_filtrado["local"] == LOCAL_CASA]
        .sort_values("data")
        .tail(5)
    )
    ultimos_5_fora = (
        df_filtrado[df_filtrado["local"] == LOCAL_FORA]
        .sort_values("data")
        .tail(5)
    )

    aprov_5_casa = calcular_aproveitamento(ultimos_5_casa)
    aprov_5_fora = calcular_aproveitamento(ultimos_5_fora)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {t('ultimos_5_casa', lang)}")
        if len(ultimos_5_casa) == 0:
            st.info(t("nenhum_jogo_casa", lang))
        else:
            st.metric(t("aproveitamento", lang), f"{aprov_5_casa:.1f}%")
            st.metric(t("xg_medio", lang), f"{ultimos_5_casa['xg_usuario'].mean():.2f}")
            st.metric(t("gols_jogo", lang), f"{ultimos_5_casa['gols_usuario'].mean():.2f}")
            st.metric(t("remates_jogo", lang), f"{ultimos_5_casa['remates_usuario'].mean():.1f}")
            st.metric(t("opor_flagrantes_jogo", lang), f"{ultimos_5_casa['oportunidades_flagrantes_usuario'].mean():.1f}")
            st.metric(t("cruzamentos_totais_jogo", lang), f"{ultimos_5_casa['cruzamentos_totais_usuario'].mean():.1f}")
            st.metric(t("cruzamentos_certos_jogo", lang), f"{ultimos_5_casa['cruzamentos_certos_usuario'].mean():.1f}")
            st.metric(t("cantos_jogo", lang), f"{ultimos_5_casa['cantos_usuario'].mean():.1f}")
            st.metric(t("posse_media", lang), f"{ultimos_5_casa['posse_usuario'].mean():.1f}%")

    with col2:
        st.markdown(f"### {t('ultimos_5_fora', lang)}")
        if len(ultimos_5_fora) == 0:
            st.info(t("nenhum_jogo_fora", lang))
        else:
            st.metric(t("aproveitamento", lang), f"{aprov_5_fora:.1f}%")
            st.metric(t("xg_medio", lang), f"{ultimos_5_fora['xg_usuario'].mean():.2f}")
            st.metric(t("gols_jogo", lang), f"{ultimos_5_fora['gols_usuario'].mean():.2f}")
            st.metric(t("remates_jogo", lang), f"{ultimos_5_fora['remates_usuario'].mean():.1f}")
            st.metric(t("opor_flagrantes_jogo", lang), f"{ultimos_5_fora['oportunidades_flagrantes_usuario'].mean():.1f}")
            st.metric(t("cruzamentos_totais_jogo", lang), f"{ultimos_5_fora['cruzamentos_totais_usuario'].mean():.1f}")
            st.metric(t("cruzamentos_certos_jogo", lang), f"{ultimos_5_fora['cruzamentos_certos_usuario'].mean():.1f}")
            st.metric(t("cantos_jogo", lang), f"{ultimos_5_fora['cantos_usuario'].mean():.1f}")
            st.metric(t("posse_media", lang), f"{ultimos_5_fora['posse_usuario'].mean():.1f}%")

    # Resultados casa/fora
    v_casa = (ultimos_5_casa["resultado"] == RESULTADO_VITORIA).sum()
    e_casa = (ultimos_5_casa["resultado"] == RESULTADO_EMPATE).sum()
    d_casa = (ultimos_5_casa["resultado"] == RESULTADO_DERROTA).sum()
    v_fora = (ultimos_5_fora["resultado"] == RESULTADO_VITORIA).sum()
    e_fora = (ultimos_5_fora["resultado"] == RESULTADO_EMPATE).sum()
    d_fora = (ultimos_5_fora["resultado"] == RESULTADO_DERROTA).sum()

    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"### {t('ultimos_5_casa_label', lang)}")
        st.metric(t("vitorias", lang), v_casa)
        st.metric(t("empates", lang), e_casa)
        st.metric(t("derrotas", lang), d_casa)

    with col2:
        st.markdown(f"### {t('ultimos_5_fora_label', lang)}")
        st.metric(t("vitorias", lang), v_fora)
        st.metric(t("empates", lang), e_fora)
        st.metric(t("derrotas", lang), d_fora)

    with col3:
        st.markdown(f"### {t('grafico_resultados', lang)}")
        fig_casa_fora = go.Figure(data=[
            go.Bar(name=t("ultimos_5_casa_label", lang),
                   x=[t("vitorias", lang), t("empates", lang), t("derrotas", lang)],
                   y=[v_casa, e_casa, d_casa], marker_color='indianred'),
            go.Bar(name=t("ultimos_5_fora_label", lang),
                   x=[t("vitorias", lang), t("empates", lang), t("derrotas", lang)],
                   y=[v_fora, e_fora, d_fora], marker_color='lightsalmon')
        ])
        fig_casa_fora.update_layout(barmode='group', title_text=t("resultados_casa_fora", lang))
        st.plotly_chart(fig_casa_fora, use_container_width=True)


# =======================
# TAB 3: HISTÓRICO
# =======================
with tab3:
    st.subheader(t("historico_titulo", lang))

    if not partidas:
        st.info(t("nenhuma_partida_hist", lang))
        st.stop()

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

    st.divider()
    st.subheader(t("gerenciar_titulo", lang))

    partida_deletar = st.selectbox(
        t("selecionar_deletar", lang),
        options=df["id"].tolist(),
        format_func=lambda x: f"{df[df['id']==x]['data'].iloc[0].strftime('%d/%m/%Y')} - {df[df['id']==x]['time_usuario'].iloc[0]} {df[df['id']==x]['gols_usuario'].iloc[0]}x{df[df['id']==x]['gols_adv'].iloc[0]} {df[df['id']==x]['time_adv'].iloc[0]}"
    )

    if st.button(t("btn_deletar", lang), type="secondary"):
        if deletar_partida(partida_deletar):
            st.success(t("deletar_sucesso", lang))
            st.rerun()
        else:
            st.error(t("deletar_erro", lang))


# =======================
# TAB 4: ASSISTENTE IA
# =======================
with tab4:
    st.subheader(t("ia_titulo", lang))
    st.caption(t("ia_descricao", lang))

    partidas_ia = buscar_partidas(st.session_state.usuario_id)

    if not partidas_ia:
        st.warning(t("ia_sem_partidas", lang))
        st.stop()

    colunas_ia = [
        "id", "usuario_id", "time_usuario", "time_adv", "local", "competicao", "temporada", "data", "rodada",
        "posse_usuario", "remates_usuario", "remates_a_baliza_usuario", "xg_usuario",
        "oportunidades_flagrantes_usuario", "cantos_usuario", "passes_totais_usuario",
        "passes_certos_usuario", "cruzamentos_totais_usuario", "cruzamentos_certos_usuario",
        "gols_usuario", "posse_adv", "remates_adv", "remates_a_baliza_adv", "xg_adv",
        "oportunidades_flagrantes_adv", "cantos_adv", "passes_totais_adv",
        "passes_certos_adv", "cruzamentos_totais_adv", "cruzamentos_certos_adv",
        "gols_adv", "resultado"
    ]
    df_ia = pd.DataFrame(partidas_ia, columns=colunas_ia)
    df_ia["data"] = pd.to_datetime(df_ia["data"])
    df_ia = df_ia.sort_values("data")

    n_total = len(df_ia)
    if n_total < 3:
        st.info(t("ia_minimo", lang).format(n=n_total))

    # Escopo
    escopo_opcoes = {
        t("ia_escopo_todas", lang): None,
        t("ia_escopo_10", lang): 10,
        t("ia_escopo_5", lang): 5,
    }
    escopo_label = st.selectbox(t("ia_selecionar", lang), list(escopo_opcoes.keys()))
    escopo_n = escopo_opcoes[escopo_label]

    if escopo_n:
        df_analise = df_ia.tail(escopo_n)
    else:
        df_analise = df_ia.copy()

    n_analise = len(df_analise)
    st.info(t("ia_partidas_usadas", lang).format(n=n_analise))

    if st.button(t("ia_analisar", lang), type="primary", use_container_width=True):
        with st.spinner(t("ia_gerando", lang)):

            # Calcular métricas para o prompt
            aprov = calcular_aproveitamento(df_analise)
            resumo_res = df_analise["resultado"].value_counts()
            v = resumo_res.get(RESULTADO_VITORIA, 0)
            e = resumo_res.get(RESULTADO_EMPATE, 0)
            d = resumo_res.get(RESULTADO_DERROTA, 0)

            media_xg = df_analise["xg_usuario"].mean()
            media_gols = df_analise["gols_usuario"].mean()
            media_remates = df_analise["remates_usuario"].mean()
            media_remates_alvo = df_analise["remates_a_baliza_usuario"].mean()
            media_posse = df_analise["posse_usuario"].mean()
            media_opor = df_analise["oportunidades_flagrantes_usuario"].mean()
            media_cruzamentos_totais = df_analise["cruzamentos_totais_usuario"].mean()
            media_cruzamentos_certos = df_analise["cruzamentos_certos_usuario"].mean()
            media_cantos = df_analise["cantos_usuario"].mean()

            perc_passes_ia = calcular_percentual_passes(
                df_analise["passes_certos_usuario"].sum(),
                df_analise["passes_totais_usuario"].sum()
            )
            perc_fin_ia = calcular_percentual_finalizacao(
                df_analise["remates_a_baliza_usuario"].sum(),
                df_analise["remates_usuario"].sum()
            )

            # Médias do adversário
            media_xg_adv = df_analise["xg_adv"].mean()
            media_gols_adv = df_analise["gols_adv"].mean()
            media_remates_adv = df_analise["remates_adv"].mean()

            nome_time = df_analise["time_usuario"].iloc[-1] if n_analise > 0 else "O time"

            # Mapa de idioma para o prompt
            idioma_prompt_map = {
                "pt-br": "português do Brasil",
                "pt-pt": "português de Portugal",
                "en": "English",
                "es": "español",
            }
            idioma_prompt = idioma_prompt_map.get(lang, "português do Brasil")

            system_prompt = f"""Você é um Engenheiro de Dados e Analista de Desempenho (Performance Analyst) especializado em Football Manager. Sua função é atuar como o braço direito do treinador, interpretando dados estatísticos de partidas.

SUAS DIRETRIZES DE ANÁLISE:
1. Eficiência Ofensiva (xG vs Gols): Se o xG for alto e os gols baixos, identifique desperdício técnico. Se o xG for baixo e os gols altos, identifique sorte ou talento individual acima da média.
2. Qualidade da Posse: Avalie se a posse de bola é progressiva ou "posse inútil" (muitos passes, mas poucos remates a baliza).
3. Padrões de Benchmark Europeu:
   - xG ideal: > 1.23 por jogo
   - Acerto de passes ideal: > 80%
   - Conversão de remates (Remates no alvo/Totais): > 35%

ESTRUTURA DO RELATÓRIO — responda SEMPRE neste formato exato:
#### 📋 Veredito Tático
[Resumo de 2 frases sobre o momento atual do time]

#### 🔍 Gargalos Identificados
- **Problema:** [Ex: Baixa conversão de cruzamentos]
- **Evidência:** [Ex: {media_cruzamentos_totais:.1f} cruzamentos/jogo, apenas {media_cruzamentos_certos:.1f} certos]

#### 💡 Sugestão do Auxiliar
[Instrução específica para o painel de táticas do FM]

#### 🎯 Próximo Passo
[Uma meta clara e mensurável para a próxima partida]

RESTRITO: Não invente dados. Use apenas os dados fornecidos. Se os dados forem insuficientes, diga claramente.
Responda SEMPRE em {idioma_prompt}."""

            user_msg = f"""Analise o desempenho do time "{nome_time}" com base nas seguintes estatísticas médias de {n_analise} partida(s):

RESULTADOS:
- Aproveitamento: {aprov:.1f}%
- Vitórias: {v} | Empates: {e} | Derrotas: {d}

OFENSIVO (médias por jogo):
- xG: {media_xg:.2f} (benchmark europeu: >1.23)
- Gols: {media_gols:.2f}
- Remates: {media_remates:.1f}
- Remates a baliza: {media_remates_alvo:.1f}
- Conversão de remates: {perc_fin_ia:.1f}% (benchmark: >35%)
- Oportunidades flagrantes: {media_opor:.2f}

CONSTRUÇÃO DE JOGO:
- Posse de bola: {media_posse:.1f}%
- Acerto de passes: {perc_passes_ia:.1f}% (benchmark: >80%)
- Cruzamentos totais: {media_cruzamentos_totais:.1f} | Cruzamentos certos: {media_cruzamentos_certos:.1f}
- Cantos: {media_cantos:.1f}

ADVERSÁRIOS (médias por jogo):
- xG adversário: {media_xg_adv:.2f}
- Gols sofridos: {media_gols_adv:.2f}
- Remates adversário: {media_remates_adv:.1f}

Gere o relatório completo seguindo a estrutura definida."""

            try:
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1000,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_msg}]
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    analise_texto = data["content"][0]["text"]
                    st.divider()
                    st.subheader(t("ia_veredito", lang))
                    st.markdown(analise_texto)
                else:
                    st.error(t("ia_erro", lang))

            except Exception as e:
                st.error(t("ia_erro", lang))


# =======================
# FOOTER
# =======================
st.divider()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.caption(t("footer_email", lang))
with col2:
    st.caption(t("footer_seguro", lang))
with col3:
    st.link_button(t("footer_canal", lang), "https://www.youtube.com/@OnzeVirtual-FC")
with col4:
    st.caption(t("footer_versao", lang))
