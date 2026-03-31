import psycopg2
import streamlit as st

# =======================
# CONEXÃO
# =======================
import psycopg2
import streamlit as st

def conectar():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=int(st.secrets["DB_PORT"]),
        sslmode="require"  # 🔥 obrigatório no Supabase
    )

# =======================
# CRIAR USUÁRIO
# =======================
def criar_usuario(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (email, senha)
            VALUES (%s, %s)
            RETURNING id
        """, (email, senha))

        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id

    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar usuário: {e}")
        return None

    finally:
        conn.close()

# =======================
# BUSCAR USUÁRIO POR EMAIL
# =======================
def buscar_usuario_por_email(email):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM usuarios WHERE email = %s
        """, (email,))

        return cursor.fetchone()

    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None

    finally:
        conn.close()

# =======================
# BUSCAR USUÁRIO POR ID
# =======================
def buscar_usuario(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM usuarios WHERE id = %s
        """, (usuario_id,))

        user = cursor.fetchone()

        if user:
            return {
                "id": user[0],
                "email": user[1],
                "senha": user[2],
                "plano": user[3],
                "data_expiracao": user[4]
            }

        return None

    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None

    finally:
        conn.close()

# =======================
# LOGIN
# =======================
def autenticar_usuario(email, senha):
    usuario = buscar_usuario_por_email(email)

    if usuario and usuario[2] == senha:
        return usuario[0]  # retorna ID do usuário

    return None