import sqlite3

DB_NAME = "fm_analytics.db"

# =======================
# CONEXÃO
# =======================
def conectar():
    """Estabelece conexão com o banco de dados."""
    return sqlite3.connect(DB_NAME)


# =======================
# CRIAÇÃO DA TABELA
# =======================
def criar_tabela():
    """Cria a tabela de partidas se ela não existir."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            time_usuario TEXT NOT NULL,
            time_adv TEXT NOT NULL,
            local TEXT NOT NULL,
            competicao TEXT,
            temporada TEXT,
            data TEXT NOT NULL,
            rodada INTEGER,

            posse_usuario INTEGER,
            remates_usuario INTEGER,
            remates_a_baliza_usuario INTEGER,
            xg_usuario REAL,
            oportunidades_flagrantes_usuario INTEGER,       
            cantos_usuario INTEGER,
            passes_totais_usuario INTEGER,       
            passes_certos_usuario INTEGER,
            cruzamentos_totais_usuario INTEGER,
            cruzamentos_certos_usuario INTEGER,
            gols_usuario INTEGER,      
                   
            posse_adv INTEGER,
            remates_adv INTEGER,
            remates_a_baliza_adv INTEGER,
            xg_adv REAL,
            oportunidades_flagrantes_adv INTEGER,       
            cantos_adv INTEGER,
            passes_totais_adv INTEGER,       
            passes_certos_adv INTEGER,
            cruzamentos_totais_adv INTEGER,
            cruzamentos_certos_adv INTEGER,
            gols_adv INTEGER,       

            resultado TEXT NOT NULL,
            
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    # Criar índices para melhorar performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_data ON partidas(data)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_temporada ON partidas(temporada)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_competicao ON partidas(competicao)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_usuario ON partidas(usuario_id)
    """)

    conn.commit()
    conn.close()


# =======================
# INSERÇÃO - CORRIGIDO
# =======================
def inserir_partida(dados):
    """Insere uma nova partida no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()

    try:
        # CORRIGIDO: Agora inclui usuario_id
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    """Retorna todas as partidas cadastradas."""
    conn = conectar()
    cursor = conn.cursor()

    try:
        if usuario_id:
            cursor.execute("""
                SELECT * FROM partidas WHERE usuario_id = ? ORDER BY data DESC
            """, (usuario_id,))
        else:
            cursor.execute("""
                SELECT * FROM partidas ORDER BY data DESC
            """)
        partidas = cursor.fetchall()
        return partidas
    except Exception as e:
        print(f"Erro ao buscar partidas: {e}")
        return []
    finally:
        conn.close()


# =======================
# DELETAR PARTIDA
# =======================
def deletar_partida(id_partida, usuario_id=None):
    """Deleta uma partida pelo ID (com verificação de usuário)."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        if usuario_id:
            # Segurança: só deleta se for do usuário
            cursor.execute("DELETE FROM partidas WHERE id = ? AND usuario_id = ?", (id_partida, usuario_id))
        else:
            cursor.execute("DELETE FROM partidas WHERE id = ?", (id_partida,))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Erro ao deletar partida: {e}")
        return False
    finally:
        conn.close()


# =======================
# BUSCAR POR FILTROS
# =======================
def buscar_partidas_filtradas(usuario_id, temporada=None, competicao=None):
    """Retorna partidas filtradas por usuário, temporada e/ou competição."""
    conn = conectar()
    cursor = conn.cursor()
    
    query = "SELECT * FROM partidas WHERE usuario_id = ?"
    params = [usuario_id]
    
    if temporada:
        query += " AND temporada = ?"
        params.append(temporada)
    
    if competicao:
        query += " AND competicao = ?"
        params.append(competicao)
    
    query += " ORDER BY data DESC"
    
    try:
        cursor.execute(query, params)
        partidas = cursor.fetchall()
        return partidas
    except Exception as e:
        print(f"Erro ao buscar partidas filtradas: {e}")
        return []
    finally:
        conn.close()


# =======================
# ESTATÍSTICAS DO USUÁRIO
# =======================
def contar_partidas_usuario(usuario_id):
    """Conta quantas partidas o usuário tem cadastradas."""
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM partidas WHERE usuario_id = ?", (usuario_id,))
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"Erro ao contar partidas: {e}")
        return 0
    finally:
        conn.close()