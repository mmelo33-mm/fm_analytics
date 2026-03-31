import psycopg2
import streamlit as st

# =======================
# CONEXÃO
# =======================
def conectar():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=5432
    )

# =======================
# INSERÇÃO
# =======================
def inserir_partida(dados):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO partidas (
                usuario_id,
                time_usuario, time_adv, local, competicao, temporada, data, rodada,
                posse_usuario, remates_usuario, remates_a_baliza_usuario, xg_usuario,
                oportunidades_flagrantes_usuario, cantos_usuario, passes_totais_usuario,
                passes_certos_usuario, cruzamentos_totais_usuario, cruzamentos_certos_usuario,
                gols_usuario, posse_adv, remates_adv, remates_a_baliza_adv, xg_adv,
                oportunidades_flagrantes_adv, cantos_adv, passes_totais_adv,
                passes_certos_adv, cruzamentos_totais_adv, cruzamentos_certos_adv,
                gols_adv, resultado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, dados)

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir partida: {e}")
        return False

    finally:
        conn.close()
        
# =======================
# CONSULTA
# =======================
def buscar_partidas(usuario_id=None):
    conn = conectar()
    cursor = conn.cursor()

    try:
        if usuario_id:
            cursor.execute("""
                SELECT * FROM partidas
                WHERE usuario_id = %s
                ORDER BY data DESC
            """, (usuario_id,))
        else:
            cursor.execute("""
                SELECT * FROM partidas
                ORDER BY data DESC
            """)

        return cursor.fetchall()

    except Exception as e:
        print(f"Erro ao buscar partidas: {e}")
        return []

    finally:
        conn.close()

# =======================
# DELETAR
# =======================
def deletar_partida(id_partida, usuario_id=None):
    conn = conectar()
    cursor = conn.cursor()

    try:
        if usuario_id:
            cursor.execute("""
                DELETE FROM partidas
                WHERE id = %s AND usuario_id = %s
            """, (id_partida, usuario_id))
        else:
            cursor.execute("""
                DELETE FROM partidas
                WHERE id = %s
            """, (id_partida,))

        conn.commit()
        return cursor.rowcount > 0

    except Exception as e:
        conn.rollback()
        print(f"Erro ao deletar partida: {e}")
        return False

    finally:
        conn.close()

# =======================
# FILTROS
# =======================
def buscar_partidas_filtradas(usuario_id, temporada=None, competicao=None):
    conn = conectar()
    cursor = conn.cursor()

    query = "SELECT * FROM partidas WHERE usuario_id = %s"
    params = [usuario_id]

    if temporada:
        query += " AND temporada = %s"
        params.append(temporada)

    if competicao:
        query += " AND competicao = %s"
        params.append(competicao)

    query += " ORDER BY data DESC"

    try:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

    except Exception as e:
        print(f"Erro ao buscar partidas filtradas: {e}")
        return []

    finally:
        conn.close()

# =======================
# CONTAGEM
# =======================
def contar_partidas_usuario(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM partidas
            WHERE usuario_id = %s
        """, (usuario_id,))

        return cursor.fetchone()[0]

    except Exception as e:
        print(f"Erro ao contar partidas: {e}")
        return 0

    finally:
        conn.close()