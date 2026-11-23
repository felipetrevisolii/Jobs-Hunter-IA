import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_NAME = BASE_DIR / "vagas_enviadas.db"


def criar_tabela():
    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas_enviadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT UNIQUE NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


def vaga_ja_enviada(link):
    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()

    cursor.execute(
        "SELECT id FROM vagas_enviadas WHERE link = ?",
        (link,)
    )

    resultado = cursor.fetchone()

    conexao.close()

    return resultado is not None


def salvar_vaga(vaga):
    link = vaga.get("link")

    if not link:
        return

    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "INSERT INTO vagas_enviadas (link) VALUES (?)",
            (link,)
        )
        conexao.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conexao.close()

def status_entrega(link):
    """Salva progresso por canal para não reenviar desnecessariamente."""
    conexao = sqlite3.connect(DB_NAME)
    try:
        conexao.execute('''CREATE TABLE IF NOT EXISTS entregas_ti (
            link TEXT PRIMARY KEY, sheets_ok INTEGER DEFAULT 0,
            telegram_ok INTEGER DEFAULT 0)''')
        cursor = conexao.execute('SELECT sheets_ok, telegram_ok FROM entregas_ti WHERE link = ?', (link,))
        linha = cursor.fetchone()
        return {'sheets_ok': bool(linha[0]), 'telegram_ok': bool(linha[1])} if linha else {'sheets_ok':False, 'telegram_ok':False}
    finally:
        conexao.close()


def registrar_canal(link, canal):
    if canal not in ('sheets_ok','telegram_ok'):
        raise ValueError('Canal inválido')
    conexao = sqlite3.connect(DB_NAME)
    try:
        conexao.execute('''CREATE TABLE IF NOT EXISTS entregas_ti (
            link TEXT PRIMARY KEY, sheets_ok INTEGER DEFAULT 0,
            telegram_ok INTEGER DEFAULT 0)''')
        conexao.execute('INSERT OR IGNORE INTO entregas_ti (link) VALUES (?)', (link,))
        conexao.execute(f'UPDATE entregas_ti SET {canal}=1 WHERE link=?', (link,))
        conexao.commit()
    finally:
        conexao.close()
