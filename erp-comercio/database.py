import sqlite3
import os
from datetime import datetime

# ---------------------------------------------------------
# BANCO DE DADOS — database.py
# ---------------------------------------------------------
# O sqlite3 é um banco de dados que fica salvo num arquivo
# no próprio computador — sem precisar instalar nada.
# Ideal para sistemas desktop como esse ERP.
# ---------------------------------------------------------

CAMINHO_DB = 'erp.db'  # arquivo do banco de dados


def conectar():
    """
    Abre a conexão com o banco de dados.
    Cria o arquivo erp.db se não existir.

    Retorna:
        conn: conexão com o banco
    """
    conn = sqlite3.connect(CAMINHO_DB)
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome
    return conn


def criar_tabelas():
    """
    Cria todas as tabelas do sistema se ainda não existirem.
    Roda uma vez quando o sistema inicia.
    """
    conn = conectar()
    cursor = conn.cursor()

    # ---------------------------------------------------------
    # TABELA: clientes
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            cpf_cnpj    TEXT,
            telefone    TEXT,
            email       TEXT,
            endereco    TEXT,
            cidade      TEXT,
            ativo       INTEGER DEFAULT 1,
            criado_em   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ---------------------------------------------------------
    # TABELA: fornecedores
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fornecedores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT NOT NULL,
            cnpj        TEXT,
            telefone    TEXT,
            email       TEXT,
            endereco    TEXT,
            contato     TEXT,
            ativo       INTEGER DEFAULT 1,
            criado_em   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ---------------------------------------------------------
    # TABELA: produtos (estoque)
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo          TEXT UNIQUE,
            nome            TEXT NOT NULL,
            categoria       TEXT,
            unidade         TEXT DEFAULT 'UN',
            preco_custo     REAL DEFAULT 0,
            preco_venda     REAL DEFAULT 0,
            estoque_atual   REAL DEFAULT 0,
            estoque_minimo  REAL DEFAULT 0,
            fornecedor_id   INTEGER,
            ativo           INTEGER DEFAULT 1,
            criado_em       TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
        )
    ''')

    # ---------------------------------------------------------
    # TABELA: vendas
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id      INTEGER,
            total           REAL NOT NULL,
            desconto        REAL DEFAULT 0,
            forma_pagamento TEXT DEFAULT 'dinheiro',
            status          TEXT DEFAULT 'concluida',
            observacao      TEXT,
            criado_em       TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')

    # ---------------------------------------------------------
    # TABELA: itens_venda (produtos de cada venda)
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_venda (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id    INTEGER NOT NULL,
            produto_id  INTEGER NOT NULL,
            quantidade  REAL NOT NULL,
            preco_unit  REAL NOT NULL,
            subtotal    REAL NOT NULL,
            FOREIGN KEY (venda_id)   REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')

    # ---------------------------------------------------------
    # TABELA: financeiro (contas a pagar e receber)
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financeiro (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo            TEXT NOT NULL,  -- 'receita' ou 'despesa'
            descricao       TEXT NOT NULL,
            valor           REAL NOT NULL,
            vencimento      TEXT NOT NULL,
            pago            INTEGER DEFAULT 0,
            data_pagamento  TEXT,
            categoria       TEXT,
            venda_id        INTEGER,
            criado_em       TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venda_id) REFERENCES vendas(id)
        )
    ''')

    # ---------------------------------------------------------
    # TABELA: movimentacoes_estoque
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id  INTEGER NOT NULL,
            tipo        TEXT NOT NULL,  -- 'entrada' ou 'saida'
            quantidade  REAL NOT NULL,
            motivo      TEXT,
            criado_em   TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso.")


# ---------------------------------------------------------
# FUNÇÕES GENÉRICAS DE CRUD
# ---------------------------------------------------------
# CRUD = Create, Read, Update, Delete
# São as 4 operações básicas de qualquer banco de dados

def executar(sql, params=()):
    """
    Executa um comando SQL (INSERT, UPDATE, DELETE).
    Retorna o ID do registro inserido.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    ultimo_id = cursor.lastrowid
    conn.close()
    return ultimo_id


def buscar_um(sql, params=()):
    """
    Busca um único registro no banco.
    Retorna um dicionário com os dados ou None.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_todos(sql, params=()):
    """
    Busca vários registros no banco.
    Retorna uma lista de dicionários.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------
# FUNÇÕES DE ESTOQUE
# ---------------------------------------------------------

def atualizar_estoque(produto_id, quantidade, tipo, motivo=''):
    """
    Atualiza o estoque de um produto e registra a movimentação.

    Parâmetros:
        produto_id : ID do produto
        quantidade : quantidade a movimentar
        tipo       : 'entrada' ou 'saida'
        motivo     : descrição da movimentação
    """
    if tipo == 'entrada':
        executar(
            'UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?',
            (quantidade, produto_id)
        )
    elif tipo == 'saida':
        executar(
            'UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE id = ?',
            (quantidade, produto_id)
        )

    # Registra a movimentação
    executar(
        'INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade, motivo) VALUES (?, ?, ?, ?)',
        (produto_id, tipo, quantidade, motivo)
    )


def produtos_estoque_baixo():
    """
    Retorna produtos com estoque abaixo do mínimo.
    """
    return buscar_todos('''
        SELECT nome, estoque_atual, estoque_minimo
        FROM produtos
        WHERE estoque_atual <= estoque_minimo AND ativo = 1
        ORDER BY nome
    ''')


# ---------------------------------------------------------
# FUNÇÕES DE RELATÓRIO
# ---------------------------------------------------------

def resumo_financeiro(mes=None, ano=None):
    """
    Retorna resumo financeiro do período.
    """
    if not mes:
        mes = datetime.now().month
    if not ano:
        ano = datetime.now().year

    periodo = f'{ano}-{mes:02d}'

    receitas = buscar_um(
        "SELECT COALESCE(SUM(valor), 0) as total FROM financeiro WHERE tipo='receita' AND strftime('%Y-%m', vencimento) = ? AND pago = 1",
        (periodo,)
    )
    despesas = buscar_um(
        "SELECT COALESCE(SUM(valor), 0) as total FROM financeiro WHERE tipo='despesa' AND strftime('%Y-%m', vencimento) = ? AND pago = 1",
        (periodo,)
    )

    total_receitas = receitas['total'] if receitas else 0
    total_despesas = despesas['total'] if despesas else 0

    return {
        'receitas': total_receitas,
        'despesas': total_despesas,
        'saldo':    total_receitas - total_despesas
    }


# ---------------------------------------------------------
# INICIALIZAÇÃO
# ---------------------------------------------------------
if __name__ == '__main__':
    criar_tabelas()
    print("Banco de dados criado em:", CAMINHO_DB)
    print("\nTabelas criadas:")
    tabelas = buscar_todos("SELECT name FROM sqlite_master WHERE type='table'")
    for t in tabelas:
        print(f"  → {t['name']}")
        