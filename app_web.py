import sqlite3
import datetime
from flask import Flask

# --- LÓGICA DO BANCO DE DADOS (Copiada do nosso projeto anterior) ---
# Mantemos esta parte separada da lógica web para organização.

NOME_BANCO_DADOS = 'controle_financeiro.db'

def conectar_bd():
    """Conecta ao banco de dados SQLite e retorna a conexão e o cursor."""
    conn = sqlite3.connect(NOME_BANCO_DADOS)
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor()

def inicializar_banco_de_dados():
    """Cria a tabela de transações no banco de dados, se ela não existir."""
    conn, cursor = conectar_bd()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes_tb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT,
            data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def buscar_transacoes_db(ano=None, mes=None):
    """Busca transações, opcionalmente filtrando por ano e mês."""
    conn, cursor = conectar_bd()
    try:
        query = "SELECT id, tipo, descricao, valor, categoria, data_registro FROM transacoes_tb"
        params = []
        conditions = []
        if ano:
            conditions.append("strftime('%Y', data_registro) = ?")
            params.append(str(ano))
        if mes:
            mes_formatado = f"{int(mes):02d}"
            conditions.append("strftime('%m', data_registro) = ?")
            params.append(mes_formatado)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY data_registro DESC, id DESC"
        cursor.execute(query, params)
        linhas_db = cursor.fetchall()
        return [dict(linha) for linha in linhas_db]
    except sqlite3.Error as e:
        print(f"Erro de banco de dados ao buscar transações: {e}")
        raise e # Propaga o erro
    finally:
        conn.close()


# --- APLICAÇÃO WEB COM FLASK ---

app = Flask(__name__)

@app.route('/')
def pagina_inicial():
    """Busca as transações no banco e as exibe na página."""
    try:
        # 1. Chama nossa função de backend para buscar os dados
        transacoes = buscar_transacoes_db()

        if not transacoes:
            return "<h1>Controle Financeiro</h1><p>Nenhuma transação encontrada no banco de dados.</p>"

        # 2. Constrói uma string HTML para exibir os dados
        # Usamos <br> para quebrar a linha no navegador
        html_output = "<h1>Controle Financeiro - Todas as Transações</h1>"
        for t in transacoes:
            data_obj = datetime.datetime.fromisoformat(t['data_registro'])
            data_formatada = data_obj.strftime('%d/%m/%Y')
            
            linha = (f"ID: {t['id']} | "
                     f"Data: {data_formatada} | "
                     f"Tipo: {t['tipo']} | "
                     f"Descrição: {t['descricao']} | "
                     f"Valor: R$ {t['valor']:.2f} | "
                     f"Categoria: {t['categoria'] or '-'}<br>") # 'or' para lidar com categoria None
            
            html_output += linha
        
        # 3. Retorna a string HTML completa para o navegador
        return html_output

    except Exception as e:
        # Se ocorrer um erro no banco de dados, exibimos uma mensagem de erro na página
        return f"<h1>Ocorreu um Erro</h1><p>Não foi possível buscar as transações: {e}</p>"


if __name__ == '__main__':
    # Garante que a tabela no banco de dados exista antes de rodar a aplicação
    inicializar_banco_de_dados()
    app.run(debug=True)