"""
Funções auxiliares para cálculos e análises do FM Analytics
VERSÃO CORRIGIDA - Aceita usuario_id
"""

import pandas as pd

# =======================
# CONSTANTES
# =======================
RESULTADO_VITORIA = "Vitória"
RESULTADO_EMPATE = "Empate"
RESULTADO_DERROTA = "Derrota"

LOCAL_CASA = "Casa"
LOCAL_FORA = "Fora"


# =======================
# BENCHMARK – GRANDES LIGAS EUROPEIAS
# =======================
BENCHMARK = {
    "xg_usuario": {"min": 0.80, "max": 2.20, "ideal": 1.23},
    "gols_usuario": {"min": 0.80, "max": 2.35, "ideal": 1.40},
    "remates_usuario": {"min": 8.0, "max": 17.50, "ideal": 13.0},
    "remates_a_baliza_usuario": {"min": 3.0, "max": 6.50, "ideal": 4.8},
    "posse_usuario": {"min": 35.0, "max": 58.0, "ideal": 54.0},
    "passes_certos_usuario": {"min": 300, "max": 570, "ideal": 430},
    "aproveitamento": {"min": 20.0, "max": 60.0, "ideal": 55.0}
}


# =======================
# CÁLCULOS
# =======================
def calcular_aproveitamento(df):
    """
    Calcula o aproveitamento percentual de pontos.
    
    Args:
        df: DataFrame com coluna 'resultado'
    
    Returns:
        float: Percentual de aproveitamento (0-100)
    """
    if len(df) == 0:
        return 0.0
    
    pontos = (
        (df["resultado"] == RESULTADO_VITORIA).sum() * 3 +
        (df["resultado"] == RESULTADO_EMPATE).sum() * 1
    )
    pontos_possiveis = len(df) * 3
    
    return (pontos / pontos_possiveis) * 100 if pontos_possiveis > 0 else 0.0


def calcular_percentual_passes(passes_certos, passes_totais):
    """Calcula percentual de acerto de passes."""
    if passes_totais == 0:
        return 0.0
    return (passes_certos / passes_totais) * 100


def calcular_percentual_cruzamentos(cruzamentos_certos, cruzamentos_totais):
    """Calcula percentual de acerto de cruzamentos."""
    if cruzamentos_totais == 0:
        return 0.0
    return (cruzamentos_certos / cruzamentos_totais) * 100


def calcular_percentual_finalizacao(remates_baliza, remates_totais):
    """Calcula percentual de remates no alvo."""
    if remates_totais == 0:
        return 0.0
    return (remates_baliza / remates_totais) * 100


def calcular_eficiencia_gols(gols, xg):
    """Calcula eficiência de finalização (gols / xG)."""
    if xg == 0:
        return 0.0
    return (gols / xg) * 100


# =======================
# COMPARAÇÃO COM BENCHMARK
# =======================
def comparar_com_benchmark(meu_valor, benchmark_info, melhor="maior"):
    """
    Compara valor do usuário com benchmark europeu (intervalos).
    
    Args:
        meu_valor: Valor do usuário
        benchmark_info: Dict com 'min', 'max' e 'ideal'
        melhor: "maior" ou "menor" indica qual direção é melhor
    
    Returns:
        tuple: (status_emoji, status_texto, cor, intervalo_str)
    """
    if pd.isna(meu_valor):
        return "⚪", "Sem dados suficientes", "gray", ""

    min_val = benchmark_info["min"]
    max_val = benchmark_info["max"]
    intervalo_str = f"{min_val:.2f} - {max_val:.2f}"

    if melhor == "maior":
        if meu_valor > max_val:
            return "🟢", "Acima do padrão europeu", "green", intervalo_str
        elif meu_valor >= min_val:
            return "🟡", "Dentro do padrão europeu", "orange", intervalo_str
        else:
            return "🔴", "Abaixo do padrão europeu", "red", intervalo_str
    else:
        if meu_valor < min_val:
            return "🟢", "Acima do padrão defensivo", "green", intervalo_str
        elif meu_valor <= max_val:
            return "🟡", "Dentro do padrão defensivo", "orange", intervalo_str
        else:
            return "🔴", "Abaixo do padrão defensivo", "red", intervalo_str



def calcular_score_benchmark(df, aproveitamento_geral):
    """
    Calcula score geral comparando com benchmark por intervalos.
    
    Returns:
        int: Score de -7 a 7
    """
    metricas = {
        "xg_usuario": df["xg_usuario"].mean(),
        "gols_usuario": df["gols_usuario"].mean(),
        "remates_usuario": df["remates_usuario"].mean(),
        "remates_a_baliza_usuario": df["remates_a_baliza_usuario"].mean(),
        "posse_usuario": df["posse_usuario"].mean(),
        "passes_certos_usuario": df["passes_certos_usuario"].mean(),
        "aproveitamento": aproveitamento_geral,
    }

    score = 0

    for chave, meu_valor in metricas.items():
        if pd.isna(meu_valor):
            continue

        benchmark = BENCHMARK[chave]
        min_val = benchmark["min"]
        max_val = benchmark["max"]

        if meu_valor > max_val:
            score += 1          # acima do padrão
        elif meu_valor < min_val:
            score -= 1          # abaixo do padrão
        else:
            score += 0          # dentro do padrão

    return score


def diagnostico_geral(score):
    """
    Retorna diagnóstico baseado no score.
    
    Returns:
        tuple: (tipo, mensagem) - tipo pode ser "success", "warning", "error"
    """
    if score >= 3:
        return "success", "O time apresenta desempenho competitivo em nível europeu."
    elif score >= -2:
        return "warning", "O time está dentro do padrão europeu, mas com margens claras de evolução."
    else:
        return "error", "O time apresenta desempenho abaixo do padrão das principais ligas europeias."


# =======================
# VALIDAÇÕES - CORRIGIDO
# =======================

def validar_dados_partida(dados):
    """
    Valida os dados de uma partida antes de salvar.
    CORRIGIDO: Agora aceita usuario_id como primeiro parâmetro
    
    Args:
        dados: tupla com (usuario_id, time_usuario, time_adv, ..., resultado)
    
    Returns:
        tuple: (bool, str) - (válido, mensagem_erro)
    """
    # Desempacota os dados (agora com usuario_id)
    try:
        (usuario_id, time_usuario, time_adv, local, competicao, temporada, data, rodada,
         posse_usuario, remates_usuario, remates_a_baliza_usuario, xg_usuario, 
         oportunidades_flagrantes_usuario, cantos_usuario,
         passes_totais_usuario, passes_certos_usuario, cruzamentos_totais_usuario,
         cruzamentos_certos_usuario, gols_usuario,
         posse_adv, remates_adv, remates_a_baliza_adv, xg_adv,
         oportunidades_flagrantes_adv, cantos_adv,
         passes_totais_adv, passes_certos_adv, cruzamentos_totais_adv,
         cruzamentos_certos_adv, gols_adv, resultado) = dados
    except ValueError as e:
        return False, f"❌ Erro na estrutura dos dados: {e}"
    
    # Validar campos obrigatórios
    if not time_usuario or not time_adv:
        return False, "❌ Nome dos times é obrigatório."
    
    # Validar passes
    if passes_certos_usuario > passes_totais_usuario:
        return False, "❌ Passes certos não podem ser maiores que passes totais."
    
    if passes_certos_adv > passes_totais_adv:
        return False, "❌ Passes certos do adversário não podem ser maiores que passes totais."
    
    # Validar remates
    if remates_a_baliza_usuario > remates_usuario:
        return False, "❌ Remates a baliza não podem ser maiores que remates totais."
    
    if remates_a_baliza_adv > remates_adv:
        return False, "❌ Remates a baliza do adversário não podem ser maiores que remates totais."
    
    # Validar cruzamentos
    if cruzamentos_certos_usuario > cruzamentos_totais_usuario:
        return False, "❌ Cruzamentos certos não podem ser maiores que cruzamentos totais."
    
    if cruzamentos_certos_adv > cruzamentos_totais_adv:
        return False, "❌ Cruzamentos certos do adversário não podem ser maiores que cruzamentos totais."
    
    # Validar gols vs remates
    if gols_usuario > remates_a_baliza_usuario:
        return False, "❌ Gols não podem ser maiores que remates a baliza."
    
    if gols_adv > remates_a_baliza_adv:
        return False, "❌ Gols do adversário não podem ser maiores que remates a baliza."
    
    # Avisar sobre posse (não bloqueia)
    if abs((posse_usuario + posse_adv) - 100) > 5:
        return True, "⚠️ Aviso: A soma das posses de bola não está próxima de 100%."
    
    return True, ""