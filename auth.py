"""
Sistema de Autenticação Simplificado - FM Analytics
Versão Manual (Você ativa os planos)
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta

DB_NAME = "fm_analytics.db"

# =======================
# FUNÇÕES BÁSICAS
# =======================

def hash_senha(senha):
    """Cria hash da senha"""
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_tabela_usuarios():
    """Cria tabela de usuários se não existir"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT,
            plano TEXT DEFAULT 'FREE',
            data_expiracao TEXT,
            data_cadastro TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_email ON usuarios(email)
    """)
    
    conn.commit()
    conn.close()
    print("✅ Tabela de usuários criada/verificada")

# =======================
# CADASTRO E LOGIN
# =======================

def cadastrar_usuario(email, senha, nome=""):
    """Cadastra novo usuário (sempre começa FREE)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Verificar se email já existe
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        if cursor.fetchone():
            return False, "Email já cadastrado"
        
        # Criar usuário
        senha_hash = hash_senha(senha)
        data_cadastro = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO usuarios (email, senha_hash, nome, data_cadastro, plano)
            VALUES (?, ?, ?, ?, 'FREE')
        """, (email, senha_hash, nome, data_cadastro))
        
        conn.commit()
        usuario_id = cursor.lastrowid
        
        print(f"✅ Usuário cadastrado: {email} (ID: {usuario_id})")
        return True, usuario_id
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao cadastrar: {e}")
        return False, str(e)
    finally:
        conn.close()

def fazer_login(email, senha):
    """Realiza login do usuário"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        senha_hash = hash_senha(senha)
        
        cursor.execute("""
            SELECT id, email, nome, plano, data_expiracao
            FROM usuarios 
            WHERE email = ? AND senha_hash = ?
        """, (email, senha_hash))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            return False, "Email ou senha incorretos"
        
        # Verificar se plano expirou
        if usuario[4]:  # data_expiracao
            try:
                data_exp = datetime.fromisoformat(usuario[4])
                if datetime.now() > data_exp:
                    # Plano expirado, reverter para FREE
                    cursor.execute("UPDATE usuarios SET plano = 'FREE' WHERE id = ?", (usuario[0],))
                    conn.commit()
                    plano = "FREE"
                else:
                    plano = usuario[3]
            except:
                plano = usuario[3]
        else:
            plano = usuario[3]
        
        return True, {
            "id": usuario[0],
            "email": usuario[1],
            "nome": usuario[2],
            "plano": plano,
            "data_expiracao": usuario[4]
        }
        
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return False, "Erro ao fazer login"
    finally:
        conn.close()

def buscar_usuario(usuario_id):
    """Busca dados do usuário por ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, email, nome, plano, data_expiracao
            FROM usuarios WHERE id = ?
        """, (usuario_id,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            return None
        
        return {
            "id": usuario[0],
            "email": usuario[1],
            "nome": usuario[2],
            "plano": usuario[3],
            "data_expiracao": usuario[4]
        }
        
    finally:
        conn.close()

# =======================
# ATIVAÇÃO MANUAL DE PLANOS
# =======================

def atualizar_plano(usuario_id, plano, dias=30):
    """
    Atualiza plano do usuário (VOCÊ CHAMA ISSO MANUALMENTE)
    
    Exemplos:
        atualizar_plano(5, "PRO", 30)      # PRO por 1 mês
        atualizar_plano(5, "STARTER", 365) # STARTER por 1 ano
        atualizar_plano(5, "FREE", 0)      # Volta para FREE
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        if plano == "FREE":
            data_exp = None
        else:
            data_exp = (datetime.now() + timedelta(days=dias)).isoformat()
        
        cursor.execute("""
            UPDATE usuarios 
            SET plano = ?, data_expiracao = ?
            WHERE id = ?
        """, (plano, data_exp, usuario_id))
        
        conn.commit()
        
        usuario = buscar_usuario(usuario_id)
        print(f"✅ Plano atualizado!")
        print(f"   Usuário: {usuario['email']}")
        print(f"   Plano: {plano}")
        print(f"   Expira: {data_exp if data_exp else 'Nunca'}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar plano: {e}")
        return False
    finally:
        conn.close()

def listar_usuarios():
    """Lista todos os usuários (para você ver quem tem)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, nome, plano, data_expiracao, data_cadastro
        FROM usuarios
        ORDER BY id DESC
    """)
    
    usuarios = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("USUÁRIOS CADASTRADOS")
    print("="*80)
    print(f"{'ID':<5} {'EMAIL':<30} {'NOME':<20} {'PLANO':<10} {'EXPIRA':<15}")
    print("-"*80)
    
    for u in usuarios:
        expira = u[4][:10] if u[4] else "Nunca"
        print(f"{u[0]:<5} {u[1]:<30} {u[2] or '-':<20} {u[3]:<10} {expira:<15}")
    
    print("-"*80)
    print(f"Total: {len(usuarios)} usuários")
    print("="*80 + "\n")
    
    return usuarios

def buscar_por_email(email):
    """Busca usuário por email"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, nome, plano, data_expiracao
        FROM usuarios WHERE email = ?
    """, (email,))
    
    usuario = cursor.fetchone()
    conn.close()
    
    if usuario:
        print(f"\n📧 Usuário encontrado:")
        print(f"   ID: {usuario[0]}")
        print(f"   Email: {usuario[1]}")
        print(f"   Nome: {usuario[2] or 'Não informado'}")
        print(f"   Plano: {usuario[3]}")
        print(f"   Expira: {usuario[4] or 'Nunca'}\n")
        
        return {
            "id": usuario[0],
            "email": usuario[1],
            "nome": usuario[2],
            "plano": usuario[3],
            "data_expiracao": usuario[4]
        }
    else:
        print(f"\n❌ Usuário com email '{email}' não encontrado\n")
        return None

# =======================
# SCRIPT DE ATIVAÇÃO
# =======================

def ativar_cliente_interativo():
    """
    Script interativo para ativar clientes
    Execute: python -c "from auth import ativar_cliente_interativo; ativar_cliente_interativo()"
    """
    print("\n" + "="*60)
    print("ATIVAR CLIENTE - FM ANALYTICS")
    print("="*60 + "\n")
    
    # Listar usuários
    usuarios = listar_usuarios()
    
    if not usuarios:
        print("❌ Nenhum usuário cadastrado ainda\n")
        return
    
    # Pedir ID ou email
    busca = input("Digite o ID ou EMAIL do cliente: ").strip()
    
    # Buscar usuário
    if busca.isdigit():
        usuario = buscar_usuario(int(busca))
    else:
        usuario = buscar_por_email(busca)
    
    if not usuario:
        print("❌ Usuário não encontrado\n")
        return
    
    # Escolher plano
    print("\nPlanos disponíveis:")
    print("1. STARTER (R$ 19,90/mês)")
    print("2. PRO (R$ 39,90/mês)")
    print("3. TEAM (R$ 99,90/mês)")
    print("4. FREE (cancelar plano)")
    
    opcao = input("\nEscolha o plano (1-4): ").strip()
    
    planos = {"1": "STARTER", "2": "PRO", "3": "TEAM", "4": "FREE"}
    plano = planos.get(opcao)
    
    if not plano:
        print("❌ Opção inválida\n")
        return
    
    # Escolher duração
    if plano != "FREE":
        print("\nDuração:")
        print("1. 30 dias (mensal)")
        print("2. 365 dias (anual)")
        
        duracao = input("\nEscolha (1-2): ").strip()
        dias = 30 if duracao == "1" else 365
    else:
        dias = 0
    
    # Confirmar
    print(f"\n⚠️  CONFIRMAR:")
    print(f"   Cliente: {usuario['email']}")
    print(f"   Plano: {plano}")
    print(f"   Dias: {dias if dias > 0 else 'N/A'}")
    
    confirma = input("\nConfirmar? (s/n): ").strip().lower()
    
    if confirma == 's':
        atualizar_plano(usuario['id'], plano, dias)
        print("\n🎉 Cliente ativado com sucesso!")
        print("   Ele já pode usar o sistema!\n")
    else:
        print("\n❌ Operação cancelada\n")

# =======================
# TESTE
# =======================

if __name__ == "__main__":
    # Criar tabelas
    criar_tabela_usuarios()
    
    print("\n🔧 MODO DE TESTE\n")
    print("Comandos disponíveis:")
    print("1. from auth import cadastrar_usuario")
    print("2. from auth import fazer_login")
    print("3. from auth import listar_usuarios")
    print("4. from auth import ativar_cliente_interativo")
    print("\nExemplo:")
    print(">>> from auth import ativar_cliente_interativo")
    print(">>> ativar_cliente_interativo()")
