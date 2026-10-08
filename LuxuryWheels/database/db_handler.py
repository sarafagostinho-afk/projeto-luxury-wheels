# Módulo: db_handler.py
# Descrição: Gestor central da base de dados SQLite do Luxury Wheels.
           # Responsável pela criação automática de diretórios, tabelas relacionais e inserção de dados iniciais (utilizadores, formas de pagamento, etc.).

import sqlite3
import os
import hashlib

# Caminho absoluto para a base de dados na pasta 'database'
PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DB = os.path.join(PROJ_ROOT, "database")
DB_PATH = os.path.join(PASTA_DB, "luxury_wheels.db")


def get_connection():
    # Cria e retorna uma ligação ativa à base de dados SQLite. Usa sqlite3.Row para permitir aceder aos campos das tabelas como dicionários.
    os.makedirs(PASTA_DB, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_base_dados():
    # Executa a criação de todas as tabelas do sistema se estas ainda não existirem, e insere dados iniciais essenciais para o correto funcionamento da aplicação.
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabela de Utilizadores / Autenticação
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome_completo TEXT,
            nivel_acesso TEXT DEFAULT 'Administrador',
            ativo INTEGER DEFAULT 1
        )
    """)

    # 2. Tabela de Veículos da Frota
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE NOT NULL,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER,
            tipo TEXT,
            categoria TEXT,
            transmissao TEXT,
            num_passageiros INTEGER,
            combustivel TEXT,
            cor TEXT,
            preco_diario REAL,
            quilometragem INTEGER DEFAULT 0,
            data_proxima_revisao TEXT,
            data_proxima_inspecao TEXT,
            estado TEXT DEFAULT 'Disponível',
            motivo_indisponivel TEXT,
            imagem_path TEXT,
            extras TEXT
        )
    """)

    # 3. Tabela de Clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            nif TEXT UNIQUE NOT NULL,
            numero_carta TEXT,
            telefone TEXT,
            email TEXT,
            morada TEXT
        )
    """)

    # 4. Tabela de Formas de Pagamento
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS formas_pagamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            ativo INTEGER DEFAULT 1
        )
    """)

    # 5. Tabela de Reservas / Alugueres
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            forma_pagamento_id INTEGER NOT NULL,
            data_inicio TEXT NOT NULL,
            data_fim_prevista TEXT NOT NULL,
            data_fim_real TEXT,
            km_inicial INTEGER DEFAULT 0,
            km_final INTEGER DEFAULT 0,
            valor_diario_aplicado REAL NOT NULL,
            valor_total REAL NOT NULL,
            estado_reserva TEXT DEFAULT 'Ativa',
            observacoes TEXT,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos (id),
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            FOREIGN KEY (forma_pagamento_id) REFERENCES formas_pagamento (id)
        )
    """)

    conn.commit()

    # --- SEMENTEIRA DE DADOS INICIAIS (SEED) ---

    # Criar Administrador por defeito se não existir
    cursor.execute("SELECT COUNT(*) FROM utilizadores")
    if cursor.fetchone()[0] == 0:
        pwd_admin = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        cursor.execute("""
            INSERT INTO utilizadores (username, password_hash, nome_completo, nivel_acesso, ativo)
            VALUES ('admin', ?, 'Administrador Principal', 'Administrador', 1)
        """, (pwd_admin,))

    # Criar Formas de Pagamento padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM formas_pagamento")
    if cursor.fetchone()[0] == 0:
        metodos_iniciais = [
            ("Multibanco", "Pagamento por referência MB ou ATM"),
            ("Cartão de Crédito", "Visa, Mastercard ou American Express"),
            ("Transferência Bancária", "Transferência direta interbancária SEBA"),
            ("Numerário", "Pagamento em dinheiro (sujeito a sinal de 20%)")
        ]
        cursor.executemany("""
            INSERT INTO formas_pagamento (nome, descricao, ativo)
            VALUES (?, ?, 1)
        """, metodos_iniciais)

    conn.commit()
    conn.close()


# Executar inicialização automática ao importar o módulo
if __name__ != "__main__":
    inicializar_base_dados()