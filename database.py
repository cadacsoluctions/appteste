import sqlite3

conn = sqlite3.connect("loja.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT,
categoria TEXT,
preco REAL,
custo REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT,
cpf TEXT,
telefone TEXT,
email TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
id INTEGER PRIMARY KEY AUTOINCREMENT,
produto TEXT,
quantidade INTEGER,
valor REAL,
data TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS despesas (
id INTEGER PRIMARY KEY AUTOINCREMENT,
descricao TEXT,
valor REAL,
data TEXT,
pago TEXT
)
""")

conn.commit()
conn.close()